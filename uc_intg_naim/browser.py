"""
Media browser for Naim integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import StatusCodes
from ucapi.media_player import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
)
from ucapi.api_definitions import Pagination

from uc_intg_naim.const import (
    BROWSABLE_SOURCES,
    DEFAULT_SOURCE_NAMES,
    UNSELECTABLE_SOURCES,
)

if TYPE_CHECKING:
    from uc_intg_naim.config import NaimConfig
    from uc_intg_naim.device import NaimDevice

_LOG = logging.getLogger(__name__)

PAGE_SIZE = 50


async def browse(
    device: NaimDevice, config: NaimConfig, options: BrowseOptions
) -> BrowseResults | StatusCodes:
    media_type = options.media_type or "root"
    media_id = options.media_id or ""

    if media_type == "root" or (options.media_id is None and options.media_type is None):
        return _browse_root(device, config)

    if media_type == "favourites":
        return _browse_favourites(config, _page(options))

    if media_type == "sources":
        return _browse_sources(device, config)

    if media_type == "node":
        return await _browse_node(device, media_id, _page(options))

    return StatusCodes.NOT_FOUND


def _page(options: BrowseOptions) -> int:
    paging = options.paging
    return int((paging.page if paging and paging.page else None) or 1)


def _truthy(val: Any) -> bool:
    return val in (True, 1, "1", "true", "True")


def _int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _display_name(device: NaimDevice, src: str) -> str:
    names = device.source_names or {}
    return names.get(src) or DEFAULT_SOURCE_NAMES.get(src, src)


def _browse_root(device: NaimDevice, config: NaimConfig) -> BrowseResults:
    items = [
        BrowseMediaItem(
            title="Favourites",
            media_class=MediaClass.DIRECTORY,
            media_type="favourites",
            media_id="favourites",
            can_browse=True,
            can_play=False,
        ),
        BrowseMediaItem(
            title="Sources",
            media_class=MediaClass.DIRECTORY,
            media_type="sources",
            media_id="sources",
            can_browse=True,
            can_play=False,
        ),
    ]

    for src in config.sources:
        if src in BROWSABLE_SOURCES:
            items.append(BrowseMediaItem(
                title=_display_name(device, src),
                media_class=MediaClass.DIRECTORY,
                media_type="node",
                media_id=f"inputs/{src}",
                can_browse=True,
                can_play=False,
            ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Naim Audio",
            media_class=MediaClass.DIRECTORY,
            media_type="root",
            media_id="root",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


def _browse_favourites(config: NaimConfig, page: int) -> BrowseResults:
    all_favs = config.favourites or []
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_favs = all_favs[start:end]

    items = []
    for i, fav in enumerate(page_favs, start + 1):
        name = fav.get("name", f"Favourite {i}")
        ussi = fav.get("ussi", "")
        fav_id = ussi.split("/", 1)[1] if "/" in ussi else ussi

        items.append(BrowseMediaItem(
            title=name,
            media_class=MediaClass.TRACK,
            media_type="favourite",
            media_id=fav_id,
            can_play=True,
            can_browse=False,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Favourites",
            media_class=MediaClass.DIRECTORY,
            media_type="favourites",
            media_id="favourites",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=PAGE_SIZE, count=len(all_favs)),
    )


def _browse_sources(device: NaimDevice, config: NaimConfig) -> BrowseResults:
    items = []
    for src in config.sources:
        if src in UNSELECTABLE_SOURCES:
            continue
        items.append(BrowseMediaItem(
            title=_display_name(device, src),
            media_class=MediaClass.CHANNEL,
            media_type="source",
            media_id=src,
            can_play=True,
            can_browse=False,
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Sources",
            media_class=MediaClass.DIRECTORY,
            media_type="sources",
            media_id="sources",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _browse_node(
    device: NaimDevice, ussi: str, page: int
) -> BrowseResults | StatusCodes:
    if not ussi:
        return StatusCodes.NOT_FOUND

    offset = (page - 1) * PAGE_SIZE
    data = await device.browse_ussi(ussi, offset, PAGE_SIZE)

    title = ussi.split("/")[-1]
    if not data:
        return _empty_node(ussi, title)

    children = data.get("children") or []
    items = []
    for child in children:
        child_ussi = child.get("ussi") or child.get("mediaUssi") or ""
        if not child_ussi:
            continue
        name = child.get("name") or child.get("title") or child_ussi.split("/")[-1]
        browsable = _truthy(child.get("browsable"))
        playable = _truthy(child.get("playable"))
        if not browsable and not playable:
            playable = True

        items.append(BrowseMediaItem(
            title=name,
            media_class=MediaClass.DIRECTORY if browsable else MediaClass.TRACK,
            media_type="node" if browsable else "play_ussi",
            media_id=child_ussi,
            can_browse=browsable,
            can_play=playable,
        ))

    total = _int(data.get("totalCount"), len(children) + offset)

    return BrowseResults(
        media=BrowseMediaItem(
            title=data.get("name") or title,
            media_class=MediaClass.DIRECTORY,
            media_type="node",
            media_id=ussi,
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=PAGE_SIZE, count=total),
    )


def _empty_node(ussi: str, title: str) -> BrowseResults:
    return BrowseResults(
        media=BrowseMediaItem(
            title=title,
            media_class=MediaClass.DIRECTORY,
            media_type="node",
            media_id=ussi,
            can_browse=True,
            items=[],
        ),
        pagination=Pagination(page=1, limit=0, count=0),
    )
