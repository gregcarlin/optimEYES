from typing import AbstractSet

from datetime import date
from structs.resident import Resident
from availability import AvailabilityBuilder
from dateutil import Weekday
from optimization.call_problem import CallProblemBuilder

START_DATE = date.fromisoformat("2025-12-29")
END_DATE = date.fromisoformat("2026-06-30")
NUM_DAYS = (END_DATE - START_DATE).days + 1

BUDDY_START = date.fromisoformat("2026-07-01")
BUDDY_END = date.fromisoformat("2026-07-20")  # inclusive
BUDDY_PERIOD = None

# The maximum difference allowed between the PGY2 with the most call and the
# PGY3 with the least call
PGY_2_3_GAP = 4

SEED = 1761842917

# If a resident has two calls that are K days apart, increase their weariness
# score by V, where K and V are the keys and values in this map.
WEARINESS_MAP = {
    # Don't consider Q2s because we already handle them separately
    3: 10,
    4: 5,
    5: 3,
    6: 2,
    7: 1,
}

RESIDENTS = {
    "Andrew": 2,
    "Andrieh": 2,
    "Jess": 2,
    "Loubna": 2,
    "Paris": 3,
    "Alex": 3,
    "Sophia": 3,
    "Keir": 3,
}


def get_availability() -> AvailabilityBuilder:
    input = AvailabilityBuilder(START_DATE, RESIDENTS, NUM_DAYS)

    # Weekday call

    # Block 1
    input.assign_to_day_of_week("Andrew", Weekday.MONDAY, "2025-12-29", "2026-02-15")
    input.assign_to_day_of_week("Jess", Weekday.TUESDAY, "2025-12-29", "2026-02-15")
    input.assign_to_day_of_week(
        "Andrieh", Weekday.WEDNESDAY, "2025-12-29", "2026-01-16"
    )
    input.set_consults("Loubna", "2025-12-29", "2025-12-30")
    input.set_consults("Loubna", "2026-01-05", "2026-01-16")
    input.assign_to_day_of_week("Loubna", Weekday.WEDNESDAY, "2026-01-19", "2026-02-06")
    input.set_consults("Andrieh", "2026-01-20", "2026-02-06")
    # Note: extra week in this block, swapping back again
    input.assign_to_day_of_week(
        "Andrieh", Weekday.WEDNESDAY, "2026-02-09", "2026-02-15"
    )
    input.set_consults("Loubna", "2026-02-08", "2026-02-13")
    input.assign_to_day_of_week(
        ["Alex", "Keir"], Weekday.THURSDAY, "2025-12-29", "2026-02-15"
    )
    input.assign_to_day_of_week(
        ["Paris", "Sophia"], Weekday.FRIDAY, "2025-12-29", "2026-02-15"
    )
    input.set_va(
        ["Andrew", "Paris"],
        "2025-12-29",
        "2026-02-15",
        omit=["2026-01-17", "2026-01-18", "2026-01-19"],
    )

    # Block 2
    input.assign_to_day_of_week("Loubna", Weekday.MONDAY, "2026-02-16", "2026-03-29")
    input.assign_to_day_of_week("Andrieh", Weekday.TUESDAY, "2026-02-16", "2026-03-29")
    input.assign_to_day_of_week("Andrew", Weekday.WEDNESDAY, "2026-02-16", "2026-03-09")
    input.set_consults("Jess", "2026-02-15", "2026-03-06")
    input.assign_to_day_of_week("Jess", Weekday.WEDNESDAY, "2026-03-10", "2026-03-29")
    input.set_consults("Andrew", "2026-03-08", "2026-03-27")
    input.assign_to_day_of_week(
        ["Paris", "Sophia"], Weekday.THURSDAY, "2026-02-16", "2026-03-29"
    )
    input.assign_to_day_of_week(
        ["Keir", "Alex"], Weekday.FRIDAY, "2026-02-16", "2026-03-29"
    )
    input.set_va(["Loubna", "Keir"], "2026-02-16", "2026-03-29")

    # Block 3
    input.assign_to_day_of_week("Jess", Weekday.MONDAY, "2026-03-30", "2026-05-17")
    input.assign_to_day_of_week("Andrew", Weekday.TUESDAY, "2026-03-30", "2026-05-17")
    input.assign_to_day_of_week("Loubna", Weekday.WEDNESDAY, "2026-03-30", "2026-04-20")
    input.set_consults("Andrieh", "2026-03-29", "2026-04-14")
    input.set_consults("Andrieh", "2026-04-16", "2026-04-17")
    input.assign_to_day_of_week(
        "Andrieh", Weekday.WEDNESDAY, "2026-04-21", "2026-05-11"
    )
    input.set_consults("Loubna", "2026-04-20", "2026-05-08")
    # Note: extra week in this block, swapping back again
    input.assign_to_day_of_week("Loubna", Weekday.WEDNESDAY, "2026-05-12", "2026-05-17")
    input.set_consults("Andrieh", "2026-05-10", "2026-05-15")
    input.assign_to_day_of_week(
        ["Keir", "Alex"], Weekday.THURSDAY, "2026-03-30", "2026-05-17"
    )
    input.assign_to_day_of_week(
        ["Sophia", "Paris"], Weekday.FRIDAY, "2026-03-30", "2026-05-17"
    )
    input.set_va(["Jess", "Sophia"], "2026-03-30", "2026-05-17")

    # Block 4
    input.assign_to_day_of_week("Andrieh", Weekday.MONDAY, "2026-05-18", "2026-06-30")
    input.assign_to_day_of_week("Loubna", Weekday.TUESDAY, "2026-05-18", "2026-06-30")
    input.assign_to_day_of_week("Jess", Weekday.WEDNESDAY, "2026-05-18", "2026-06-08")
    input.set_consults("Andrew", "2026-05-17", "2026-05-21")
    input.set_consults("Andrew", "2026-05-26", "2026-06-05")
    input.assign_to_day_of_week("Andrew", Weekday.WEDNESDAY, "2026-06-09", "2026-06-30")
    input.set_consults("Jess", "2026-06-07", "2026-06-26")
    # Note: extra 2 days at end of this block, swapping back again
    input.set_consults("Andrew", "2026-06-28", "2026-06-30")
    input.assign_to_day_of_week(
        # Note: Paris and Sophia are inverted to resolve conflicts with vacations
        ["Paris", "Sophia"],
        Weekday.THURSDAY,
        "2026-05-18",
        "2026-06-30",
    )
    input.assign_to_day_of_week(
        ["Alex", "Keir"], Weekday.FRIDAY, "2026-05-18", "2026-06-30"
    )
    input.set_va(["Andrieh", "Alex"], "2026-05-17", "2026-06-30")

    # Vacations
    input.set_vacation("Paris", "2026-03-27", "2026-04-05")
    input.set_vacation("Paris", "2026-05-22", "2026-05-31")
    input.set_vacation("Keir", "2026-01-09", "2026-01-18")
    input.set_vacation("Keir", "2026-04-17", "2026-04-26")
    input.set_vacation("Sophia", "2026-01-23", "2026-02-01")
    input.set_vacation("Sophia", "2026-05-15", "2026-05-24")
    input.set_vacation("Alex", "2026-04-17", "2026-04-26")
    input.set_vacation("Andrew", "2025-12-26", "2026-01-04")
    input.set_vacation("Andrew", "2026-04-03", "2026-04-12")
    input.set_vacation("Jess", "2026-01-09", "2026-01-18")
    input.set_vacation("Jess", "2026-05-01", "2026-05-11")
    input.set_vacation("Loubna", "2026-03-13", "2026-03-22")
    input.set_vacation("Loubna", "2026-05-22", "2026-05-31")
    input.set_vacation("Andrieh", "2026-02-13", "2026-02-22")
    input.set_vacation("Andrieh", "2026-05-15", "2026-05-24")

    # Conferences
    for resident in ["Paris", "Keir", "Sophia", "Alex"]:
        input.set_conference(resident, "2026-04-14", "2026-04-19")

    # Floating holidays
    input.set_holiday("Andrew", "2026-02-05", "2026-02-08")
    input.set_holiday("Jess", "2026-04-09", "2026-04-12")
    input.set_holiday("Jess", "2026-05-08", "2026-05-11")

    # Weekends
    input.set_weekend("Jess", "2026-04-10", "2026-04-12")
    input.set_weekend("Jess", "2026-03-13", "2026-03-15")
    input.set_weekend("Jess", "2026-02-13", "2026-02-15")
    input.set_weekend(
        "Jess", "2026-02-27", "2026-03-01"
    )  # is this a 'weekend in March?'
    input.set_weekend("Jess", "2026-03-06", "2026-03-08")
    input.set_weekend("Jess", "2026-03-20", "2026-03-22")
    input.set_weekend("Jess", "2026-03-27", "2026-03-29")
    input.set_weekend("Andrew", "2026-02-05", "2026-02-08")
    input.set_weekend("Andrew", "2026-06-26", "2026-06-28")
    # Not possible to take off this weekend, working holiday
    # input.set_weekend("Andrew", "2026-05-22", "2026-05-24")
    input.set_weekend("Andrieh", "2026-01-22", "2026-01-25")
    input.set_weekend("Andrieh", "2026-05-15", "2026-05-17")
    input.set_weekend("Andrieh", "2026-04-10", "2026-04-12")
    input.set_weekend("Andrieh", "2026-02-13", "2026-02-15")
    input.set_weekend("Sophia", "2026-01-23", "2026-01-25")
    input.set_weekend("Sophia", "2026-05-15", "2026-05-17")
    input.set_weekend("Sophia", "2026-02-20", "2026-02-22")
    input.set_weekend("Sophia", "2026-05-01", "2026-05-03")
    input.set_weekend("Sophia", "2026-02-13", "2026-02-15")
    input.set_weekend("Loubna", "2026-01-30", "2026-02-01")
    input.set_weekend("Loubna", "2026-02-20", "2026-02-22")
    input.set_weekend("Loubna", "2026-02-27", "2026-03-01")
    input.set_weekend("Loubna", "2026-03-06", "2026-03-08")
    input.set_weekend("Loubna", "2026-03-13", "2026-03-15")
    input.set_weekend("Loubna", "2026-05-29", "2026-06-01")
    input.set_weekend("Loubna", "2026-04-15", "2026-04-18")
    input.set_weekend("Keir", "2026-01-09", "2026-01-11")
    input.set_weekend("Keir", "2026-04-17", "2026-04-19")
    input.set_weekend("Keir", "2026-04-03", "2026-04-05")
    input.set_weekend("Keir", "2026-05-08", "2026-05-10")
    input.set_weekend("Keir", "2026-05-29", "2026-06-01")
    input.set_weekend("Keir", "2026-02-13", "2026-02-15")
    input.set_weekend("Keir", "2026-02-20", "2026-02-22")
    input.set_weekend("Paris", "2026-03-27", "2026-03-29")
    input.set_weekend("Paris", "2026-05-22", "2026-05-24")
    input.set_weekend("Alex", "2026-06-19", "2026-06-21")
    input.set_weekend("Alex", "2026-02-20", "2026-02-22")

    input.open_for_coverage(
        "2026-02-19", "so she can cover next day"
    )  # would otherwise be Paris

    # Holidays
    input.open_for_coverage("2025-12-30", "working next day")  # would otherwise be Jess
    input.set_unavailable("Paris", "Start", "2025-12-29", "2025-12-30")
    input.set_unavailable("Andrieh", "Start", "2025-12-29", "2025-12-30")
    input.set_unavailable("Loubna", "Start", "2025-12-29", "2025-12-30")
    input.set_unavailable("Jess", "Start", "2025-12-29", "2025-12-30")
    input.assign_to_day("Jess", "2025-12-31")
    input.assign_to_day("Loubna", "2026-01-01")
    input.assign_to_day("Jess", "2026-01-02")
    input.assign_to_day("Loubna", "2026-01-03")
    input.assign_to_day("Jess", "2026-01-04")
    input.open_for_coverage("2026-01-06", "avoiding Q2")  # would otherwise be Jess
    input.assign_to_day("Sophia", "2026-01-16")
    input.assign_to_day("Andrieh", "2026-01-17")
    input.assign_to_day("Sophia", "2026-01-18")
    input.assign_to_day("Andrieh", "2026-01-19")
    input.assign_to_day("Andrew", "2026-05-22")
    input.assign_to_day("Alex", "2026-05-23")
    input.assign_to_day("Andrew", "2026-05-24")
    input.assign_to_day("Alex", "2026-05-25")

    # input.assign_to_day("Andrieh", "2026-04-19")

    input.open_for_coverage("2026-04-21", "avoiding Q2")  # would be Andrew
    input.open_for_coverage(
        "2026-04-22", "so he can cover previous day"
    )  # would be Andrieh
    # input.open_for_coverage("2026-04-14", "test") # would be Andrew

    return input


"""
def special_handling_for_this_round(builder: CallProblemBuilder) -> None:
    builder.limit_calls_for_year(2, 25)
    builder.limit_calls_for_year(3, 21)
    builder.limit_weekday_for_all(Weekday.SATURDAY, 4)
    builder.limit_weekday_for_all(Weekday.SUNDAY, 4)
"""
