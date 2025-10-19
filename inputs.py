from typing import AbstractSet

from datetime import date
from call_problem import Resident
from availability import AvailabilityBuilder
from dateutil import Weekday

START_DATE = date.fromisoformat("2026-01-01")
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


def get_availability() -> AvailabilityBuilder:
    input = AvailabilityBuilder(START_DATE, RESIDENTS)

    # Weekday call
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

    # Vacations
    input.set_unavailable("Paris", "2026-03-28", "2026-04-05")
    input.set_unavailable("Paris", "2026-05-23", "2026-05-31")
    input.set_unavailable("Keir", "2026-01-10", "2026-01-18")
    input.set_unavailable("Keir", "2026-04-18", "2026-04-26")
    input.set_unavailable("Sophia", "2026-01-24", "2026-02-01")
    input.set_unavailable("Sophia", "2026-05-16", "2026-05-24")
    input.set_unavailable("Alex", "2026-04-18", "2026-04-26")
    input.set_unavailable("Andrew", "2025-12-27", "2026-01-04")
    input.set_unavailable("Andrew", "2026-04-04", "2026-04-12")
    input.set_unavailable("Jess", "2026-01-10", "2026-01-18")
    input.set_unavailable("Jess", "2026-05-02", "2026-05-11")
    input.set_unavailable("Loubna", "2026-03-14", "2026-03-22")
    input.set_unavailable("Loubna", "2026-05-23", "2026-05-31")
    input.set_unavailable("Andrieh", "2026-02-14", "2026-02-22")
    input.set_unavailable("Andrieh", "2026-05-16", "2026-05-24")

    # Conferences
    for resident in ["Paris", "Keir", "Sophia", "Alex"]:
        input.set_unavailable(resident, "2026-04-15", "2026-04-18")

    # Floating holidays
    input.set_unavailable("Andrew", "2026-02-06", "2026-02-08")
    input.set_unavailable("Jess", "2026-04-10", "2026-04-12")
    input.set_unavailable("Jess", "2026-05-09", "2026-05-11")

    return input
