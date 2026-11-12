import asyncio
import base64
import os
import shutil
import time
import zipfile

from github import Auth, Github, GithubException, InputGitAuthor, InputGitTreeElement
from pyrogram import filters

from config import OWNER_ID
from RoohiClone import app

# This plugin talks to the GitHub API directly (Git Data API), so it does NOT need
# the `git` program to be installed on the server (Heroku dynos don't have it).

TEMP_DIR = "temp_repos"
os.makedirs(TEMP_DIR, exist_ok=True)

TEMP_CONFIG = {}

SKIP_DIRS = {".git", "__MACOSX"}
SKIP_FILES = {".DS_Store"}
EXECUTABLE_NAMES = {"start", "setup"}
CHUNK_MAX_FILES = 80
CHUNK_MAX_BYTES = 2 * 1024 * 1024


def safe_rm(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def config_valid():
    if not TEMP_CONFIG:
        return False
    if time.time() - TEMP_CONFIG.get("timestamp", 0) > 300:
        TEMP_CONFIG.clear()
        return False
    return True


def _collect_files(root):
    files = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if name in SKIP_FILES:
                continue
            full = os.path.join(folder, name)
            if os.path.islink(full):
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            files.append((rel, full))
    return files


def _head_commit(repo, branch, retries=1):
    """GitCommit at the tip of `branch`, or None if the branch does not exist."""
    for attempt in range(retries):
        try:
            sha = repo.get_branch(branch).commit.sha
            return repo.get_git_commit(sha)
        except GithubException as e:
            if e.status not in (404, 409):
                raise
            if attempt < retries - 1:
                time.sleep(1.5)
    return None


def _tree_element(repo, rel, full):
    with open(full, "rb") as f:
        data = f.read()
    mode = "100755" if (rel.endswith(".sh") or os.path.basename(rel) in EXECUTABLE_NAMES) else "100644"
    if not data:
        blob = repo.create_git_blob("", "utf-8")
        return InputGitTreeElement(rel, mode, "blob", sha=blob.sha), 0
    try:
        text = data.decode("utf-8")
        if "\x00" in text:
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "binary")
        return InputGitTreeElement(rel, mode, "blob", content=text), len(data)
    except UnicodeDecodeError:
        blob = repo.create_git_blob(base64.b64encode(data).decode("ascii"), "base64")
        return InputGitTreeElement(rel, mode, "blob", sha=blob.sha), 0


def upload_to_github(token, name, email, repo_name, is_private, branch, root):
    """Blocking. Uploads every file under `root` as one commit. Returns (repo, created)."""
    g = Github(auth=Auth.Token(token))
    user = g.get_user()
    author = InputGitAuthor(name, email)

    created = False
    try:
        repo = user.get_repo(repo_name)
    except GithubException as e:
        if e.status != 404:
            raise
        repo = user.create_repo(
            repo_name,
            description="Source code uploaded by bot",
            private=is_private,
            auto_init=True,  # creates the first commit so the Git Data API works
        )
        created = True

    default_branch = repo.default_branch
    branch_head = _head_commit(repo, branch, retries=6 if created else 1)
    base_commit = branch_head or _head_commit(repo, default_branch, retries=6 if created else 1)
    if base_commit is None:  # existing empty repo: make a first commit
        repo.create_file("README.md", "init", "# init", branch=default_branch)
        base_commit = _head_commit(repo, default_branch, retries=6)
        if branch == default_branch:
            branch_head = base_commit

    files = _collect_files(root)
    if not files:
        raise RuntimeError("Zip is empty, nothing to upload.")

    tree = None
    chunk, chunk_bytes = [], 0

    def flush():
        nonlocal tree, chunk, chunk_bytes
        if not chunk:
            return
        tree = repo.create_git_tree(chunk, tree) if tree else repo.create_git_tree(chunk)
        chunk, chunk_bytes = [], 0

    for rel, full in files:
        element, size = _tree_element(repo, rel, full)
        chunk.append(element)
        chunk_bytes += size
        if len(chunk) >= CHUNK_MAX_FILES or chunk_bytes >= CHUNK_MAX_BYTES:
            flush()
    flush()

    # brand new repo: single clean root commit; existing repo: commit on top of the branch
    parents = [] if created else [base_commit]
    commit = repo.create_git_commit("Upload via bot", tree, parents, author=author, committer=author)

    if branch_head is not None:
        repo.get_git_ref(f"heads/{branch}").edit(commit.sha, force=created)
    else:
        repo.create_git_ref(f"refs/heads/{branch}", commit.sha)
        if created:
            repo.edit(default_branch=branch)
            try:
                repo.get_git_ref(f"heads/{default_branch}").delete()
            except GithubException:
                pass
    return repo, len(files)


