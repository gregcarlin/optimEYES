import math
from typing import override, Any
from abc import ABC, abstractmethod

import pulp as pulp

from optimization.call_problem import CallProblemBuilder
from optimization.linear_problem import PulpProblem, var_sum
from dateutil import days_until_next_weekday, num_weekdays_in_time_period, Weekday


class Constraint(ABC):
    @abstractmethod
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        pass


class SerializableConstraint(Constraint):
    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def deserialize(data: dict[str, Any]) -> Constraint:
        pass

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        pass


class DistributeDayOfWeekConstraint(SerializableConstraint):
    def __init__(self, weekday: Weekday) -> None:
        self.weekday = weekday

    @staticmethod
    @override
    def get_name() -> str:
        return "distribute_weekday"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return DistributeDayOfWeekConstraint(Weekday(data["weekday"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"weekday": int(self.weekday)}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        num_weekdays = num_weekdays_in_time_period(
            builder.get_start_date(), builder.get_num_days(), self.weekday
        )
        min_weekdays_per_resident = math.floor(
            num_weekdays / float(builder.get_num_residents())
        )
        max_weekdays_per_resident = math.ceil(
            num_weekdays / float(builder.get_num_residents())
        )
        constraints: list[pulp.LpConstraint] = []
        for days_for_resident in builder.get_day_vars().values():
            day_of_week_vars: list[pulp.LpVariable] = []
            next_day = days_until_next_weekday(builder.get_start_date(), self.weekday)
            while next_day < builder.get_num_days():
                day_of_week_vars.append(days_for_resident[next_day])
                next_day += 7
            constraints.append(var_sum(day_of_week_vars) >= min_weekdays_per_resident)
            constraints.append(var_sum(day_of_week_vars) <= max_weekdays_per_resident)
        return constraints


class DistributeWeekendsConstraint(SerializableConstraint):
    @staticmethod
    @override
    def get_name() -> str:
        return "distribute_weekends"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return DistributeWeekendsConstraint()

    @override
    def serialize(self) -> dict[str, Any]:
        return {}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        num_saturdays = num_weekdays_in_time_period(
            builder.get_start_date(), builder.get_num_days(), Weekday.SATURDAY
        )
        num_sundays = num_weekdays_in_time_period(
            builder.get_start_date(), builder.get_num_days(), Weekday.SUNDAY
        )
        num_weekend_days = num_saturdays + num_sundays
        min_per_resident = math.floor(
            num_weekend_days / float(builder.get_num_residents())
        )
        max_per_resident = math.ceil(
            num_weekend_days / float(builder.get_num_residents())
        )

        first_saturday = days_until_next_weekday(
            builder.get_start_date(), Weekday.SATURDAY
        )
        first_sunday = days_until_next_weekday(builder.get_start_date(), Weekday.SUNDAY)
        assert (
            first_saturday < first_sunday
        ), "Starting on a sunday is not yet supported"

        constraints: list[pulp.LpConstraint] = []
        for days_for_resident in builder.get_day_vars().values():
            day_of_week_vars = []
            next_day = first_saturday
            while next_day < builder.get_num_days():
                day_of_week_vars.append(days_for_resident[next_day])
                if next_day + 1 < builder.get_num_days():
                    day_of_week_vars.append(days_for_resident[next_day + 1])
                next_day += 7
            constraints.append(var_sum(day_of_week_vars) >= min_per_resident)
            constraints.append(var_sum(day_of_week_vars) <= max_per_resident)
        return constraints


class LimitWeekdayConstraint(SerializableConstraint):
    def __init__(self, weekday: Weekday, limit: int) -> None:
        self.weekday = weekday
        self.limit = limit

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_weekday"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return LimitWeekdayConstraint(Weekday(data["weekday"]), int(data["limit"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"weekday": int(self.weekday), "limit": self.limit}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []
        for days_for_resident in builder.get_day_vars().values():
            day = days_until_next_weekday(builder.get_start_date(), self.weekday)
            day_vars = []
            while day < builder.get_num_days():
                day_vars.append(days_for_resident[day])
                day += 7
            constraints.append(var_sum(day_vars) <= self.limit)
        return constraints


class LimitWeekdayForResidentConstraint(SerializableConstraint):
    def __init__(self, weekday: Weekday, limit: int, resident: str) -> None:
        self.weekday = weekday
        self.limit = limit
        self.resident = resident

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_weekday_for_resident"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return LimitWeekdayForResidentConstraint(
            Weekday(data["weekday"]), int(data["limit"]), str(data["resident"])
        )

    @override
    def serialize(self) -> dict[str, Any]:
        return {
            "weekday": int(self.weekday),
            "limit": self.limit,
            "resident": self.resident,
        }

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        day_vars = builder.get_vars_for_weekday(self.resident, self.weekday)
        return [var_sum(day_vars) <= self.limit]


class SetMinimumForDaysOfWeekForResidentConstraint(SerializableConstraint):
    def __init__(self, weekdays: list[Weekday], minimum: int, resident: str) -> None:
        self.weekdays = weekdays
        self.minimum = minimum
        self.resident = resident

    @staticmethod
    @override
    def get_name() -> str:
        return "minimum_for_days_of_week_for_resident"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        weekdays = [Weekday(w) for w in data["weekdays"].split(",")]
        return SetMinimumForDaysOfWeekForResidentConstraint(
            weekdays, int(data["minimum"]), str(data["resident"])
        )

    @override
    def serialize(self) -> dict[str, Any]:
        weekdays = ",".join([str(w) for w in self.weekdays])
        return {
            "weekdays": weekdays,
            "minimum": self.minimum,
            "resident": self.resident,
        }

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        day_varss = [
            builder.get_vars_for_weekday(self.resident, weekday)
            for weekday in self.weekdays
        ]
        day_vars = [dv for sublist in day_varss for dv in sublist]
        return [var_sum(day_vars) >= self.minimum]


class NoAdjacentWeekendsConstraint(SerializableConstraint):
    """
    Ensure no resident works two weekends in a row.
    """

    @staticmethod
    @override
    def get_name() -> str:
        return "no_adjacent_weekends"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return NoAdjacentWeekendsConstraint()

    @override
    def serialize(self) -> dict[str, Any]:
        return {}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []
        for days_for_resident in builder.get_day_vars().values():
            first_saturday = days_until_next_weekday(
                builder.get_start_date(), Weekday.SATURDAY
            )
            first_sunday = days_until_next_weekday(
                builder.get_start_date(), Weekday.SUNDAY
            )
            assert (
                first_saturday < first_sunday
            ), "Starting on a sunday is not yet supported"
            if first_saturday + 1 >= builder.get_num_days():
                # No full weekends in call period
                return []

            last_saturday = days_for_resident[first_saturday]
            last_sunday = days_for_resident[first_saturday + 1]
            next_saturday = first_saturday + 7
            while next_saturday < builder.get_num_days():
                curr_saturday = days_for_resident[next_saturday]
                if next_saturday + 1 < builder.get_num_days():
                    curr_sunday = days_for_resident[next_saturday + 1]
                    constraints.append(
                        last_saturday + last_sunday + curr_saturday + curr_sunday <= 1
                    )

                    last_saturday = curr_saturday
                    last_sunday = curr_sunday
                else:
                    constraints.append(last_saturday + last_sunday + curr_saturday <= 1)
                    break  # should be redundant, but just in case
                next_saturday += 7

        return constraints


class LimitForPGYConstraint(SerializableConstraint):
    """
    Limit the number of calls for residents in a given year.
    """

    def __init__(self, pgy: int, limit: int) -> None:
        self.pgy = pgy
        self.limit = limit

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_for_pgy"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return LimitForPGYConstraint(int(data["pgy"]), int(data["limit"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"pgy": self.pgy, "limit": self.limit}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []
        for resident, days_for_resident in builder.get_day_vars().items():
            if builder.get_residents()[resident].pgy != self.pgy:
                continue
            constraints.append(var_sum(days_for_resident) <= self.limit)
        return constraints


class LimitVACoverageConstraint(SerializableConstraint):
    def __init__(self, limit: int) -> None:
        self.limit = limit

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_va_coverage"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return LimitVACoverageConstraint(int(data["limit"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        return [var_sum(builder.get_va_vars()) <= self.limit]


class DistributeQ2sConstraint(SerializableConstraint):
    def __init__(self, tolerance: int) -> None:
        self.tolerance = tolerance

    @staticmethod
    @override
    def get_name() -> str:
        return "distribute_q2s"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return DistributeQ2sConstraint(int(data["tolerance"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"tolerance": self.tolerance}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        q2s_dict = builder.get_qn_vars(2)
        q2s_per_resident = [var_sum(q2_vars) for q2_vars in q2s_dict.values()]
        max_q2s = builder.get_problem().max_of(
            q2s_per_resident, builder.get_num_days(), "max_q2s"
        )
        min_q2s = builder.get_problem().min_of(
            q2s_per_resident, builder.get_num_days(), "min_q2s"
        )
        return [max_q2s - min_q2s <= self.tolerance]


class LimitQ2sConstraint(SerializableConstraint):
    def __init__(self, limit: int) -> None:
        self.limit = limit

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_q2s"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return LimitQ2sConstraint(int(data["limit"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []
        q2s_dict = builder.get_qn_vars(2)
        for q2_vars in q2s_dict.values():
            constraints.append(var_sum(q2_vars) <= self.limit)
        return constraints


class LimitTotalQ2sConstraint(SerializableConstraint):
    def __init__(self, limit: int) -> None:
        self.limit = limit

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_total_q2s"

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        return LimitTotalQ2sConstraint(int(data["limit"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit}

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        q2s_dict = builder.get_qn_vars(2)
        q2s = [v for vs in q2s_dict.values() for v in vs]
        return [var_sum(q2s) <= self.limit]


class ConstraintRegistry:
    def __init__(self) -> None:
        self.constraints = {
            c.get_name(): c
            for c in [
                DistributeDayOfWeekConstraint,
                DistributeWeekendsConstraint,
                LimitWeekdayConstraint,
                LimitWeekdayForResidentConstraint,
                SetMinimumForDaysOfWeekForResidentConstraint,
                NoAdjacentWeekendsConstraint,
                LimitForPGYConstraint,
                LimitVACoverageConstraint,
                DistributeQ2sConstraint,
                LimitQ2sConstraint,
                LimitTotalQ2sConstraint,
            ]
        }

    def deserialize(self, name: str, data: dict[str, Any]) -> SerializableConstraint:
        return self.constraints[name].deserialize(data)
