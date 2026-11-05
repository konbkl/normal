import asyncio
import random
from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from RoohiClone import app

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

# 🔘 Smart Button Creator (Font updated to Premium style)
def create_btn(text, cb=None, url=None, user_id=None, style=ButtonStyle.PRIMARY, no_emoji=False):
    # Text ko premium font mein convert kiya (Simplified replacement)
    # Agar tumhare system mein custom font support hai toh yeh tag kaam karega
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    if user_id: kwargs["user_id"] = user_id
    if not no_emoji: kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
    return InlineKeyboardButton(**kwargs)

def start_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="✙ ᴧᴅᴅ ϻє ᴛσ ʏσᴜʀ ɢʀσυᴘ ✙", 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map[2]
            ),
            create_btn(
                text="sυᴘᴘσʀᴛ", 
                url=config.SUPPORT_CHAT, 
                style=s_map[2]
            ),
        ],
    ]
    return buttons

def private_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="ᴧᴅᴅ ϻє ᴛσ ʏσᴜʀ ɢʀσυᴘ",
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map[1]
            )
        ],
        [
            create_btn(
                text="σᴡηєʀ", 
                user_id=config.OWNER_ID, 
                style=s_map[2]
            )
        ],
        [
            create_btn(
                text="sυᴘᴘσʀᴛ", 
                cb="support_page", 
                style=s_map[2]
            ),
            create_btn(
                text="sσυʀᴄє", 
                cb="gib_source", 
                style=s_map[2]
            )
        ],
        [
            create_btn(
                text="ʜєʟᴘ ᴧηᴅ ᴄσϻϻᴧηᴅs", 
                cb="settings_back_helper", 
                style=s_map[1]
            )
        ],
    ]
    return buttons

def support_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="sυᴘᴘσʀᴛ", 
                url=config.SUPPORT_CHAT, 
                style=s_map[2]
            ),
            create_btn(
                text="υᴘᴅᴧᴛєs", 
                url=config.SUPPORT_CHANNEL, 
                style=s_map[2]
            ),
        ],
        [
            create_btn(
                text="ʙᴧᴄᴋ", 
                cb="settingsback_helper", 
                style=s_map[1]
            )
        ]
    ]
    return buttons

def about_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="σᴡηєʀ", 
                user_id=config.OWNER_ID, 
                style=s_map[2]
            ),
            create_btn(
                text="ɢɪᴛʜυʙ", 
                url=config.GITHUB, 
                style=s_map[2]
            ),
        ],
        [
            create_btn(
                text="υᴘᴅᴧᴛєs", 
                url=config.SUPPORT_CHANNEL, 
                style=s_map[2]
            ),
            create_btn(
                text="sυᴘᴘσʀᴛ", 
                url=config.SUPPORT_CHAT, 
                style=s_map[2]
            )
        ],
        [
            create_btn(
                text="ʙᴧᴄᴋ", 
                cb="settingsback_helper", 
                style=s_map[1]
            )
        ]
    ]
    return buttons
    


# ================================================================
# ROOHI STYLE START BUTTONS
# ================================================================
from RoohiClone.utils.roohi import btn as _mbtn, main_start_markup as _roohi_start


def private_panel(_):
    return _roohi_start(app.username).inline_keyboard


def start_panel(_):
    return [[
        _mbtn("✚ Add me ✚", url=f"https://t.me/{app.username}?startgroup=true"),
        _mbtn("Support", url=config.SUPPORT_CHAT),
    ]]
