from datetime import datetime, timedelta

def get_next_n_days(n: int) -> list[str]:
    return [(datetime.now() + timedelta(days=i)).date().isoformat() for i in range(n)]

def time_to_seconds(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 3600 + m * 60

def seconds_to_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"