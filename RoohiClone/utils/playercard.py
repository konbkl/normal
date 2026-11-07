"""Now-playing player card (1280x720), music-app style.

    path = await make_player_card(videoid)

* blurred, desaturated cover as background, rounded square album art on the left
* title / artist / star + more buttons / progress / volume / transport icons
* everything is drawn at 2x and scaled down, so edges stay smooth
* saved as an optimised JPEG (~60-120 KB) and old cards are pruned from
  cache/ automatically, so thumbnails never fill the disk
"""

import asyncio
import glob
import math
import os
import time
from io import BytesIO

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H, S = 1280, 720, 2

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
CACHE_DIR = "cache"
CARD_GLOB = os.path.join(CACHE_DIR, "roohi_*")
KEEP_FILES = 40          # newest cards that are always kept
MAX_AGE = 2 * 3600       # anything older than this (seconds) is deleted
JPEG_QUALITY = 86

WHITE = (255, 255, 255, 255)
ICON = (247, 247, 247, 255)


# ---------------------------------------------------------------- helpers
def _font(name, size):
    for n in (name, "pc_bold.ttf", "font2.ttf"):
        try:
            return ImageFont.truetype(os.path.join(ASSETS, n), int(round(size * S)))
        except Exception:
            continue
    return ImageFont.load_default()


def _safe_text(text):
    """Inter has no Devanagari / emoji etc. -> transliterate so no boxes show."""
    text = str(text or "").strip()
    if any(ord(c) > 0x024F for c in text):
        try:
            from unidecode import unidecode
            text = unidecode(text).strip()
        except Exception:
            text = "".join(c for c in text if ord(c) <= 0x024F).strip()
    return " ".join(text.split()) or "Unknown"


def _fit(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w * S:
        return text
    while text and draw.textlength(text + " ...", font=font) > max_w * S:
        text = text[:-1]
    return text.rstrip() + " ..."


def _secs(duration):
    try:
        return sum(int(x) * 60 ** i for i, x in enumerate(reversed(str(duration).split(":"))))
    except Exception:
        return 0


def _fmt(sec):
    sec = max(0, int(sec))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _bot_name():
    try:
        from RoohiClone import app
        name = (app.me.first_name if app.me else None) or app.name
        return _safe_text(name)
    except Exception:
        return "Music Bot"


# ---------------------------------------------------------------- background + art
def _background(thumb):
    small = ImageOps.fit(thumb, (320, 180), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.6))
    bg = small.resize((W, H), Image.BICUBIC)
    bg = ImageEnhance.Color(bg).enhance(0.3)
    bg = ImageEnhance.Brightness(bg).enhance(0.6)
    return bg.convert("RGBA")


def _album(thumb):
    """512x512 rounded album art, centre-cropped from the cover."""
    size, radius, ss = 512, 38, 4
    art = ImageOps.fit(thumb, (size, size), Image.LANCZOS, centering=(0.5, 0.5)).convert("RGBA")
    mask = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * ss - 1, size * ss - 1), radius=radius * ss, fill=255)
    art.putalpha(mask.resize((size, size), Image.LANCZOS))
    return art


# ---------------------------------------------------------------- icons (1x coordinates)
def _sx(v):
    return v * S


def _tri(d, pts, color, r=2.2):
    p = [(_sx(x), _sx(y)) for x, y in pts]
    d.polygon(p, fill=color)
    d.line(p + [p[0]], fill=color, width=int(r * 2 * S), joint="curve")


def _pill(d, x0, y0, x1, y1, fill):
    d.rounded_rectangle((_sx(x0), _sx(y0), _sx(x1), _sx(y1)), radius=_sx((y1 - y0) / 2), fill=fill)


def _dot(d, x, y, r, fill):
    d.ellipse((_sx(x - r), _sx(y - r), _sx(x + r), _sx(y + r)), fill=fill)


def _star(d, cx, cy, ro, ri, color, w):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = ro if i % 2 == 0 else ri
        pts.append((_sx(cx + r * math.cos(ang)), _sx(cy + r * math.sin(ang))))
    d.line(pts + [pts[0]], fill=color, width=int(w * S), joint="curve")


