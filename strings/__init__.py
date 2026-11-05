import os
from typing import List

import yaml

languages = {}
languages_present = {}


def get_string(lang: str):
    return languages[lang]


for filename in os.listdir(r"./strings/langs/"):
    if "en" not in languages:
        languages["en"] = yaml.safe_load(
            open(r"./strings/langs/en.yml", encoding="utf8")
        )
        languages_present["en"] = languages["en"]["name"]
    if filename.endswith(".yml"):
        language_name = filename[:-4]
        if language_name == "en":
            continue
        languages[language_name] = yaml.safe_load(
            open(r"./strings/langs/" + filename, encoding="utf8")
        )
        for item in languages["en"]:
            if item not in languages[language_name]:
                languages[language_name][item] = languages["en"][item]
    try:
        languages_present[language_name] = languages[language_name]["name"]
    except:
        print("There is some issue with the language file inside bot.")
        exit()


# =====================================================================
# ROOHI STYLE overrides (applied to every language)
# =====================================================================
class _PlayerCaption(str):
    """_["stream_1"].format(link, title, duration, user) -> Roohi player caption."""

    def format(self, link="", title="", dur="", user=None, *args, video=None, **kwargs):
        from roohifont import player_caption
        return player_caption(link, title, dur, user, video=video)


class _LiveCaption(str):
    """_["stream_2"].format(user, video=bool) -> live / index stream caption."""

    def format(self, user="", *args, video=None, **kwargs):
        from roohifont import fancy, quote, stream_type_label
        return quote(f"<b>🔴 {fancy('Live stream activated.')} | {fancy('Enjoy the music')} |</b>") + "\n" + quote(
            f"▫️ <b>{fancy('Stream Type')} :</b> {stream_type_label(video)}\n"
            f"▫️ <b>{fancy('Requested by')} :</b> {user}", True)


class _QueueCaption(str):
    """_["queue_4"].format(position, title, duration, user)."""

    def format(self, pos="", title="", dur="", user="", *args, **kwargs):
        import html
        from roohifont import fancy, nice_duration, quote
        return quote(f"<b>✚ {fancy('Added to queue at')} #{pos}</b>") + "\n" + quote(
            f"▫️ <b>{fancy('Melody')} :</b> {html.escape(str(title))}\n"
            f"▫️ <b>{fancy('Length')} :</b> {nice_duration(dur)}\n"
            f"▫️ <b>{fancy('Requested by')} :</b> {user}", True)


def _roohi_overrides():
    from roohifont import fancy, quote

    def q(t, exp=False):
        return quote(t, exp)

    o = {
        "stream_1": _PlayerCaption("stream_1"),
        "stream_2": _LiveCaption("stream_2"),
        "queue_4": _QueueCaption("queue_4"),
        "admin_2": q(f"<b>II {fancy('Stream paused')}</b>\n└ <b>{fancy('By')} :</b> {{0}}"),
        "admin_4": q(f"<b>▷ {fancy('Stream resumed')}</b>\n└ <b>{fancy('By')} :</b> {{0}}"),
        "admin_5": q(f"<b>▢ {fancy('Stream ended / stopped')}</b>\n└ <b>{fancy('By')} :</b> {{0}}"),
        "start_3": q(f"<b>🎵 {fancy('Thanks for adding me! Use')} /play [{fancy('song')}] {fancy('to start playing music.')}</b>"),
        "start_4": q(f"<b>{fancy('This chat is not a supergroup yet.')}</b>")
        + "\n" + q(f"<b>⚠️ {fancy('Please convert this group into a supergroup, then add me again as an admin.')}</b>\n\n"
                   f"<b>{fancy('How to convert?')}</b> {fancy('Make chat history visible for new members once.')}"),
        "CLOSE_BUTTON": "ᴄʟσsє",
        "CLOSEMENU_BUTTON": "ᴄʟσsє",
        "BACK_BUTTON": "⟵",
        "S_B_1": "✚ ᴧᴅᴅ ᴍє ✚",
        "S_B_2": "sᴜᴘᴘσʀᴛ",
        "S_B_3": "✧₊ ᴧᴅᴅ ᴍє ᴛσ ʏσᴜʀ ᴄʜᴧᴛ ₊✧",
        "S_B_4": "ʜєʟᴘ & ᴄσᴍᴍᴧηᴅs",
        "S_B_6": "ᴜᴘᴅᴧᴛєs",
        "S_B_9": "sᴜᴘᴘσʀᴛ",
        "help_2": q(f"<b>{fancy('Click the button below to get my help menu in your PM.')}</b>"),
        "start_2": __import__("roohifont").start_caption("{0}", "{1}"),
        "help_1": __import__("strings.roohihelp", fromlist=["HELP_HOME"]).HELP_HOME,
        "play_1": q(f"<b>🔎 {fancy('Searching your song...')}</b>"),
    }
    for lang in languages.values():
        lang.update(o)


try:
    _roohi_overrides()
except Exception as _e:  # never break the bot because of styling
    print(f"[ROOHI] string overrides skipped: {_e}")
