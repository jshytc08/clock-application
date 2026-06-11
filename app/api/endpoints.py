import pytz
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

# New endpoint to get the list of ALL timezones
@router.get("/timezones")
async def get_all_timezones():
    # pytz.all_timezones contains every timezone string (e.g., 'Africa/Abidjan', 'America/New_York', etc.)
    return {"zones": pytz.all_timezones}

@router.get("/world-clock/{timezone:path}")
async def get_time(timezone: str):
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz).strftime("%H:%M:%S")
        return {"timezone": timezone, "time": current_time}
    except Exception as e:
        return {"error": str(e)}