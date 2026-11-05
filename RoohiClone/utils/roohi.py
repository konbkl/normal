"""Roohi-style UI kit shared by the main bot and every clone.

    from RoohiClone.utils.roohi import fancy, btn, rows_to_kb, player_markup, quote

* fancy()          -> small-caps font (ᴧ є σ η ...) that keeps HTML, links,
                      {placeholders}, /commands and @mentions untouched
* btn()            -> InlineKeyboardButton with a random colour (blue/green/red)
* player_markup()  -> now-playing keyboard (progress bar, ▷ II ↻ ‣‣I ▢,
                      -15s / repo / 15s+, autoplay toggle, close)
* thumbnails on/off per chat (/nothumb)
"""

import random
import re

from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config

# ------------------------------------------------------------------ colours
STYLES = (ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER)


def rstyle():
    return random.choice(STYLES)


from roohifont import fancy, quote, nice_duration, player_caption, _to_sec, _fmt  # noqa: F401


# ------------------------------------------------------------------ buttons
def btn(text, cb=None, url=None, user_id=None, style=None, font=True, **extra):
    kw = {"text": fancy(text) if font else str(text), "style": style or rstyle()}
    if url:
        kw["url"] = url
    elif user_id:
        kw["user_id"] = int(user_id)
    else:
        kw["callback_data"] = cb or "roohi_none"
    # premium icons only when explicitly enabled (they fail for normal bots)
    icon = extra.pop("icon_custom_emoji_id", None)
    if icon and getattr(config, "BUTTON_ICONS", False):
        kw["icon_custom_emoji_id"] = str(icon)
    return InlineKeyboardButton(**kw)


def rows_to_kb(rows):
    return InlineKeyboardMarkup(rows)


def tg_link(val, fallback=None):
    """'@chat', 'chat', 't.me/chat' or full url -> https url."""
    if not val or str(val).strip().lower() in ("", "none"):
        return fallback or config.SUPPORT_CHAT
    val = str(val).strip()
    if " " in val:  # e.g. "No support chat set."
        return fallback or config.SUPPORT_CHAT
    if val.startswith(("https://", "http://", "tg://")):
        return val
    if val.startswith("t.me/"):
        return "https://" + val
    return f"https://t.me/{val.lstrip('@')}"


# ------------------------------------------------------------------ player
SEEK_STEP = 15


def progress_bar(played, dur, size=9):
    p, d = _to_sec(played), _to_sec(dur)
    pos = min(size, int(size * p / d)) if d else 0
    line = "—" * pos + "●" + "—" * (size - pos)
    return f"{_fmt(p)} {line} {_fmt(d) if d else dur}"


def _autoplay_state(chat_id):
    try:
        from RoohiClone.utils.database.database import autoplay
        return bool(autoplay.get(int(chat_id), False))
    except Exception:
        return False


def _now(chat_id):
    try:
        from RoohiClone.misc import db
        q = db.get(int(chat_id))
        if q:
            return q[0].get("played", 0), q[0].get("dur", "00:00")
    except Exception:
        pass
    return 0, "00:00"


CLONE_BOT_LINK = "https://t.me/SizzuMusicBot?start=clone"


def repo_url():
    return CLONE_BOT_LINK


# (chat_id, message_id) of player cards that currently show the "More" panel
MORE_OPEN = {}
_AUDIO_BUSY = set()


def player_markup(_=None, chat_id=0, played=None, dur=None, **__):
    """Main now-playing keyboard. Returns a list of rows."""
    if played is None or dur is None:
        p, d = _now(chat_id)
        played = p if played is None else played
        dur = d if dur is None else dur
    rows = []
    if _to_sec(dur):
        rows.append([btn(progress_bar(played, dur), cb="GetTimer", font=False)])
    rows.append([
        btn("▷", cb=f"ADMIN Resume|{chat_id}", font=False),
        btn("II", cb=f"ADMIN Pause|{chat_id}", font=False),
        btn("↻", cb=f"ADMIN Replay|{chat_id}", font=False),
        btn("‣‣I", cb=f"ADMIN Skip|{chat_id}", font=False),
        btn("▢", cb=f"ADMIN Stop|{chat_id}", font=False),
    ])
    rows.append([
        btn(f"-{SEEK_STEP}ˢ", cb=f"ADMIN SeekBack|{chat_id}", font=False),
        btn("More", cb=f"ADMIN More|{chat_id}"),
        btn(f"{SEEK_STEP}ˢ+", cb=f"ADMIN SeekForward|{chat_id}", font=False),
    ])
    rows.append([btn("Close", cb="close")])
    return rows


