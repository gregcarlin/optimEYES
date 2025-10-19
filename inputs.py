from typing import AbstractSet

from datetime import date
from call_problem import Resident
from availability import AvailabilityBuilder
from dateutil import Weekday

START_DATE = date.fromisoformat("2025-12-29")
END_DATE = date.fromisoformat("2026-06-30")
NUM_DAYS = (END_DATE - START_DATE).days + 1

BUDDY_START = date.fromisoformat("2026-07-01")
BUDDY_END = date.fromisoformat("2026-07-20")  # inclusive
BUDDY_PERIOD = None

RESIDENTS = {
    Resident(
        name="Andrew",
        pgy=2,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Andrieh",
        pgy=2,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Jess",
        pgy=2,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Loubna",
        pgy=2,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Paris",
        pgy=3,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Alex",
        pgy=3,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Sophia",
        pgy=3,
        num_days=NUM_DAYS,
    ),
    Resident(
        name="Keir",
        pgy=3,
        num_days=NUM_DAYS,
    ),
}


def get_availability() -> AbstractSet[Resident]:
    input = AvailabilityBuilder(START_DATE, RESIDENTS)

    input.assign_to_day_of_week("Andrew", Weekday.MONDAY, "2025-12-29", "2026-02-15")
    input.assign_to_day_of_week(
        ["Alex", "Keir"], Weekday.THURSDAY, "2025-12-29", "2026-02-15"
    )
    input.assign_to_day_of_week(
        ["Paris", "Sophia"], Weekday.FRIDAY, "2025-12-29", "2026-02-15"
    )

    input.assign_to_day_of_week("Loubna", Weekday.MONDAY, "2026-02-16", "2026-03-29")
    input.assign_to_day_of_week(
        ["Paris", "Sophia"], Weekday.THURSDAY, "2026-02-16", "2026-03-29"
    )
    input.assign_to_day_of_week(
        ["Keir", "Alex"], Weekday.FRIDAY, "2026-02-16", "2026-03-29"
    )

    input.assign_to_day_of_week("Jess", Weekday.MONDAY, "2026-03-30", "2026-05-17")
    input.assign_to_day_of_week(
        ["Keir", "Alex"], Weekday.THURSDAY, "2026-03-30", "2026-05-17"
    )
    input.assign_to_day_of_week(
        ["Sophia", "Paris"], Weekday.FRIDAY, "2026-03-30", "2026-05-17"
    )

    input.assign_to_day_of_week("Andrieh", Weekday.MONDAY, "2026-05-18", "2026-06-30")
    input.assign_to_day_of_week(
        ["Sophia", "Paris"], Weekday.THURSDAY, "2026-05-18", "2026-06-30"
    )
    input.assign_to_day_of_week(
        ["Alex", "Keir"], Weekday.FRIDAY, "2026-05-18", "2026-06-30"
    )

    return input.build()
