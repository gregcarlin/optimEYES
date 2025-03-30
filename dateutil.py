from datetime import date, timedelta
from enum import IntEnum


# Follows ISO something
class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


# The number of days between the start date and the next given day of the week
def days_until_next_weekday(start: date, weekday: Weekday) -> int:
    return (7 + weekday - start.weekday()) % 7


# The number of days between the given start date and the previous given day of the week
def days_after_last_weekday(start: date, weekday: Weekday) -> int:
    return (start.weekday() + 7 - weekday - 1) % 7


def num_weekdays_in_time_period(start: date, num_days: int, weekday: Weekday) -> int:
    # The number of days before the first instance of the given weekday
    days_before_first = days_until_next_weekday(start, weekday) % 7
    # The number of days after the last instance of the given weekday
    days_after_last = days_after_last_weekday(start + timedelta(days=num_days), weekday)
    num_days = num_days - days_before_first - days_after_last
    # num_days is the number of days between the first day of the given
    # day-of-week and the last, inclusive of both days of that week at either
    # end.
    assert num_days % 7 == 1
    return int((num_days - 1) / 7) + 1