def _thumb_state_sync(chat_id):
    try:
        return bool(_thumb_cache.get(int(chat_id), True))
    except Exception:
        return True


def more_markup(_=None, chat_id=0, played=None, dur=None, **__):
    """'More' panel: mute / loop / equalizer / track mode / unmute + autoplay / thumbnail / back."""
    if played is None or dur is None:
        p, d = _now(chat_id)
        played = p if played is None else played
        dur = d if dur is None else dur
    rows = []
    if _to_sec(dur):
        rows.append([btn(progress_bar(played, dur), cb="GetTimer", font=False)])
    rows.append([
        btn("🔇", cb=f"ADMIN Mute|{chat_id}", font=False),
        btn("🔄", cb=f"ADMIN Loop|{chat_id}", font=False),
        btn("🎚", cb=f"ADMIN EqPanel|{chat_id}", font=False),
        btn("📡", cb=f"ADMIN TrackMode|{chat_id}", font=False),
        btn("🔊", cb=f"ADMIN Unmute|{chat_id}", font=False),
    ])
    ap = "On" if _autoplay_state(chat_id) else "Off"
    th = "On" if _thumb_state_sync(chat_id) else "Off"
    rows.append([
        btn(f"♫ Autoplay: {ap}", cb=f"ADMIN Autoplay|{chat_id}"),
        btn(f"🖼 Thumbnail: {th}", cb=f"ADMIN Thumb|{chat_id}"),
    ])
    rows.append([btn("Clone", url=repo_url()), btn("Back ⟲", cb=f"ADMIN Back|{chat_id}")])
    return rows


def current_markup(_, chat_id, message=None):
    """Keyboard that matches what the card is showing right now (main or More)."""
    if message is not None and (message.chat.id, message.id) in MORE_OPEN:
        return more_markup(_, chat_id)
    return player_markup(_, chat_id)


# ------------------------------------------------------------------ seek / replay
async def seek_player(chat_id, delta=None, to=None):
    """Seek the running stream. Returns (ok, text)."""
    from RoohiClone import YouTube
    from RoohiClone.core.call import ROOHI
    from RoohiClone.misc import db

    playing = db.get(chat_id)
    if not playing:
        return False, fancy("Nothing is playing.")
    total = int(playing[0].get("seconds", 0) or 0)
    played = int(playing[0].get("played", 0) or 0)
    if total == 0:
        return False, fancy("Can't seek a live stream.")
    target = to if to is not None else played + delta
    target = max(0, min(target, total - 3))
    file_path = playing[0].get("file", "")
    if playing[0].get("speed_path"):
        file_path = playing[0]["speed_path"]
    elif "vid_" in file_path:
        n, file_path = await YouTube.video(playing[0]["vidid"], True)
        if n == 0:
            return False, fancy("Seek failed, try again.")
    elif "index_" in file_path:
        file_path = playing[0]["vidid"]
    try:
        await ROOHI.seek_stream(chat_id, file_path, _fmt(target),
                                 playing[0].get("dur", "00:00"),
                                 playing[0].get("streamtype", "audio"))
    except Exception:
        return False, fancy("Seek failed, try again.")
    if db.get(chat_id):
        db[chat_id][0]["played"] = target
    return True, f"⏱ {_fmt(target)} / {playing[0].get('dur', '')}"


# ------------------------------------------------------------------ thumbnail on/off
_thumb_cache = {}


def _thumbdb():
    from RoohiClone.core.mongo import mongodb
    return mongodb.thumbmode


