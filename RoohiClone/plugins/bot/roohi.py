"""Roohi-style extras for the main bot: help router, start home, /nothumb."""
import random

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InputMediaPhoto

import config
from RoohiClone import app
from RoohiClone.misc import SUDOERS
from RoohiClone.utils.roohi import (fancy, help_router, is_thumb_on, main_start_markup,
                                  roohi_edit, set_thumb, thumb_markup, thumb_text)
from config import BANNED_USERS, START_IMG_URL
from roohifont import start_caption


@app.on_callback_query(filters.regex(r"^roohihelp ") & ~BANNED_USERS)
async def roohi_help_cb(client, cq):
    key = cq.data.split(None, 1)[1]
    await help_router(client, cq, key, support_link=config.SUPPORT_CHAT)


@app.on_callback_query(filters.regex(r"^roohi_home$") & ~BANNED_USERS)
async def roohi_home_cb(client, cq):
    try:
        await cq.answer()
    except Exception:
        pass
    caption = start_caption(cq.from_user.mention, app.mention)
    markup = main_start_markup(app.username)
    img = random.choice(START_IMG_URL) if isinstance(START_IMG_URL, list) else START_IMG_URL
    try:
        await cq.edit_message_media(InputMediaPhoto(img, caption=caption), reply_markup=markup)
    except Exception:
        await roohi_edit(cq, caption, markup)


async def _is_admin(client, chat_id, user_id):
    if user_id in SUDOERS:
        return True
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


@app.on_message(filters.command(["nothumb", "thumb", "thumbnail"]) & filters.group & ~BANNED_USERS)
async def nothumb_cmd(client, message):
    if not message.from_user or not await _is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text(f"<blockquote><b>{fancy('Only admins can change this.')}</b></blockquote>")
    on = await is_thumb_on(message.chat.id)
    await message.reply_text(thumb_text(on), reply_markup=thumb_markup(message.chat.id))


@app.on_callback_query(filters.regex(r"^roohithumb ") & ~BANNED_USERS)
async def nothumb_cb(client, cq):
    action, chat_id = cq.data.split(None, 1)[1].split("|")
    chat_id = int(chat_id)
    if not await _is_admin(client, chat_id, cq.from_user.id):
        return await cq.answer(fancy("Only admins can change this."), show_alert=True)
    await set_thumb(chat_id, action == "on")
    await cq.answer(fancy("Thumbnail enabled") if action == "on" else fancy("Thumbnail disabled"))
    await roohi_edit(cq, thumb_text(action == "on"), thumb_markup(chat_id))


@app.on_message(filters.video_chat_started, group=21)
async def main_vc_started(client, message):
    from roohifont import quote
    try:
        await message.reply_text(quote(
            f"<b>♻️ {fancy('Voice chat started!')}</b>\n\n"
            f"{fancy('Use')} /play [{fancy('song name')}] {fancy('to play music.')}"))
    except Exception:
        pass
