import asyncio
import random
import math
from pyrogram.types import CallbackQuery, InputMediaPhoto, InputMediaVideo, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from pyrogram.errors import WebpageMediaEmpty
from pyrogram.enums import ButtonStyle, ChatMemberStatus

from RoohiClone import YouTube, app
from RoohiClone.core.call import ROOHI
from RoohiClone.misc import SUDOERS, db
from RoohiClone.utils.database import (
    get_active_chats, get_lang, get_upvote_count, is_active_chat,
    is_music_playing, is_nonadmin_chat, music_off, music_on, set_loop, get_assistant,
    is_autoplay_on, autoplay_on, autoplay_off
)

from RoohiClone.utils.decorators.language import languageCB
from RoohiClone.utils.formatters import seconds_to_min
from RoohiClone.utils.inline import close_markup, stream_markup, stream_markup_timer
from RoohiClone.utils.stream.autoclear import auto_clean
from RoohiClone.utils.thumbnails import get_thumb
import config
from config import (
    BANNED_USERS, SOUNCLOUD_IMG_URL, STREAM_IMG_URL, TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL, START_IMG_URL, adminlist, confirmer, votemode
)
from strings import get_string
from RoohiClone.utils.inline.start import private_panel

checker = {}
upvoters = {}

# 💎 Premium Emojis ID List
PREMIUM_EMOJIS = [
    5258362837411045098, 6102938383456146362, 5463274047771000031, 6100397162976252509,
    5373310679241466020, 5408916593780470262, 5776182936638329359, 5258389041006518073,
    6280269890821558384, 5936143551854285132, 6172332822892647766, 5891211339170326418,
    5409368076447657845, 6172312314423808834, 6082387600599944892, 6271537028307881531
]

# 🎨 Dynamic Color Generator
def get_style_map():
    styles = [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
    random.shuffle(styles)
    from button import RandomStyleMap

    return RandomStyleMap(styles)

# 🔘 Smart Button Creator
def create_btn(text, cb=None, url=None, style=ButtonStyle.PRIMARY, emoji_id=None, no_emoji=False):
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    
    # Premium Emoji Logic
    if emoji_id:
        kwargs["icon_custom_emoji_id"] = int(emoji_id)
    elif not no_emoji:
        kwargs["icon_custom_emoji_id"] = int(random.choice(PREMIUM_EMOJIS))
        
    return InlineKeyboardButton(**kwargs)

@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_helper(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass

    if isinstance(START_IMG_URL, list):
        img = random.choice(START_IMG_URL)
    else:
        img = START_IMG_URL

    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media=img,
            caption=_["start_2"].format(CallbackQuery.from_user.mention, app.mention)
        ),
        reply_markup=InlineKeyboardMarkup(private_panel(_))
    )

@app.on_callback_query(filters.regex("support_page") & ~BANNED_USERS)
@languageCB
async def support_page_cb(client, CallbackQuery, _):
    await CallbackQuery.answer()
    style_map = get_style_map()
    support_text = (
        f"<blockquote><b><tg-emoji emoji-id=\"6172312314423808834\">✨</tg-emoji> ᴡєʟᴄσϻє ᴛσ ᴛʜє sυᴘᴘσʀᴛ ϻєηυ <tg-emoji emoji-id=\"6172312314423808834\">✨</tg-emoji></b>\n\n"
        f"<b>ɪғ ʏσυ ηєєᴅ ᴧηʏ ʜєʟᴘ ʀєɢᴧʀᴅɪηɢ ᴛʜє ʙσᴛ σʀ ᴡᴧηᴛ ᴛσ ʀєᴘσʀᴛ ᴧ ʙυɢ, "
        f"ᴊσɪη συʀ sυᴘᴘσʀᴛ ᴄʜᴧᴛ σʀ ᴄʜᴧηηєʟ ʙєʟσᴡ.</b></blockquote>"
    )

    custom_support_buttons = [
        [
            create_btn(text="υᴘᴅᴧᴛєs", url="https://t.me/betabot_hub", style=style_map[1], emoji_id=6039381989985882045),
            create_btn(text="sυᴘᴘσʀᴛ", url="https://t.me/betabot_support", style=style_map[2], emoji_id=6021618194228187816)
        ],
        [
            create_btn(text="ʙσᴛs", url="https://t.me/betabot_hub/6701", style=style_map[3], emoji_id=5355051922862653659)
        ],
        [
            create_btn(text="ʙᴧᴄᴋ", cb="settingsback_helper", style=style_map[4], emoji_id=5352759161945867747)
        ]
    ]

    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media="https://files.catbox.moe/4hl7n8.jpg", 
            caption=support_text
        ),
        reply_markup=InlineKeyboardMarkup(custom_support_buttons)
    )