async def is_thumb_on(chat_id) -> bool:
    chat_id = int(chat_id)
    if chat_id not in _thumb_cache:
        try:
            doc = await _thumbdb().find_one({"chat_id": chat_id})
            _thumb_cache[chat_id] = not bool(doc and doc.get("off"))
        except Exception:
            _thumb_cache[chat_id] = True
    return _thumb_cache[chat_id]


async def set_thumb(chat_id, on: bool):
    chat_id = int(chat_id)
    _thumb_cache[chat_id] = on
    try:
        if on:
            await _thumbdb().delete_one({"chat_id": chat_id})
        else:
            await _thumbdb().update_one({"chat_id": chat_id}, {"$set": {"off": True}}, upsert=True)
    except Exception:
        pass


async def send_card(client, chat_id=None, photo=None, caption="", reply_markup=None, **kw):
    """Drop-in for client.send_photo() on now-playing cards.
    Respects /nothumb and falls back to a text message if the photo fails."""
    kw.pop("has_spoiler", None)
    if isinstance(photo, (list, tuple)):
        photo = random.choice(photo) if photo else None
    if photo and await is_thumb_on(chat_id):
        try:
            return await client.send_photo(chat_id, photo=photo, caption=caption,
                                           reply_markup=reply_markup, **kw)
        except Exception as e:
            print(f"[ROOHI] photo card failed, sending text: {e}")
    return await client.send_message(chat_id, caption, reply_markup=reply_markup,
                                     disable_web_page_preview=True)


send_player = send_card


