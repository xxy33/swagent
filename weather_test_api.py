from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  
import requests
def get_weather(lat: float, lon: float, when: datetime | str | None = None, tz: str = "Asia/Shanghai"):
    base = "https://api.open-meteo.com/v1/forecast"

    # 未指定时间：取 current
    if when is None:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": tz  # 用明确时区
        }
        j = requests.get(base, params=params, timeout=10).json()
        return {"mode": "current", "data": j.get("current", {})}

    # 规范化 when
    if isinstance(when, str):
        when = when.replace(" ", "T")
        dt = datetime.fromisoformat(when)  # 若不带偏移，则是 naive
    else:
        dt = when

    # 将时间转换到指定时区，并取整点
    tzinfo = ZoneInfo(tz)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzinfo)
    else:
        dt = dt.astimezone(tzinfo)

    dt_hour = dt.replace(minute=0, second=0, microsecond=0)
    dt_next = dt_hour + timedelta(hours=1)

    # 构造本地时区的 start/end（不带偏移）
    start_iso = dt_hour.strftime("%Y-%m-%dT%H:%M")
    end_iso   = dt_next.strftime("%Y-%m-%dT%H:%M")

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": tz,            # 用明确时区，不用 auto
        "start": start_iso,        # 本地时区的小时
        "end": end_iso,
        "timeformat": "iso8601"
    }

    j = requests.get(base, params=params, timeout=10).json()
    hourly = j.get("hourly", {})
    times = hourly.get("time", [])

    # 按 start_iso 精确匹配（返回 times 是该时区）
    idx = None
    for i, t in enumerate(times):
        if t.startswith(start_iso):
            idx = i
            break
    if idx is None and times:
        idx = 0

    if idx is None:
        return {"mode": "hourly", "data": {}, "msg": "no hourly data returned"}

    out = {"time": times[idx]}
    for k, v in hourly.items():
        if isinstance(v, list) and len(v) > idx:
            out[k] = v[idx]
    return {"mode": "hourly", "data": out}


if __name__ == "__main__":
    # 示例：未指定时间（当前）
    print(get_weather(39.9042, 116.4074))

    # 示例：指定时间（ISO8601）
    print(get_weather(39.9042, 116.4074, "2026-01-20T14:00"))

    # 示例：指定时间（datetime）
    print(get_weather(39.9042, 116.4074, datetime(2026, 1, 20, 9)))
