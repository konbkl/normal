"""Pure text helpers for the Roohi style (no bot imports, safe to import anywhere)."""
import html
import re

# ------------------------------------------------------------------ font
_MAP = {
    "a": "ᴧ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "є", "f": "ғ", "g": "ɢ",
    "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "η",
    "o": "σ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ",
    "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ",
}
_TABLE = str.maketrans({**_MAP, **{k.upper(): v for k, v in _MAP.items()}})

# parts of a string that must never be converted
_KEEP = re.compile(
    r"(<code>.*?</code>|<pre>.*?</pre>|<[^>]+>|&[#\w]+;|\{[^{}]*\}"
    r"|(?:https?|tg)://\S+|(?<![\w/])/[A-Za-z0-9_]+(?:@\w+)?|@\w+)",
    re.S,
)


def fancy(text) -> str:
    if text is None:
        return ""
    text = str(text)
    out, last = [], 0
    for m in _KEEP.finditer(text):
        out.append(text[last:m.start()].translate(_TABLE))
        out.append(m.group(0))
        last = m.end()
    out.append(text[last:].translate(_TABLE))
    return "".join(out)


def quote(text, expandable=False) -> str:
    tag = "<blockquote expandable>" if expandable else "<blockquote>"
    return f"{tag}{text}</blockquote>"


def _to_sec(t):
    try:
        return sum(int(x) * 60 ** i for i, x in enumerate(reversed(str(t).split(":"))))
    except Exception:
        return 0


def _fmt(sec):
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def nice_duration(dur):
    """'06:30' -> '6m 30s' (Roohi style)."""
    sec = _to_sec(dur)
    if not sec:
        return str(dur or "ʟɪᴠє")
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s" if m else f"{s}s"


def stream_type_label(video=None):
    """True -> '🎬 ᴠɪᴅєσ', anything else -> '🎵 ᴧᴜᴅɪσ'."""
    return f"🎬 {fancy('Video')}" if video else f"🎵 {fancy('Audio')}"


def player_caption(link, title, dur, user=None, video=None):
    title = html.escape(str(title or "Unknown")[:40])
    head = quote(f"<b>{fancy('Playback activated.')} | {fancy('Enjoy the music')} |</b>")
    body = (
        f"▫️ <b>{fancy('Melody')} :</b> <a href=\"{link}\">{title}</a>\n"
        f"▫️ <b>{fancy('Length')} :</b> {nice_duration(dur)}\n"
        f"▫️ <b>{fancy('Stream Type')} :</b> {stream_type_label(video)}"
    )
    if user:
        body += f"\n▫️ <b>{fancy('Requested by')} :</b> {user}"
    return head + "\n" + quote(body, expandable=True)


def start_caption(user, bot):
    """Roohi start message: 'Salutations user,' + expandable welcome."""
    head = quote(f"<b>{fancy('Salutations')} {user},</b>")
    body = "\n".join([
        f"✧ <b>{fancy('Welcome to')} {bot} — {fancy('a powerful and high-speed tg music bot')}</b>",
        f"✧ <b>{fancy('Built for smooth • stable • lag-free music streaming')}</b>",
        f"✧ <b>{fancy('Powered by an optimized youtube api for instant playback')}</b>",
        f"✧ <b>{fancy('Enjoy high quality audio with seamless control')}</b>",
        "•───────────────────•",
        f"✧ <b>{fancy('Use help to view all commands and features')}</b>",
    ])
    return head + "\n" + quote(body, expandable=True)