def _speaker(d, x, cy, waves, color):
    d.rounded_rectangle((_sx(x), _sx(cy - 3.6), _sx(x + 6), _sx(cy + 3.6)), radius=_sx(1.2), fill=color)
    d.polygon([(_sx(x + 4), _sx(cy - 3.6)), (_sx(x + 13), _sx(cy - 10)),
               (_sx(x + 13), _sx(cy + 10)), (_sx(x + 4), _sx(cy + 3.6))], fill=color)
    if waves:
        cx = _sx(x + 14)
        for r in (5.5, 10.0, 14.5):
            R = _sx(r)
            d.arc((cx - R, _sx(cy) - R, cx + R, _sx(cy) + R), start=-48, end=48, fill=color, width=int(2.3 * S))


def _lyrics(d, color):
    x, y = 817, 565
    d.rounded_rectangle((_sx(x + 1.6), _sx(y + 1.6), _sx(x + 34.4), _sx(y + 26)), radius=_sx(7), outline=color, width=int(3.2 * S))
    d.polygon([(_sx(x + 8), _sx(y + 24)), (_sx(x + 8), _sx(y + 35)), (_sx(x + 19), _sx(y + 24))], fill=color)
    for qx in (12.5, 24.0):
        _dot(d, x + qx, y + 12, 3.5, color)
        d.line([(_sx(x + qx + 2.6), _sx(y + 12.5)), (_sx(x + qx - 0.4), _sx(y + 19))], fill=color, width=int(2.4 * S))


def _list(d, color):
    x, y = 1024, 567
    for ly in (2.3, 13.5, 24.7):
        _dot(d, x + 2.6, y + ly, 2.6, color)
        _pill(d, x + 9, y + ly - 2.4, x + 37, y + ly + 2.4, color)


# ---------------------------------------------------------------- card
def render_card(thumb, title, artist, duration, bot_name="Music Bot", played=3):
    thumb = thumb.convert("RGB")
    base = _background(thumb)
    base.alpha_composite(_album(thumb), (100, 104))

    ui = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ui)

    f_title = _font("pc_inter_bold.otf", 22.8)
    f_artist = _font("pc_inter_regular.otf", 22)
    f_time = _font("pc_inter_bold.otf", 18)
    f_rem = _font("pc_inter_regular.otf", 18)
    f_chip = _font("pc_inter_regular.otf", 14)

    total = _secs(duration)
    title = _fit(d, _safe_text(title), f_title, 262)
    artist = _fit(d, _safe_text(artist), f_artist, 300)

    # title / artist
    d.text((_sx(727), _sx(144.5)), title, font=f_title, fill=WHITE, anchor="ls")
    d.text((_sx(728), _sx(184)), artist, font=f_artist, fill=(200, 200, 200, 255), anchor="ls")

    # star + more buttons
    for cx in (1067.5, 1140.0):
        r = 22.8
        d.ellipse((_sx(cx - r), _sx(145.5 - r), _sx(cx + r), _sx(145.5 + r)), fill=(255, 255, 255, 92))
    _star(d, 1067.5, 145.5, 12.6, 5.3, WHITE, 2.2)
    for dy in (-9, 0, 9):
        _dot(d, 1140, 145.5 + dy, 2.7, WHITE)

    # progress bar
    x0, x1, y0, y1 = 718, 1161, 218, 230
    _pill(d, x0, y0, x1, y1, (255, 255, 255, 82))
    frac = min(1.0, played / total) if total else 0.0
    fx = x0 + max(14, (x1 - x0) * frac)
    _pill(d, x0, y0, fx, y1, (244, 244, 244, 255))
    d.rectangle((_sx(x0 + 6), _sx(y0), _sx(fx), _sx(y1)), fill=(244, 244, 244, 255))  # flat right end

    # times
    d.text((_sx(716), _sx(266)), _fmt(played), font=f_time, fill=(208, 208, 208, 255), anchor="ls")
    rem = f"-{_fmt(total - played)}" if total else "LIVE"
    d.text((_sx(1155), _sx(266)), rem, font=f_rem, fill=(196, 196, 196, 255), anchor="rs")

    # bot name chip
    name = _fit(d, bot_name, f_chip, 150)
    tw = d.textlength(name, font=f_chip) / S
    cw, cx = tw + 24, 925
    d.rounded_rectangle((_sx(cx - cw / 2), _sx(246), _sx(cx + cw / 2), _sx(265)), radius=_sx(4.5), fill=(255, 255, 255, 64))
    d.text((_sx(cx), _sx(259.5)), name, font=f_chip, fill=(214, 214, 214, 255), anchor="ms")

    # transport: rewind, pause, forward
    _tri(d, [(781, 359.5), (746.5, 379.7), (781, 399.8)], ICON)
    _tri(d, [(814, 359.5), (781.5, 379.7), (814, 399.8)], ICON)
    d.rounded_rectangle((_sx(913), _sx(348), _sx(934), _sx(411)), radius=_sx(5), fill=ICON)
    d.rounded_rectangle((_sx(944), _sx(348), _sx(965), _sx(411)), radius=_sx(5), fill=ICON)
    _tri(d, [(1065, 359.5), (1098, 379.7), (1065, 399.8)], ICON)
    _tri(d, [(1099, 359.5), (1131, 379.7), (1099, 399.8)], ICON)

    # volume
    _pill(d, 766, 493, 1094, 504, (242, 242, 242, 255))
    _speaker(d, 725, 498.5, False, (236, 236, 236, 255))
    _speaker(d, 1120, 498.5, True, (236, 236, 236, 255))

    # bottom icons
    _lyrics(d, (240, 240, 240, 255))
    _list(d, (240, 240, 240, 255))

    ui = ui.resize((W, H), Image.LANCZOS)
    base.alpha_composite(ui)
    return base.convert("RGB")


