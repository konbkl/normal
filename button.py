"""Coloured inline buttons.

Old code used its own Enum here, which kurigram silently ignored (all buttons
came out without colour). ButtonStyle now maps to pyrogram's real enum.
"""
from pyrogram.enums import ButtonStyle as _BS
from pyrogram.types import InlineKeyboardButton

import config


class ButtonStyle:
    DEFAULT = _BS.DEFAULT
    PRIMARY = _BS.PRIMARY      # blue
    SUCCESS = _BS.SUCCESS      # green
    DANGER = _BS.DANGER        # red
    # old aliases kept so nothing breaks
    SECONDARY = _BS.PRIMARY
    INFO = _BS.PRIMARY
    TRANSPARENT = _BS.DEFAULT


def styled_button(text: str, callback_data: str = None, url: str = None,
                  user_id: int = None, style=ButtonStyle.PRIMARY, **kwargs):
    params = {"text": text}
    if url:
        params["url"] = url
    elif user_id:
        params["user_id"] = user_id
    else:
        params["callback_data"] = callback_data or "none"
    if isinstance(style, str):
        style = getattr(_BS, style.upper(), _BS.PRIMARY)
    params["style"] = style
    icon = kwargs.pop("icon_custom_emoji_id", None)
    if icon and getattr(config, "BUTTON_ICONS", False):
        params["icon_custom_emoji_id"] = str(icon)
    params.update(kwargs)
    return InlineKeyboardButton(**params)


class RandomStyleMap(dict):
    """style_map[n] -> a fresh random colour on every access (Roohi look)."""

    def __init__(self, styles=None):
        super().__init__()
        self.styles = list(styles or (_BS.PRIMARY, _BS.SUCCESS, _BS.DANGER))

    def __getitem__(self, key):
        import random
        return random.choice(self.styles)

    def get(self, key, default=None):
        return self[key]
