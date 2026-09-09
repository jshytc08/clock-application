"""Read-only time API with bounded, deterministic catalog queries."""

from datetime import datetime
from datetime import timezone as datetime_timezone
from typing import Annotated

import pytz
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

router = APIRouter()
ZONES = tuple(sorted(pytz.common_timezones))
REGIONS = tuple(sorted({zone.split("/")[0] if "/" in zone else "Other" for zone in ZONES}))


class TimezonePage(BaseModel):
    zones: list[str]
    regions: list[str]
    total: int
    page: int
    page_size: int
    pages: int


@router.get("/timezones", response_model=TimezonePage)
async def get_all_timezones(
    response: Response,
    q: Annotated[str, Query(max_length=80)] = "",
    region: Annotated[str, Query(max_length=32)] = "",
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    page_size: Annotated[int, Query(ge=12, le=48)] = 12,
):
    if page_size not in (12, 24, 48):
        raise HTTPException(status_code=422, detail="Page size must be 12, 24, or 48.")
    if region and region not in REGIONS:
        raise HTTPException(status_code=422, detail="Choose a supported region.")
    query = " ".join(q.replace("_", " ").casefold().split())
    matches = [
        zone
        for zone in ZONES
        if query in zone.replace("_", " ").casefold()
        and (not region or (zone.split("/")[0] if "/" in zone else "Other") == region)
    ]
    pages = max(1, (len(matches) + page_size - 1) // page_size)
    if page > pages:
        raise HTTPException(status_code=404, detail="This page does not exist.")
    start = (page - 1) * page_size
    response.headers["Cache-Control"] = "public, max-age=300"
    return TimezonePage(
        zones=matches[start : start + page_size],
        regions=list(REGIONS),
        total=len(matches),
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/time")
async def get_server_time(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"epoch_ms": int(datetime.now(datetime_timezone.utc).timestamp() * 1000)}


@router.get("/world-clock/{timezone:path}")
async def get_time(timezone: str, response: Response):
    if len(timezone) > 128 or timezone not in pytz.all_timezones_set:
        raise HTTPException(status_code=404, detail="Unknown timezone.")
    current = datetime.now(pytz.timezone(timezone))
    response.headers["Cache-Control"] = "no-store"
    return {
        "timezone": timezone,
        "time": current.strftime("%H:%M:%S"),
        "date": current.date().isoformat(),
        "iso": current.isoformat(),
    }
