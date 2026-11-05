"""Roohi-style help menu texts.

Each section = (button label, title, body). Bodies go inside an expandable
blockquote and stay well under Telegram's 1024 caption limit.
"""
from roohifont import fancy


def _sec(title, body):
    return (
        f"⦿ <b><u>{fancy(title)} :</u></b>\n\n"
        f"<blockquote expandable>{body}</blockquote>"
    )


def _cmd(cmd, desc):
    return f"➻ {cmd} : {fancy(desc)}"


HELP_HOME = (
    "<blockquote><b>🔮 {explore}</b></blockquote>\n\n"
    "<blockquote><b>• {guide}</b> <a href=\"{{0}}\">{support}</a></blockquote>\n"
    "<blockquote><b>• {prefix} ➜</b> <code>/</code></blockquote>"
).format(
    explore=fancy("Explore the complete command index below"),
    guide=fancy("Access expert technical guidance & real-time support"),
    support=fancy("here"),
    prefix=fancy("Execute all commands using standard prefix"),
)

# order = button order in the grid (playlist section removed on purpose)
SECTIONS = {
    "admin": ("Admin", _sec("Admin commands", "\n".join([
        fancy("Add c in front of a command to use it for channel play.") + "\n",
        _cmd("/pause", "pause the current stream."),
        _cmd("/resume", "resume the paused stream."),
        _cmd("/skip", "skip to the next track in queue."),
        _cmd("/stop", "stop the stream and clear the queue."),
        _cmd("/seek [sec]", "seek forward."),
        _cmd("/seekback [sec]", "seek backward."),
        _cmd("/loop [1-10 / disable]", "loop the current track."),
        _cmd("/shuffle", "shuffle the queue."),
        _cmd("/speed", "change playback speed."),
        "\n❏ " + fancy("Only group admins can use these commands."),
    ]))),
    "auth": ("Auth", _sec("Auth users", "\n".join([
        fancy("Auth users can use admin commands without admin rights.") + "\n",
        _cmd("/auth [user]", "add a user to auth list."),
        _cmd("/unauth [user]", "remove a user from auth list."),
        _cmd("/authusers", "show the auth list of this chat."),
    ]))),
    "bcast": ("B-Cast", _sec("Broadcast", "\n".join([
        _cmd("/broadcast [msg / reply]", "send a message to all served chats.") + "\n",
        "<b>" + fancy("Modes") + " :</b>",
        "• <code>-pin</code> : " + fancy("pin the message"),
        "• <code>-pinloud</code> : " + fancy("pin with notification"),
        "• <code>-user</code> : " + fancy("also send to bot users"),
        "• <code>-assistant</code> : " + fancy("send from assistant"),
        "• <code>-nobot</code> : " + fancy("don't send from bot"),
        "\n❏ " + fancy("Only for bot owner & sudoers."),
    ]))),
    "play": ("Play", _sec("Play commands", "\n".join([
        _cmd("/play [song / link]", "play audio in voice chat."),
        _cmd("/vplay [song / link]", "play video in voice chat."),
        _cmd("/playforce", "stop current & play instantly."),
        _cmd("/vplayforce", "force play a video."),
        _cmd("/cplay , /cvplay", "play in linked channel."),
        _cmd("/channelplay [id / linked / disable]", "connect a channel."),
        _cmd("/playmode", "change play mode of the chat."),
        "\n❏ " + fancy("Supports youtube, spotify, soundcloud, apple music & telegram files."),
    ]))),
    "sudo": ("Sudo", _sec("Sudo users", "\n".join([
        _cmd("/addsudo [user]", "add a sudo user."),
        _cmd("/delsudo [user]", "remove a sudo user."),
        _cmd("/sudolist", "show all sudo users."),
        _cmd("/delallsudo", "remove every sudo user."),
        _cmd("/stats", "bot statistics."),
        _cmd("/reboot", "restart the bot."),
        "\n❏ " + fancy("Only the bot owner can manage sudoers."),
    ]))),
    "restrict": ("Restrict", _sec("Restrict", "\n".join([
        _cmd("/blacklistchat [id]", "blacklist a chat."),
        _cmd("/whitelistchat [id]", "remove a chat from blacklist."),
        _cmd("/blacklistedchats", "show blacklisted chats."),
        _cmd("/gban [user]", "globally ban a user."),
        _cmd("/ungban [user]", "remove global ban."),
        _cmd("/gbannedusers", "show gbanned users."),
        "\n❏ " + fancy("Only for owner & sudoers."),
    ]))),
    "thumb": ("Thumbnail", _sec("Thumbnail settings", "\n".join([
        _cmd("/nothumb", "manage stream visual settings.") + "\n",
        "🎨 <b>" + fancy("Toggle album art display. Disabling it reduces data load and keeps a minimalist chat look.") + "</b>\n",
        "<b>" + fancy("Options") + " :</b>",
        "• <b>" + fancy("Enable") + "</b> : " + fancy("display artwork with stream info."),
        "• <b>" + fancy("Disable") + "</b> : " + fancy("send pure text-based updates."),
        "• <b>" + fancy("Close") + "</b> : " + fancy("dismiss the configuration."),
        "\n❏ " + fancy("Settings are saved individually per chat."),
    ]))),
    "start": ("Start", _sec("Start & info", "\n".join([
        _cmd("/start", "start the bot."),
        _cmd("/help", "open this help menu."),
        _cmd("/ping", "check bot ping & system stats."),
        _cmd("/stats", "show bot stats."),
        _cmd("/id", "get user / chat id."),
        _cmd("/lang", "change bot language."),
        _cmd("/settings", "group settings panel."),
    ]))),
    "autoplay": ("Autoplay", _sec("Autoplay system", "\n".join([
        _cmd("/autoplay enable", "play related tracks when queue ends."),
        _cmd("/autoplay disable", "stop when the queue is finished."),
        "\n• " + fancy("You can also toggle it from the player button."),
        "❏ " + fancy("Only group admins can manage autoplay."),
    ]))),
    "vclogs": ("VC-Logs", _sec("Voice chat logs", "\n".join([
        _cmd("/vclogger on", "log who joins / leaves the voice chat."),
        _cmd("/vclogger off", "turn voice chat logs off."),
        _cmd("/vclogger", "check current status."),
        "\n❏ " + fancy("Log messages auto delete after a few seconds."),
    ]))),
    "inline": ("Inline", _sec("Bot play button details", "\n".join([
        "🎛 <b>" + fancy("Manage your music playback directly through inline buttons with ease.") + "</b>\n",
        "<b>" + fancy("Playback controls") + " :</b>",
        "➻ ▷ : " + fancy("resume the paused stream."),
        "➻ II : " + fancy("pause the ongoing stream."),
        "➻ ↻ : " + fancy("replay the current song from start."),
        "➻ ‣‣I : " + fancy("skip the current track and play next."),
        "➻ ▢ : " + fancy("stop the playback and clear queue."),
        "\n<b>" + fancy("Seek and navigation") + " :</b>",
        "➻ -15ˢ : " + fancy("seek backward by 15 seconds."),
        "➻ 15ˢ+ : " + fancy("seek forward by 15 seconds."),
        "\n❏ " + fancy("All buttons only for group admins."),
    ]))),
}
