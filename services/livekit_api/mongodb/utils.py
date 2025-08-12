from typing import Any, Optional
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


def now_ist_iso() -> str:
    return datetime.now(IST).isoformat()


def parse_bound_date_only(s: Optional[str], *, as_end: bool = False) -> Optional[datetime]:
    if not s:
        return None
    try:
        if not (len(s) == 10 and s[4] == "-" and s[7] == "-"):
            raise ValueError("Invalid date format")
        from datetime import datetime as _dt
        dt = _dt.strptime(s, "%Y-%m-%d")
        if as_end:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return IST.localize(dt)
    except Exception:
        raise ValueError("Invalid date. Use YYYY-MM-DD (IST)")


def parse_any_dt_to_ist(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, datetime):
            dt = v
        elif isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        else:
            return None
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt).astimezone(IST)
        else:
            dt = dt.astimezone(IST)
        return dt
    except Exception:
        return None
