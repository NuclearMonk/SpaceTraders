from datetime import datetime, timedelta, UTC
from json import dumps


def print_json(json_dict):
    print(dumps(json_dict, indent=2))


def clamp(n, m, M):
    if n < m:
        return m
    elif n > M:
        return M
    else:
        return n


def clamped_inverse_lerp[T](A: T, B: T, V: T) -> float:
    return clamp((V-A) / (B-A), 0, 100)


def iso_8601(time: str) -> datetime:
    return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")


def error_wrap(msg: str) -> str:
    return f"[red]{msg}[/red]"


def success_wrap(msg: str) -> str:
    return f"[green]{msg}[/green]"


def format_time_ms(time: datetime) -> str:
    return datetime.strftime(time, "%Y-%m-%d %H:%M:%S.%f")[:-3]


def time_until(t: datetime) -> timedelta:
    return max(t - datetime.now(UTC), timedelta(0))
