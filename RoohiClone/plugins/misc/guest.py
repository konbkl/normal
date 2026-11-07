from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultPhoto,
    Message,
)

from ShiviMusic import app


# ==========================================================
# GUEST MESSAGE
# ==========================================================

ADD_ME_PROMO_TEXT = (
    "❖ <a href=\"https://t.me/{username}\">˹{name}˼ ♪</a> — <b>Your Premium Music Streamer Bot 🍂</b>\n\n"
    
    "<blockquote><b>▸ Fast • Lag Free • No Ads 🍂</b>\n"
    "<b>▸ Auto-Play • Audio • Video 🎥</b></blockquote>\n\n"
    
    "<b>◼️ Add</b> <a href=\"https://t.me/{username}\">˹{name}˼ ♪</a> <b>To Your Group & Enjoy High Quality Songs ❄️</b>"
)


# ==========================================================
# BUTTONS
# ==========================================================

def _add_me_markup(username: str):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="✙ Add Me In Your Group ✙",
                    url=f"https://t.me/{username}?startgroup=true",
                )
            ]
        ]
    )


# ==========================================================
# GUEST MODE
# ==========================================================

@app.on_guest_message()
async def guest_username_mention(_, message: Message):

    guest_query_id = getattr(
        message,
        "guest_query_id",
        None,
    )

    if not guest_query_id:
        return

    try:

        # --------------------------------------------------
        # GET BOT INFORMATION 
        # --------------------------------------------------

        me = await app.get_me()

        # Full bot name 
        name = me.first_name or "Music Bot"

        if me.last_name:
            name = f"{name} {me.last_name}"

        # Bot username
        username = me.username

        if not username:
            return

        # --------------------------------------------------
        # CREATE MESSAGE
        # --------------------------------------------------

        promo_text = ADD_ME_PROMO_TEXT.format(
            name=name,
            username=username,
        )

        # --------------------------------------------------
        # KEYBOARD
        # --------------------------------------------------

        keyboard = _add_me_markup(username)

        # --------------------------------------------------
        # INLINE RESULT (WITH PHOTO)
        # --------------------------------------------------

        result = InlineQueryResultPhoto(
            photo_url="https://files.catbox.moe/t6q1xz.jpg",
            thumb_url="https://files.catbox.moe/t6q1xz.jpg",
            title=f"❖ {name} ♪",
            description=f"@{username} • Add Me In Your Group 🎶",
            caption=promo_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

        # --------------------------------------------------
        # ANSWER GUEST QUERY
        # --------------------------------------------------

        await app.answer_guest_query(
            guest_query_id,
            result=result,
        )

    except Exception as e:

        print(
            f"Guest Mode Error: {type(e).__name__}: {e}"
        )
