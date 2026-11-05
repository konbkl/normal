"""🎚 Equalizer / track-mode / volume engine (ported from redwinemusic).

Every preset is a plain ffmpeg audio-filter chain (no spaces!) that is handed
to py-tgcalls through MediaStream(ffmpeg_parameters="--audio ---mid -af <chain>").
State is per chat and resets when the chat's stream ends.
"""

# key: (button name, ffmpeg -af chain)
EQ_PRESETS = {
    "off":      ("Normal",        ""),
    "echo":     ("Echo",          "aecho=0.8:0.9:400:0.35"),
    "clear":    ("Clear Audio",   "highpass=f=60,equalizer=f=1000:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1:g=4,dynaudnorm=f=200"),
    "dj":       ("DJ Bass",       "bass=g=12:f=70:w=0.6,treble=g=4,acompressor=ratio=3,dynaudnorm=f=150"),
    "bass":     ("Bass Boost",    "bass=g=9:f=90:w=0.5"),
    "deep":     ("Deep Bass",     "bass=g=15:f=55:w=0.7,lowpass=f=12000"),
    "8d":       ("8D Audio",      "apulsator=hz=0.09,stereotools=mlev=0.05,bass=g=4"),
    "lofi":     ("Lo-Fi",         "highpass=f=200,lowpass=f=3500,acompressor=ratio=4,aecho=0.8:0.85:60:0.25"),
    "vocal":    ("Vocal",         "highpass=f=120,equalizer=f=2500:t=q:w=2:g=6,dynaudnorm=f=200"),
    "treble":   ("Treble",        "treble=g=10:f=4000"),
    "soft":     ("Soft",          "volume=0.8,lowpass=f=8000"),
    "party":    ("Party",         "bass=g=8,treble=g=6,extrastereo=m=2.0,dynaudnorm=f=150"),
    "nightcore":("Nightcore",     "asetrate=48000*1.25,aresample=48000,atempo=1.0"),
    "slowed":   ("Slowed+Reverb", "asetrate=48000*0.85,aresample=48000,aecho=0.8:0.88:60:0.4"),
}

# "Track mode" button cycles through these (first one = back to normal)
TRACK_MODES = ["off", "echo", "bass", "8d", "nightcore", "slowed", "lofi", "party"]

EQ_STATE = {}        # chat_id -> preset key
VOLUME_STATE = {}    # chat_id -> volume %
MIN_VOLUME, DEFAULT_VOLUME, MAX_VOLUME = 0, 50, 1000


def _cid(chat_id):
    try:
        return int(chat_id)
    except Exception:
        return chat_id


def get_eq_filter(preset):
    data = EQ_PRESETS.get(str(preset))
    return data[1] if data else ""


def get_eq_name(preset):
    data = EQ_PRESETS.get(str(preset))
    return data[0] if data else EQ_PRESETS["off"][0]


def get_chat_eq(chat_id):
    return EQ_STATE.get(_cid(chat_id), "off")


def get_chat_eq_filter(chat_id):
    return get_eq_filter(get_chat_eq(chat_id))


def set_chat_eq(chat_id, preset):
    if str(preset) == "off":
        EQ_STATE.pop(_cid(chat_id), None)
    else:
        EQ_STATE[_cid(chat_id)] = str(preset)


def next_track_mode(chat_id):
    cur = get_chat_eq(chat_id)
    if cur not in TRACK_MODES:
        return TRACK_MODES[0]
    return TRACK_MODES[(TRACK_MODES.index(cur) + 1) % len(TRACK_MODES)]


def get_chat_volume(chat_id):
    try:
        return max(MIN_VOLUME, min(MAX_VOLUME, int(VOLUME_STATE.get(_cid(chat_id), DEFAULT_VOLUME))))
    except (TypeError, ValueError):
        return DEFAULT_VOLUME


def set_chat_volume(chat_id, volume):
    try:
        volume = int(volume)
    except (TypeError, ValueError):
        volume = DEFAULT_VOLUME
    VOLUME_STATE[_cid(chat_id)] = max(MIN_VOLUME, min(MAX_VOLUME, volume))


def reset_chat_audio(chat_id):
    """Normal EQ + default 50 % volume."""
    set_chat_eq(chat_id, "off")
    set_chat_volume(chat_id, DEFAULT_VOLUME)


def clear_chat_audio(chat_id):
    EQ_STATE.pop(_cid(chat_id), None)
    VOLUME_STATE.pop(_cid(chat_id), None)


def get_chat_volume_filter(chat_id):
    volume = get_chat_volume(chat_id)
    if volume == DEFAULT_VOLUME:
        return ""
    return f"volume={volume / DEFAULT_VOLUME:.2f}"


# ------------------------------------------------------------------ keyboards
def equalizer_markup(_, chat_id):
    from RoohiClone.utils.roohi import btn
    current = get_chat_eq(chat_id)
    rows, row = [], []
    for key, (name, _f) in EQ_PRESETS.items():
        label = f"{name} · ON" if key == current else name
        row.append(btn(label, cb=f"ADMIN EqSet:{key}|{chat_id}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([btn(f"Volume · {get_chat_volume(chat_id)}%", cb=f"ADMIN VolPanel|{chat_id}")])
    rows.append([btn("Close", cb="close")])
    return rows


def volume_markup(_, chat_id):
    from RoohiClone.utils.roohi import btn
    volume = get_chat_volume(chat_id)
    return [
        [btn("Vol +50", cb=f"ADMIN VolSet:up|{chat_id}"), btn("Vol -25", cb=f"ADMIN VolSet:down|{chat_id}")],
        [btn(f"Boost +500 · {volume}%", cb=f"ADMIN VolSet:boost|{chat_id}")],
        [btn("Reset · Normal EQ · 50%", cb=f"ADMIN AudioReset|{chat_id}")],
        [btn("Back to EQ", cb=f"ADMIN VolBack|{chat_id}")],
        [btn("Close", cb="close")],
    ]