# ------------------------------------------------------------------ player buttons
async def player_action(client, cq, _, command, chat_id):
    """Handles the Roohi player buttons (permission checks are done by the caller).
    Returns True when the command was handled here."""
    from RoohiClone.core.call import ROOHI
    from RoohiClone.misc import db
    from RoohiClone.utils.database import (
        autoplay_off, autoplay_on, get_loop, is_autoplay_on, is_music_playing,
        music_off, music_on, set_loop,
    )
    from RoohiClone.utils import equalizer as eqm

    mention = cq.from_user.mention
    base_cmd, _sep, arg = str(command).partition(":")

    async def refresh():
        try:
            await cq.edit_message_reply_markup(InlineKeyboardMarkup(current_markup(_, chat_id, cq.message)))
        except Exception:
            pass

    async def no_song():
        await cq.answer("🔁 " + fancy("No song playing...!"), show_alert=True)
        return True

    async def note(text, delay=45):
        """Small temporary confirmation message with a Close button (like the screenshots)."""
        import asyncio
        try:
            m = await cq.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[btn("Close", cb="close")]]))
        except Exception:
            return

        async def _later():
            await asyncio.sleep(delay)
            try: await m.delete()
            except Exception: pass
        asyncio.create_task(_later())

    # ---------------------------------------------------------- More panel
    if command == "More":
        MORE_OPEN[(cq.message.chat.id, cq.message.id)] = 1
        if len(MORE_OPEN) > 2000:
            MORE_OPEN.clear()
        await cq.answer()
        try:
            await cq.edit_message_reply_markup(InlineKeyboardMarkup(more_markup(_, chat_id)))
        except Exception:
            pass
        return True

    if command == "Back":
        MORE_OPEN.pop((cq.message.chat.id, cq.message.id), None)
        await cq.answer()
        try:
            await cq.edit_message_reply_markup(InlineKeyboardMarkup(player_markup(_, chat_id)))
        except Exception:
            pass
        return True

    if command in ("Mute", "Unmute"):
        if not db.get(chat_id):
            return await no_song()
        try:
            if command == "Mute":
                await ROOHI.mute_stream(chat_id)
                await cq.answer("🔇 " + fancy("Assistant muted in video chat..!"), show_alert=True)
            else:
                await ROOHI.unmute_stream(chat_id)
                await cq.answer("🔊 " + fancy("Assistant unmuted in video chat..!"), show_alert=True)
        except Exception:
            await cq.answer("❌ " + fancy("Failed, try again."), show_alert=True)
        return True

    if command == "Loop":
        if not db.get(chat_id):
            return await no_song()
        cur = await get_loop(chat_id)
        nxt = 5 if cur == 0 else (10 if cur < 10 else 0)
        await set_loop(chat_id, nxt)
        await cq.answer()
        if nxt:
            await note(quote(f"<b>❖ {fancy('Loop enabled')} ({nxt} {fancy('times')}) 🎄</b>\n└ <b>{fancy('By')} ▸</b> {mention}"))
        else:
            await note(quote(f"<b>❖ {fancy('Loop disabled')}</b>\n└ <b>{fancy('By')} ▸</b> {mention}"))
        return True

    if command == "Thumb":
        on = await is_thumb_on(chat_id)
        await set_thumb(chat_id, not on)
        await cq.answer(fancy("Thumbnail disabled") if on else fancy("Thumbnail enabled"))
        await refresh()
        return True

    # ---------------------------------------------------------- equalizer / track mode / volume
    async def apply_audio(fn, fail_text):
        if chat_id in _AUDIO_BUSY:
            await cq.answer("⏳ " + fancy("Another audio change is running."), show_alert=True)
            return False
        _AUDIO_BUSY.add(chat_id)
        try:
            await fn()
            return True
        except Exception:
            await cq.answer("❌ " + fancy(fail_text), show_alert=True)
            return False
        finally:
            _AUDIO_BUSY.discard(chat_id)

    async def set_eq(key):
        if not await is_music_playing(chat_id):
            eqm.set_chat_eq(chat_id, key)      # paused: applies when playback resumes
            return True
        return await apply_audio(lambda: ROOHI.equalizer_stream(chat_id, key), "Equalizer apply failed.")

    def eq_text():
        return quote(
            f"<b>🎚 {fancy('Equalizer panel')}</b>\n│\n"
            f"├ <b>{fancy('Current')} :</b> <code>{fancy(eqm.get_eq_name(eqm.get_chat_eq(chat_id)))}</code>\n"
            f"└ <b>{fancy('Pick an effect - the track keeps playing from the same second.')}</b>")

    def vol_text():
        return quote(
            f"<b>🔊 {fancy('Volume panel')}</b>\n│\n"
            f"├ <b>{fancy('Current')} :</b> <code>{eqm.get_chat_volume(chat_id)}%</code>\n"
            f"└ <b>+50 / -25 · {fancy('boost')} +500 · {fancy('max')} 1000%</b>")

    async def edit_panel(text, rows):
        try:
            await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            pass

    if command == "EqPanel":
        if not db.get(chat_id):
            return await no_song()
        await cq.answer("🎚 " + fancy("Equalizer opened!"))
        try:
            await cq.message.reply_text(eq_text(), reply_markup=InlineKeyboardMarkup(eqm.equalizer_markup(_, chat_id)))
        except Exception:
            pass
        return True

    if command == "TrackMode":
        if not db.get(chat_id):
            return await no_song()
        key = eqm.next_track_mode(chat_id)
        if await set_eq(key):
            await cq.answer()
            await note(quote(
                f"<b>↠ {fancy('Track mode changed')} 🎶</b>\n│\n"
                f"├ <b>{fancy('Mode')} :</b> 🔊 {fancy(eqm.get_eq_name(key))}\n"
                f"└ <b>{fancy('By')} :</b> {mention}"))
        return True

    if base_cmd == "EqSet":
        if not db.get(chat_id):
            return await no_song()
        if arg not in eqm.EQ_PRESETS:
            return await cq.answer("❌", show_alert=True) or True
        was_playing = await is_music_playing(chat_id)
        if await set_eq(arg):
            await cq.answer("🎚 " + fancy(f"{eqm.get_eq_name(arg)} applied." if was_playing else f"{eqm.get_eq_name(arg)} saved - applies from the next track."))
            await edit_panel(eq_text(), eqm.equalizer_markup(_, chat_id))
        return True

    if command == "VolPanel":
        if not db.get(chat_id):
            return await no_song()
        await cq.answer("🔊 " + fancy("Volume panel opened."))
        await edit_panel(vol_text(), eqm.volume_markup(_, chat_id))
        return True

    if command == "VolBack":
        await cq.answer()
        await edit_panel(eq_text(), eqm.equalizer_markup(_, chat_id))
        return True

    if base_cmd == "VolSet":
        if not db.get(chat_id):
            return await no_song()
        old = eqm.get_chat_volume(chat_id)
        new = {"up": min(1000, old + 50), "down": max(0, old - 25), "boost": min(1000, old + 500)}.get(arg)
        if new is None:
            return await cq.answer("❌", show_alert=True) or True
        if new == old:
            return await cq.answer("🔊 " + fancy("Volume is already at its limit."), show_alert=True) or True
        eqm.set_chat_volume(chat_id, new)
        if await is_music_playing(chat_id):
            if not await apply_audio(lambda: ROOHI.volume_stream(chat_id), "Volume update failed."):
                eqm.set_chat_volume(chat_id, old)
                return True
        await cq.answer("🔊 " + fancy(f"Volume set to {new}%."))
        await edit_panel(vol_text(), eqm.volume_markup(_, chat_id))
        return True

    if command == "AudioReset":
        if not db.get(chat_id):
            return await no_song()
        old_eq, old_vol = eqm.get_chat_eq(chat_id), eqm.get_chat_volume(chat_id)
        eqm.reset_chat_audio(chat_id)
        ok = True
        if await is_music_playing(chat_id):
            ok = await apply_audio(lambda: ROOHI.equalizer_stream(chat_id, "off"), "Audio reset failed.")
        if not ok:
            eqm.set_chat_eq(chat_id, old_eq)
            eqm.set_chat_volume(chat_id, old_vol)
            return True
        await cq.answer("✅ " + fancy("EQ Normal · Volume 50%"))
        await edit_panel(vol_text(), eqm.volume_markup(_, chat_id))
        return True

    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await cq.answer(fancy("Stream is already paused."), show_alert=True) or True
        await ROOHI.pause_stream(chat_id)
        await music_off(chat_id)
        await cq.answer(fancy("Stream paused ⏸"))
        try:
            await cq.message.reply_text(_["admin_2"].format(mention))
        except Exception:
            pass
        return True

    if command == "Resume":
        if await is_music_playing(chat_id):
            return await cq.answer(fancy("Stream is already playing."), show_alert=True) or True
        await ROOHI.resume_stream(chat_id)
        await music_on(chat_id)
        await cq.answer(fancy("Stream resumed ▶️"))
        try:
            await cq.message.reply_text(_["admin_4"].format(mention))
        except Exception:
            pass
        return True

    if command in ("Stop", "End"):
        await cq.answer(fancy("Stream stopped."))
        await ROOHI.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        try:
            await cq.message.reply_text(_["admin_5"].format(mention))
            await cq.message.delete()
        except Exception:
            pass
        return True

    if command == "Autoplay":
        if await is_autoplay_on(chat_id):
            await autoplay_off(chat_id)
            await cq.answer(fancy("Autoplay disabled"), show_alert=False)
        else:
            await autoplay_on(chat_id)
            await cq.answer(fancy("Autoplay enabled"), show_alert=False)
        await refresh()
        return True

    if command in ("SeekBack", "SeekForward", "1", "2"):
        delta = -SEEK_STEP if command in ("SeekBack", "1") else SEEK_STEP
        ok, text = await seek_player(chat_id, delta=delta)
        await cq.answer(text, show_alert=not ok)
        if ok:
            await refresh()
        return True

    if command == "Replay":
        ok, text = await seek_player(chat_id, to=0)
        await cq.answer(fancy("Replaying from start ↻") if ok else text, show_alert=not ok)
        if ok:
            await refresh()
        return True

    if command == "Skip":
        if not db.get(chat_id):
            return await cq.answer(fancy("Queue is empty."), show_alert=True) or True
        await cq.answer(fancy("Skipped ‣‣I"))
        await set_loop(chat_id, 0)
        try:
            await cq.message.delete()
        except Exception:
            pass
        clients = await ROOHI.get_active_clients(chat_id)
        await ROOHI.change_stream(clients[0] if clients else ROOHI.one, chat_id)
        return True

    try:
        await cq.answer()
    except Exception:
        pass
    return False


