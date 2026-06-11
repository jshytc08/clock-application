from fastapi import APIRouter
from datetime import datetime
import pytz

router = APIRouter()

@router.get("/world-clock/{timezone}")
async def get_time(timezone: str):
    try:
        # Validate timezone input
        tz = pytz.timezone(timezone.replace("-", "/"))
        current_time = datetime.now(tz).strftime("%H:%M:%S")
        return {"timezone": timezone, "time": current_time}
    except Exception:
        return {"error": "Invalid timezone"}