# ---------------------------------------------------------------- data + public API
def _strip_bars(img):
    """hqdefault is 4:3 with black bars -> crop to the real 16:9 picture."""
    w, h = img.size
    if abs(w / h - 4 / 3) < 0.05:
        nh = int(w * 9 / 16)
        top = (h - nh) // 2
        img = img.crop((0, top, w, top + nh))
    return img


async def _fetch(videoid):
    from youtubesearchpython.__future__ import VideosSearch

    title, artist, duration = "Unknown Title", "Unknown Artist", "0:00"
    try:
        data = await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next()
        r = data["result"][0]
        title = str(r.get("title") or title)
        artist = str((r.get("channel") or {}).get("name") or artist)
        duration = str(r.get("duration") or duration)
    except Exception as e:
        print(f"[PLAYERCARD] info fetch failed: {e}")

    thumb = None
    for name in ("maxresdefault", "hq720", "hqdefault", "mqdefault"):
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(f"https://i.ytimg.com/vi/{videoid}/{name}.jpg") as resp:
                    if resp.status == 200:
                        thumb = _strip_bars(Image.open(BytesIO(await resp.read())).convert("RGB"))
                        break
        except Exception as e:
            print(f"[PLAYERCARD] thumb fetch failed ({name}): {e}")
    if thumb is None:
        thumb = Image.new("RGB", (640, 360), (60, 60, 68))
    return title, artist, duration, thumb


def prune_cache(keep=KEEP_FILES, max_age=MAX_AGE, protect=None):
    """Delete old player cards (and leftover .png cards) so storage never fills up."""
    try:
        now = time.time()
        files = []
        for f in glob.glob(CARD_GLOB):
            try:
                files.append((os.path.getmtime(f), f))
            except OSError:
                pass
        files.sort(reverse=True)
        for i, (mt, f) in enumerate(files):
            if f == protect:
                continue
            if f.endswith(".png") or i >= keep or now - mt > max_age:
                try:
                    os.remove(f)
                except OSError:
                    pass
    except Exception:
        pass


async def make_player_card(videoid, user_id=None):
    os.makedirs(CACHE_DIR, exist_ok=True)
    out = os.path.join(CACHE_DIR, f"roohi_{videoid}.jpg")
    if os.path.exists(out):
        os.utime(out, None)  # still in use -> keep it fresh
        return out
    try:
        title, artist, duration, thumb = await _fetch(videoid)
        bot = _bot_name()
        loop = asyncio.get_running_loop()

        def _build():
            img = render_card(thumb, title, artist, duration, bot)
            tmp = out + ".tmp"
            img.save(tmp, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True, subsampling=0)
            os.replace(tmp, out)

        await loop.run_in_executor(None, _build)
        await loop.run_in_executor(None, prune_cache, KEEP_FILES, MAX_AGE, out)
        return out
    except Exception as e:
        print(f"[PLAYERCARD] render failed: {e}")
        return None
    