# ------------------------------------------------------------------ live progress updater
_last = {}


async def refresh_players():
    """One loop for main + clones: keeps the progress bar / autoplay label fresh."""
    import asyncio
    from pyrogram.errors import FloodWait
    from RoohiClone.misc import db
    from RoohiClone.utils.database import get_active_chats, is_music_playing

    while True:
        await asyncio.sleep(10)
        try:
            chats = await get_active_chats()
        except Exception:
            continue
        for chat_id in chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                q = db.get(chat_id)
                if not q or not int(q[0].get("seconds", 0) or 0):
                    continue
                mystic = q[0].get("mystic")
                if not mystic:
                    continue
                key = (mystic.chat.id, mystic.id)
                stamp = (int(q[0].get("played", 0)) // 10, _autoplay_state(chat_id))
                if _last.get(key) == stamp:
                    continue
                _last[key] = stamp
                await mystic.edit_reply_markup(InlineKeyboardMarkup(current_markup(None, chat_id, mystic)))
            except FloodWait as e:
                await asyncio.sleep(min(int(e.value), 30))
            except Exception:
                continue
        if len(_last) > 2000:
            _last.clear()


_started = False


def start_refresher():
    global _started
    if _started:
        return
    _started = True
    import asyncio
    try:
        asyncio.get_event_loop().create_task(refresh_players())
    except Exception:
        _started = False


# ------------------------------------------------------------------ help menu
def help_markup(back_cb=None):
    from strings.roohihelp import SECTIONS

    rows, row = [], []
    for k in SECTIONS:
        row.append(btn(SECTIONS[k][0], cb=f"roohihelp {k}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([btn("⟵", cb=back_cb or "roohi_home", font=False)])
    return InlineKeyboardMarkup(rows)


def back_markup(cb="roohihelp home"):
    return InlineKeyboardMarkup([[btn("⟵", cb=cb, font=False)]])


async def roohi_edit(cq, text, markup):
    """Edit a menu message whether it is a photo/video (caption) or plain text."""
    from pyrogram.errors import MessageNotModified

    m = cq.message
    try:
        if m.photo or m.video or m.animation or m.document:
            await cq.edit_message_caption(text, reply_markup=markup)
        else:
            await cq.edit_message_text(text, reply_markup=markup, disable_web_page_preview=True)
    except MessageNotModified:
        pass


async def help_router(client, cq, key, support_link):
    """Shared handler for 'roohihelp <key>' callbacks."""
    from strings.roohihelp import HELP_HOME, SECTIONS
    try:
        await cq.answer()
    except Exception:
        pass
    if key == "home":
        return await roohi_edit(cq, HELP_HOME.format(support_link), help_markup())
    if key in SECTIONS:
        return await roohi_edit(cq, SECTIONS[key][1], back_markup())


# ------------------------------------------------------------------ start buttons
def main_start_markup(bot_username):
    return InlineKeyboardMarkup([
        [btn("✧₊ Add me to your chat ₊✧", url=f"https://t.me/{bot_username}?startgroup=true")],
        [btn("Help & Commands", cb="settings_back_helper")],
        [btn("Updates", url=config.SUPPORT_CHANNEL), btn("Support", url=config.SUPPORT_CHAT)],
    ])


def thumb_markup(chat_id):
    return InlineKeyboardMarkup([
        [btn("Enable", cb=f"roohithumb on|{chat_id}"), btn("Disable", cb=f"roohithumb off|{chat_id}")],
        [btn("Close", cb="close")],
    ])


def thumb_text(on: bool):
    state = fancy("Enabled") if on else fancy("Disabled")
    return (
        f"⦿ <b><u>{fancy('Thumbnail settings')} :</u></b>\n\n"
        f"<blockquote>🎨 <b>{fancy('Album art display')} :</b> {state}</blockquote>\n"
        f"<blockquote expandable>• <b>{fancy('Enable')}</b> : {fancy('display artwork with stream info.')}\n"
        f"• <b>{fancy('Disable')}</b> : {fancy('send pure text-based updates.')}\n"
        f"• <b>{fancy('Close')}</b> : {fancy('dismiss the configuration.')}\n\n"
        f"❏ {fancy('Settings are saved individually per chat.')}</blockquote>"
    )