@app.on_message(filters.command("gitconfig") & filters.user(OWNER_ID))
async def gitconfig(client, message):
    if len(message.command) < 4:
        return await message.reply(
            "**» ᴜsᴀɢᴇ :-** `/gitconfig username email token`"
        )
    name = message.command[1]
    email = message.command[2]
    token = message.command[3]
    TEMP_CONFIG.update({"name": name, "email": email, "token": token, "timestamp": time.time()})
    try:  # do not leave the token sitting in the chat
        await message.delete()
    except Exception:
        pass
    await message.reply("✅ **ɢɪᴛʜᴜʙ ᴄᴏɴꜰɪɢ sᴇᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!** (ᴠᴀʟɪᴅ ꜰᴏʀ **5 ᴍɪɴᴜᴛᴇs**)")


@app.on_message(filters.command(["gitupload", "gt"]) & filters.user(OWNER_ID))
async def gitupload(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "**» ᴜsᴀɢᴇ :-** `/gitupload repo_name private/public branch_name` **(ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴢɪᴘ ғɪʟᴇ)**"
        )

    if not config_valid():
        return await message.reply(
            "**⚠️ ᴄᴏɴꜰɪɢ ᴇxᴘɪʀᴇᴅ ᴏʀ ɴᴏᴛ sᴇᴛ!**\n\n**» ᴘʟᴇᴀsᴇ ʀᴜɴ** `/gitconfig` **ғɪʀsᴛ.**"
        )

    repo_name = message.command[1]
    visibility = message.command[2].lower() if len(message.command) >= 3 else "public"
    is_private = visibility == "private"
    branch_name = message.command[3] if len(message.command) >= 4 else "main"

    replied = message.reply_to_message
    if not (
        replied
        and replied.document
        and (replied.document.file_name or "").lower().endswith(".zip")
    ):
        return await message.reply("⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ **ᴢɪᴘ** ғɪʟᴇ!")

    zip_path = os.path.join(TEMP_DIR, replied.document.file_name)
    extract_root = os.path.join(TEMP_DIR, f"{repo_name}_extract")
    final_path = os.path.join(TEMP_DIR, f"{repo_name}_final")

    for p in (zip_path, extract_root, final_path):
        safe_rm(p)

    status = await message.reply("**⏳ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ...**")

    try:
        await replied.download(file_name=zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_root)

        inner = [i for i in os.listdir(extract_root) if i not in SKIP_DIRS | SKIP_FILES]
        inner_dirs = [d for d in inner if os.path.isdir(os.path.join(extract_root, d))]
        inner_files = [f for f in inner if os.path.isfile(os.path.join(extract_root, f))]
        if len(inner_dirs) == 1 and not inner_files:
            shutil.move(os.path.join(extract_root, inner_dirs[0]), final_path)
        else:
            shutil.move(extract_root, final_path)

        repo, count = await asyncio.to_thread(
            upload_to_github,
            TEMP_CONFIG["token"],
            TEMP_CONFIG["name"],
            TEMP_CONFIG["email"],
            repo_name,
            is_private,
            branch_name,
            final_path,
        )
    except GithubException as e:
        detail = e.data.get("message") if isinstance(e.data, dict) else e.data
        hint = ""
        if e.status == 401:
            hint = "\n**ᴛɪᴘ :-** ᴛᴏᴋᴇɴ ᴡʀᴏɴɢ/ᴇxᴘɪʀᴇᴅ ʜᴀɪ, ɴᴀʏᴀ ʙᴀɴᴀᴏ."
        elif e.status == 403:
            hint = "\n**ᴛɪᴘ :-** ᴛᴏᴋᴇɴ ᴍᴇ `repo` ᴘᴇʀᴍɪssɪᴏɴ ᴅᴏ."
        for p in (zip_path, extract_root, final_path):
            safe_rm(p)
        await status.delete()
        return await message.reply(f"❌** ᴇʀʀᴏʀ :-** `{e.status} {detail}`{hint}")
    except Exception as e:
        for p in (zip_path, extract_root, final_path):
            safe_rm(p)
        await status.delete()
        return await message.reply(f"❌** ᴇʀʀᴏʀ :-** `{e}`")

    for p in (zip_path, extract_root, final_path):
        safe_rm(p)
    await status.delete()
    await message.reply(
        f"✅ **ʀᴇᴘᴏ** `{repo_name}` **ᴜᴘʟᴏᴀᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**\n\n"
        f"🔒 **ᴠɪsɪʙɪʟɪᴛʏ :-** `{'Private' if repo.private else 'Public'}`\n"
        f"🌿 **ʙʀᴀɴᴄʜ :-** `{branch_name}`\n"
        f"📁 **ꜰɪʟᴇs :-** `{count}`\n\n"
        f"🔗 **ᴜʀʟ :-** {repo.html_url}"
    )
    