@app.on_callback_query(filters.regex("gib_source"))
async def gib_repo_callback(_, callback_query):
    try:
        image_url = "https://h.uguu.se/eJnvkhyK.jpg"
        style_map = get_style_map()
        await callback_query.edit_message_media(
            media=InputMediaPhoto(
                media=image_url, 
                caption=f"<blockquote><b><tg-emoji emoji-id=\"5258389041006518073\">📂</tg-emoji> ʀєᴘσ = ||ɪsᴛᴋʜᴧʀ ᴧηᴅ ᴅєᴠɪʟ ᴋσ ᴘᴧᴘᴧ ʙσʟ ᴄʜᴧʟ ʙσʟ😎||</b></blockquote>"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        create_btn(text="ʙᴧᴄᴋ", cb="settingsback_helper", style=style_map[1], emoji_id=5352759161945867747),
                        create_btn(text="ᴄʟσsє", cb="close", style=style_map[2], emoji_id=6271611232457855630)
                    ]
                ]
            ),
        )
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("unban_assistant"))
async def unban_assistant(_, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    userbot = await get_assistant(chat_id)
    try:
        await app.unban_chat_member(chat_id, userbot.id)
        await callback.answer("✅ ᴧssɪsᴛᴧηᴛ υηʙᴧηηєᴅ sυᴄᴄєssғυʟʟʏ!", show_alert=True)
    except Exception:
        await callback.answer("❌ ғᴧɪʟєᴅ ᴛσ υηʙᴧη. ɢɪᴠє ϻє ᴧᴅϻɪη ᴘєʀϻɪssɪσηs.", show_alert=True)

@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    counter = None
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    mention = CallbackQuery.from_user.mention
    style_map = get_style_map()

    if command == "UpVote":
        if chat_id not in votemode: votemode[chat_id] = {}
        if chat_id not in upvoters: upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters: upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote: votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] += 1

        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])

        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
                if current["vidid"] != exists["vidid"] or current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message_text(_["admin_35"])
            except:
                return await CallbackQuery.edit_message_text(_["admin_36"])
            try:
                await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
            except:
                pass
            command = counter
            mention = "υᴘᴠσᴛєs"
        else:
            if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)

            upl = InlineKeyboardMarkup([
                [create_btn(text=f"{get_upvotes}", cb=f"ADMIN  UpVote|{chat_id}_{counter}", style=style_map[1], emoji_id=6041720006973067267)]
            ])
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            return await CallbackQuery.edit_message_reply_markup(reply_markup=upl)
    else:
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(CallbackQuery.message.chat.id)
                allowed = bool(admins and CallbackQuery.from_user.id in admins)
                if not allowed:
                    try:
                        member = await client.get_chat_member(
                            CallbackQuery.message.chat.id,
                            CallbackQuery.from_user.id,
                        )
                        allowed = member.status in (
                            ChatMemberStatus.ADMINISTRATOR,
                            ChatMemberStatus.OWNER,
                        )
                    except Exception:
                        allowed = False
                if not allowed:
                    return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    from RoohiClone.utils.roohi import player_action
    await player_action(client, CallbackQuery, _, command, chat_id)


@app.on_callback_query(filters.regex("^GetTimer$") & ~BANNED_USERS)
async def get_timer_cb(client, CallbackQuery):
    from RoohiClone.utils.roohi import progress_bar
    playing = db.get(CallbackQuery.message.chat.id)
    if not playing:
        return await CallbackQuery.answer("ɴσᴛʜɪηɢ ɪs ᴘʟᴧʏɪηɢ.")
    await CallbackQuery.answer(f"⏱ {progress_bar(playing[0].get('played', 0), playing[0].get('dur', '00:00'))}")


# shared progress-bar updater
from RoohiClone.utils.roohi import start_refresher
start_refresher()

@app.on_message(filters.video & filters.private)
async def get_my_own_file_id(client, message):
    await message.reply_text(f"<blockquote><b><tg-emoji emoji-id=\"5409143496902716934\">🖼</tg-emoji> ϻєʀᴧ ᴠɪᴅєσ ғɪʟє ɪᴅ (ɪsᴋσ ᴄσᴘʏ ᴋᴧʀσ) :</b>\n<code>{message.video.file_id}</code></blockquote>")
