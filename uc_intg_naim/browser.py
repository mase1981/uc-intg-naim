"""
Media browser for Naim integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ucapi import StatusCodes
from ucapi.api_definitions import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    Pagination,
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
        return _browse_root(config)

    if media_type == "favourites":
        paging = options.paging
        page = int((paging.page if paging and paging.page else None) or 1)
        return _browse_favourites(config, page)

    if media_type == "sources":
        return _browse_sources(device, config)

    return StatusCodes.NOT_FOUND


def _browse_root(config: NaimConfig) -> BrowseResults:
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
    source_names = device.source_names or {}
    items = []
    for src in config.sources:
        display = source_names.get(src, src)
        items.append(BrowseMediaItem(
            title=display,
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
