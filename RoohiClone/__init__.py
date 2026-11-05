# ---- Roohi UI: safe coloured buttons everywhere ----
import config as _cfg
from pyrogram import enums as _enums
from pyrogram.types import InlineKeyboardButton as _IKB

import random as _random

_COLOURS = (_enums.ButtonStyle.PRIMARY, _enums.ButtonStyle.SUCCESS, _enums.ButtonStyle.DANGER)
_ikb_init = _IKB.__init__


def _safe_ikb_init(self, *args, **kwargs):
    style = kwargs.get("style")
    if style is None:
        # every button without a colour gets a random one (blue / green / red)
        kwargs["style"] = _random.choice(_COLOURS)
    elif not isinstance(style, _enums.ButtonStyle):
        name = str(getattr(style, "value", style)).upper()
        kwargs["style"] = getattr(_enums.ButtonStyle, name, _enums.ButtonStyle.PRIMARY)
    icon = kwargs.get("icon_custom_emoji_id")
    if icon is not None:
        if getattr(_cfg, "BUTTON_ICONS", False):
            kwargs["icon_custom_emoji_id"] = str(icon)
        else:
            kwargs.pop("icon_custom_emoji_id")
    _ikb_init(self, *args, **kwargs)


_IKB.__init__ = _safe_ikb_init

from RoohiClone.core.bot import ROOHI
from RoohiClone.core.dir import dirr
from RoohiClone.core.git import git
from RoohiClone.core.userbot import Userbot
from RoohiClone.misc import dbb, heroku
from pyrogram import Client
from SafoneAPI import SafoneAPI
from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = ROOHI()
api = SafoneAPI()
userbot = Userbot()

from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
