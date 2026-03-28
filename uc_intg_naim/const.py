"""
Constants for Naim integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

POLL_INTERVAL = 5
WATCHDOG_INTERVAL = 30
RECONNECT_DELAY = 10
CONNECT_TIMEOUT = 10
CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 5

DEFAULT_PORT = 15081

SOURCE_MAP = {
    "SOURCE_ANA1": "ana1",
    "SOURCE_ANA2": "ana2",
    "SOURCE_ANA3": "ana3",
    "SOURCE_ANA4": "ana4",
    "SOURCE_DIG1": "dig1",
    "SOURCE_DIG2": "dig2",
    "SOURCE_DIG3": "dig3",
    "SOURCE_DIG4": "dig4",
    "SOURCE_DIG5": "dig5",
    "SOURCE_HDMI": "hdmi",
    "SOURCE_BLUETOOTH": "bluetooth",
    "SOURCE_RADIO": "radio",
    "SOURCE_SPOTIFY": "spotify",
    "SOURCE_TIDAL": "tidal",
    "SOURCE_QOBUZ": "qobuz",
    "SOURCE_USB": "usb",
    "SOURCE_AIRPLAY": "airplay",
    "SOURCE_GCAST": "gcast",
    "SOURCE_UPNP": "upnp",
    "SOURCE_PLAYQUEUE": "playqueue",
    "SOURCE_FILES": "files",
}

DEFAULT_SOURCE_NAMES = {
    "ana1": "Analogue 1",
    "ana2": "Analogue 2",
    "ana3": "Analogue 3",
    "ana4": "Analogue 4",
    "dig1": "Digital 1",
    "dig2": "Digital 2",
    "dig3": "Digital 3",
    "dig4": "Digital 4",
    "dig5": "Digital 5",
    "hdmi": "HDMI",
    "bluetooth": "Bluetooth",
    "radio": "Internet Radio",
    "spotify": "Spotify",
    "tidal": "TIDAL",
    "qobuz": "Qobuz",
    "usb": "USB",
    "airplay": "AirPlay",
    "gcast": "Chromecast",
    "upnp": "UPnP/Servers",
    "playqueue": "Play Queue",
    "files": "Local Files",
    "multiroom": "Multi-room",
}
