import math
from typing import override, Any, Generic, TypeVar
from abc import ABC, abstractmethod

import pulp as pulp

from optimization.call_problem import CallProblemBuilder
from optimization.linear_problem import var_sum
from structs.field import (
    Field,
    WeekdayField,
    WeekdayListField,
    IntField,
    StringField,
    LimitedStringField,
    MultiCheckField,
)
from structs.project_info import ProjectInfo
from dateutil import days_until_next_weekday, num_weekdays_in_time_period, Weekday


class Constraint(ABC):
    enabled: bool = True

    @abstractmethod
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        pass


TFields = TypeVar("TFields", bound="tuple[Field, ...]")


class SerializableConstraint(Constraint, Generic[TFields]):
    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def human_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def default(project: ProjectInfo) -> Constraint:
        pass

    @staticmethod
    @abstractmethod
    def deserialize(data: dict[str, Any]) -> Constraint:
        pass

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def fields(self, project: ProjectInfo) -> TFields:
        pass

    @staticmethod
    @abstractmethod
    def from_fields(fields: TFields) -> "SerializableConstraint":
        pass


class DistributeDayOfWeekConstraint(
    SerializableConstraint[tuple[WeekdayField, MultiCheckField, IntField]]
):
    def __init__(
        self,
        weekday: Weekday,
        pgys: dict[int, bool],
        tolerance: int,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        self.weekday = weekday
        self.pgys = pgys
        self.tolerance = tolerance

    @staticmethod
    @override
    def get_name() -> str:
        return "distribute_weekday"

    @staticmethod
    @override
    def human_name() -> str:
        return "Evenly distribute day of week"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        min_pgy = project.get_min_pgy()
        max_pgy = project.get_max_pgy()
        return DistributeDayOfWeekConstraint(
            Weekday.MONDAY, {pgy: False for pgy in range(min_pgy, max_pgy + 1)}, 2
        )

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        weekday = Weekday(data["weekday"])
        pgys = {int(k): bool(v) for k, v in data["pgys"].items()}
        tolerance = int(data["tolerance"])
        enabled = bool(data["enabled"])
        return DistributeDayOfWeekConstraint(weekday, pgys, tolerance, enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {
            "enabled": 1 if self.enabled else 0,
            "weekday": int(self.weekday),
            "pgys": {k: 1 if v else 0 for k, v in self.pgys.items()},
            "tolerance": self.tolerance,
        }

    @override
    def fields(
        self, project: ProjectInfo
    ) -> tuple[WeekdayField, MultiCheckField, IntField]:
        return (
            WeekdayField(self.weekday, name="Day of the week"),
            MultiCheckField({str(k): v for k, v in self.pgys.items()}, name="For PGYs"),
            IntField(self.tolerance, name="Tolerance"),
        )

    @override
    @staticmethod
    def from_fields(
        fields: tuple[WeekdayField, MultiCheckField, IntField],
    ) -> SerializableConstraint:
        weekday = fields[0].value
        pgys = {int(k): v for k, v in fields[1].value.items()}
        tolerance = fields[2].value
        return DistributeDayOfWeekConstraint(weekday, pgys, tolerance)

    @override
    def description(self) -> str:
        base = f"Evenly distribute {self.weekday.human_name()}s"
        set_for = [str(k) for k, v in self.pgys.items() if v]
        if set_for == []:
            return base
        elif len(set_for) == 1:
            return base + " for PGY " + set_for[0]
        else:
            return base + " for PGYs " + ", ".join(set_for)

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        pgys = [pgy for pgy, v in self.pgys.items() if v]
        if pgys == []:
            # Nothing selected means everything selected
            pgys = list(self.pgys.keys())
        pgys = frozenset(pgys)
        days = frozenset({self.weekday})
        min_var = builder.get_min_by_years_on_weekdays(pgys, days)
        max_var = builder.get_max_by_years_on_weekdays(pgys, days)
        return [max_var - min_var <= self.tolerance]


class DistributeWeekendsConstraint(SerializableConstraint):
    def __init__(
        self, pgys: dict[int, bool], tolerance: int, enabled: bool = True
    ) -> None:
        self.pgys = pgys
        self.tolerance = tolerance
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "distribute_weekends"

    @staticmethod
    @override
    def human_name() -> str:
        return "Evenly distribute weekend days (combined Saturdays and Sundays)"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        min_pgy = project.get_min_pgy()
        max_pgy = project.get_max_pgy()
        return DistributeWeekendsConstraint(
            {pgy: False for pgy in range(min_pgy, max_pgy + 1)}, 2
        )

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        pgys = {int(k): bool(v) for k, v in data["pgys"].items()}
        tolerance = int(data["tolerance"])
        enabled = bool(data["enabled"])
        return DistributeWeekendsConstraint(pgys, tolerance, enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {
            "pgys": {k: 1 if v else 0 for k, v in self.pgys.items()},
            "tolerance": self.tolerance,
            "enabled": self.enabled,
        }

    @override
    def fields(self, project: ProjectInfo) -> tuple[(MultiCheckField, IntField)]:
        return (
            MultiCheckField({str(k): v for k, v in self.pgys.items()}, name="For PGYs"),
            IntField(self.tolerance, name="Tolerance"),
        )

    @override
    @staticmethod
    def from_fields(
        fields: tuple[(MultiCheckField, IntField)],
    ) -> SerializableConstraint:
        return DistributeWeekendsConstraint(
            {int(k): v for k, v in fields[0].value.items()}, fields[1].value
        )

    @override
    def description(self) -> str:
        base = DistributeWeekendsConstraint.human_name()
        set_for = [str(k) for k, v in self.pgys.items() if v]
        if set_for == []:
            return base
        elif len(set_for) == 1:
            return base + " for PGY " + set_for[0]
        else:
            return base + " for PGYs " + ", ".join(set_for)

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        pgys = [pgy for pgy, v in self.pgys.items() if v]
        if pgys == []:
            # Nothing selected means everything selected
            pgys = list(self.pgys.keys())
        pgys = frozenset(pgys)
        weekend = frozenset({Weekday.SATURDAY, Weekday.SUNDAY})
        min_var = builder.get_min_by_years_on_weekdays(pgys, weekend)
        max_var = builder.get_max_by_years_on_weekdays(pgys, weekend)
        return [max_var - min_var <= self.tolerance]


class ConstrainWeekdayConstraint(SerializableConstraint):
    def __init__(
        self,
        weekday: Weekday,
        minimum: int,
        limit: int,
        pgys: dict[int, bool],
        enabled: bool = True,
    ) -> None:
        self.weekday = weekday
        self.minimum = minimum
        self.limit = limit
        self.pgys = pgys
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "constrain_weekday"

    @staticmethod
    @override
    def human_name() -> str:
        return "Constrain a day of the week"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        min_pgy = project.get_min_pgy()
        max_pgy = project.get_max_pgy()
        return ConstrainWeekdayConstraint(
            Weekday.MONDAY, 5, 10, {pgy: False for pgy in range(min_pgy, max_pgy + 1)}
        )

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        pgys = {int(k): bool(v) for k, v in data["pgys"].items()}
        enabled = bool(data["enabled"])
        return ConstrainWeekdayConstraint(
            Weekday(data["weekday"]),
            int(data["min"]),
            int(data["limit"]),
            pgys,
            enabled,
        )

    @override
    def serialize(self) -> dict[str, Any]:
        return {
            "weekday": int(self.weekday),
            "min": self.minimum,
            "limit": self.limit,
            "pgys": {k: 1 if v else 0 for k, v in self.pgys.items()},
            "enabled": 1 if self.enabled else 0,
        }

    @override
    def fields(
        self, project: ProjectInfo
    ) -> tuple[WeekdayField, IntField, IntField, MultiCheckField]:
        return (
            WeekdayField(self.weekday, "Day of the week"),
            IntField(self.minimum, "Minimum"),
            IntField(self.limit, "Maximum"),
            MultiCheckField({str(k): v for k, v in self.pgys.items()}, name="For PGYs"),
        )

    @override
    @staticmethod
    def from_fields(
        fields: tuple[WeekdayField, IntField, IntField, MultiCheckField],
    ) -> SerializableConstraint:
        pgys = {int(k): v for k, v in fields[3].value.items()}
        return ConstrainWeekdayConstraint(
            fields[0].value, fields[1].value, fields[2].value, pgys
        )

    @override
    def description(self) -> str:
        base = f"Constrain {self.weekday.human_name()}s between {self.minimum} and {self.limit}"
        set_for = [str(k) for k, v in self.pgys.items() if v]
        if set_for == []:
            return base
        elif len(set_for) == 1:
            return base + " for PGY " + set_for[0]
        else:
            return base + " for PGYs " + ", ".join(set_for)

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        pgys = [pgy for pgy, v in self.pgys.items() if v]
        if pgys == []:
            # Nothing selected means everything selected
            pgys = list(self.pgys.keys())
        pgys = set(pgys)

        constraints: list[pulp.LpConstraint] = []
        for days_for_resident in builder.get_day_vars(pgys).values():
            day = days_until_next_weekday(builder.get_start_date(), self.weekday)
            day_vars = []
            while day < builder.get_num_days():
                day_vars.append(days_for_resident[day])
                day += 7
            together = var_sum(day_vars)
            constraints.append(together >= self.minimum)
            constraints.append(together <= self.limit)
        return constraints


class LimitWeekdayForResidentConstraint(SerializableConstraint):
    def __init__(
        self, weekday: Weekday, limit: int, resident: str, enabled: bool = True
    ) -> None:
        self.weekday = weekday
        self.limit = limit
        self.resident = resident
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_weekday_for_resident"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit a day of the week for a resident"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return LimitWeekdayForResidentConstraint(
            Weekday.MONDAY, 5, project.get_residents()[0]
        )

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return LimitWeekdayForResidentConstraint(
            Weekday(data["weekday"]), int(data["limit"]), str(data["resident"]), enabled
        )

    @override
    def serialize(self) -> dict[str, Any]:
        return {
            "weekday": int(self.weekday),
            "limit": self.limit,
            "resident": self.resident,
            "enabled": 1 if self.enabled else 0,
        }

    @override
    def fields(
        self, project: ProjectInfo
    ) -> tuple[WeekdayField, IntField, LimitedStringField]:
        return (
            WeekdayField(self.weekday, "Day of the week"),
            IntField(self.limit, "Limit"),
            LimitedStringField(self.resident, "Resident", project.get_residents()),
        )

    @override
    @staticmethod
    def from_fields(
        fields: tuple[WeekdayField, IntField, LimitedStringField],
    ) -> SerializableConstraint:
        return LimitWeekdayForResidentConstraint(
            fields[0].value, fields[1].value, fields[2].value
        )

    @override
    def description(self) -> str:
        return f"Limit {self.weekday.human_name()}s for {self.resident} to {self.limit}"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        day_vars = builder.get_vars_for_weekday(self.resident, self.weekday)
        return [var_sum(day_vars) <= self.limit]


class SetMinimumForDaysOfWeekForResidentConstraint(SerializableConstraint):
    def __init__(
        self, weekdays: set[Weekday], minimum: int, resident: str, enabled: bool = True
    ) -> None:
        self.weekdays = weekdays
        self.minimum = minimum
        self.resident = resident
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "minimum_for_days_of_week_for_resident"

    @staticmethod
    @override
    def human_name() -> str:
        return "Set minimum for day of week for resident"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return SetMinimumForDaysOfWeekForResidentConstraint(
            {Weekday.MONDAY}, 5, project.get_residents()[0]
        )

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        weekdays = {Weekday(int(w)) for w in data["weekdays"].split(",")}
        enabled = bool(data["enabled"])
        return SetMinimumForDaysOfWeekForResidentConstraint(
            weekdays, int(data["minimum"]), str(data["resident"]), enabled
        )

    @override
    def serialize(self) -> dict[str, Any]:
        weekdays = ",".join([str(w) for w in self.weekdays])
        return {
            "weekdays": weekdays,
            "minimum": self.minimum,
            "resident": self.resident,
            "enabled": 1 if self.enabled else 0,
        }

    @override
    def fields(
        self, project: ProjectInfo
    ) -> tuple[WeekdayListField, IntField, LimitedStringField]:
        return (
            WeekdayListField(self.weekdays, "Days of the week"),
            IntField(self.minimum, "Minimum"),
            LimitedStringField(self.resident, "Resident", project.get_residents()),
        )

    @override
    @staticmethod
    def from_fields(
        fields: tuple[WeekdayListField, IntField, LimitedStringField],
    ) -> SerializableConstraint:
        return SetMinimumForDaysOfWeekForResidentConstraint(
            fields[0].value, fields[1].value, fields[2].value
        )

    @override
    def description(self) -> str:
        if len(self.weekdays) == 1:
            return f"Ensure {self.resident} has at least {self.minimum} {next(iter(self.weekdays)).human_name()}s"
        else:
            weekdays_str = ", ".join([w.human_name() for w in self.weekdays])
            return f"Ensure {self.resident} has at least {self.minimum} of days: {weekdays_str}"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        day_varss = [
            builder.get_vars_for_weekday(self.resident, weekday)
            for weekday in self.weekdays
        ]
        day_vars = [dv for sublist in day_varss for dv in sublist]
        return [var_sum(day_vars) >= self.minimum]


class NoAdjacentWeekendsConstraint(SerializableConstraint):
    def __init__(self, num: int, enabled: bool = True):
        self.num = num
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "no_adjacent_weekends"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit weekends worked in a row"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return NoAdjacentWeekendsConstraint(1)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        num = int(data["num"])
        return NoAdjacentWeekendsConstraint(enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {"num": self.num, "enabled": 1 if self.enabled else 0}

    @override
    def fields(self, project: ProjectInfo) -> tuple[(IntField)]:
        return (IntField(self.num, name="Number", minimum=1),)

    @override
    @staticmethod
    def from_fields(fields: tuple[(IntField)]) -> SerializableConstraint:
        return NoAdjacentWeekendsConstraint(fields[0].value)

    @override
    def description(self) -> str:
        return f"Ensure no resident works more than {self.num} {'weekend' if self.num == 1 else 'weekends'} in a row"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []

        residents = builder.get_residents().keys()
        for resident in residents:
            weekend_tuples = builder.get_vars_for_weekends(resident)
            weekends_worked = []
            for weekend in weekend_tuples:
                match weekend:
                    case None, sunday:
                        worked = sunday
                    case saturday, None:
                        worked = saturday
                    case saturday, sunday:
                        worked = saturday + sunday
                weekends_worked.append(worked)

            # For a sliding window of our limit + 1, ensure the total number of weekends worked is within the limit
            for i in range(len(weekends_worked) - self.num - 1):
                constraints.append(
                    var_sum(weekends_worked[i : i + self.num + 1]) <= self.num
                )

        return constraints


class ConstrainPGYConstraint(SerializableConstraint):
    def __init__(
        self, pgy: int, minimum: int, limit: int, enabled: bool = True
    ) -> None:
        self.pgy = pgy
        self.minimum = minimum
        self.limit = limit
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "constrain_pgy"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit calls for a PGY year"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return ConstrainPGYConstraint(project.get_min_pgy(), 20, 25)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return ConstrainPGYConstraint(
            int(data["pgy"]), int(data["minimum"]), int(data["limit"]), enabled
        )

    @override
    def serialize(self) -> dict[str, Any]:
        return {
            "pgy": self.pgy,
            "minimum": self.minimum,
            "limit": self.limit,
            "enabled": 1 if self.enabled else 0,
        }

    @override
    def fields(self, project: ProjectInfo) -> tuple[IntField, IntField, IntField]:
        return (
            IntField(
                self.pgy,
                name="PGY",
                minimum=project.get_min_pgy(),
                maximum=project.get_max_pgy(),
            ),
            IntField(self.minimum, "Minimum"),
            IntField(self.limit, "Limit"),
        )

    @override
    @staticmethod
    def from_fields(
        fields: tuple[IntField, IntField, IntField],
    ) -> SerializableConstraint:
        return ConstrainPGYConstraint(fields[0].value, fields[1].value, fields[2].value)

    @override
    def description(self) -> str:
        return f"Limit calls for PGY{self.pgy}s between {self.minimum} and {self.limit}"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []
        for resident, days_for_resident in builder.get_day_vars().items():
            if builder.get_residents()[resident].pgy != self.pgy:
                continue
            vs = var_sum(days_for_resident)
            constraints.append(vs >= self.minimum)
            constraints.append(vs <= self.limit)
        return constraints


class LimitVACoverageConstraint(SerializableConstraint):
    def __init__(self, limit: int, enabled: bool = True) -> None:
        self.limit = limit
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_va_coverage"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit VA coverage days"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return LimitVACoverageConstraint(5)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return LimitVACoverageConstraint(int(data["limit"]), enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit, "enabled": 1 if self.enabled else 0}

    @override
    def fields(self, project: ProjectInfo) -> tuple[IntField]:
        return (IntField(self.limit, "Limit"),)

    @override
    @staticmethod
    def from_fields(fields: tuple[IntField]) -> SerializableConstraint:
        return LimitVACoverageConstraint(fields[0].value)

    @override
    def description(self) -> str:
        return f"Limit VA coverage days to {self.limit}"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        return [var_sum(builder.get_va_vars()) <= self.limit]


class DistributeQ2sConstraint(SerializableConstraint):
    def __init__(self, tolerance: int, enabled: bool = True) -> None:
        self.tolerance = tolerance
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "distribute_q2s"

    @staticmethod
    @override
    def human_name() -> str:
        return "Evenly distribute Q2s"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return DistributeQ2sConstraint(5)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return DistributeQ2sConstraint(int(data["tolerance"]), enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {"tolerance": self.tolerance, "enabled": 1 if self.enabled else 0}

    @override
    def fields(self, project: ProjectInfo) -> tuple[IntField]:
        return (IntField(self.tolerance, "Tolerance"),)

    @override
    @staticmethod
    def from_fields(fields: tuple[IntField]) -> SerializableConstraint:
        return DistributeQ2sConstraint(fields[0].value)

    @override
    def description(self) -> str:
        return f"Keep the difference between the most and least Q2s to {self.tolerance}"

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
    def __init__(self, limit: int, enabled: bool = True) -> None:
        self.limit = limit
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_q2s"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit the number of Q2s per resident"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return LimitQ2sConstraint(5)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return LimitQ2sConstraint(int(data["limit"]), enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit, "enabled": 1 if self.enabled else 0}

    @override
    def fields(self, project: ProjectInfo) -> tuple[IntField]:
        return (IntField(self.limit, "Limit"),)

    @override
    @staticmethod
    def from_fields(fields: tuple[IntField]) -> SerializableConstraint:
        return LimitQ2sConstraint(fields[0].value)

    @override
    def description(self) -> str:
        return f"Limit the number of Q2s per resident to {self.limit}"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        constraints: list[pulp.LpConstraint] = []
        q2s_dict = builder.get_qn_vars(2)
        for q2_vars in q2s_dict.values():
            constraints.append(var_sum(q2_vars) <= self.limit)
        return constraints


class LimitTotalQ2sConstraint(SerializableConstraint):
    def __init__(self, limit: int, enabled: bool = True) -> None:
        self.limit = limit
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_total_q2s"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit the total number of Q2s"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return LimitTotalQ2sConstraint(20)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return LimitTotalQ2sConstraint(int(data["limit"]), enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit, "enabled": 1 if self.enabled else 0}

    @override
    def fields(self, project: ProjectInfo) -> tuple[IntField]:
        return (IntField(self.limit, "Q2s"),)

    @override
    @staticmethod
    def from_fields(fields: tuple[IntField]) -> SerializableConstraint:
        return LimitTotalQ2sConstraint(fields[0].value)

    @override
    def description(self) -> str:
        return f"Limit the total Q2s to {self.limit}"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        q2s_dict = builder.get_qn_vars(2)
        q2s = [v for vs in q2s_dict.values() for v in vs]
        return [var_sum(q2s) <= self.limit]


class LimitPGY23GapConstraint(SerializableConstraint):
    def __init__(self, limit: int, enabled: bool = True) -> None:
        self.limit = limit
        self.enabled = enabled

    @staticmethod
    @override
    def get_name() -> str:
        return "limit_pgy_2_3_gap"

    @staticmethod
    @override
    def human_name() -> str:
        return "Limit the difference between the PGY2 with the most call and the PGY3 with the least call"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Constraint:
        return LimitPGY23GapConstraint(4)

    @staticmethod
    @override
    def deserialize(data: dict[str, Any]) -> Constraint:
        enabled = bool(data["enabled"])
        return LimitPGY23GapConstraint(int(data["limit"]), enabled)

    @override
    def serialize(self) -> dict[str, Any]:
        return {"limit": self.limit, "enabled": 1 if self.enabled else 0}

    @override
    def fields(self, project: ProjectInfo) -> tuple[IntField]:
        return (IntField(self.limit, "Limit"),)

    @override
    @staticmethod
    def from_fields(fields: tuple[IntField]) -> SerializableConstraint:
        return LimitPGY23GapConstraint(fields[0].value)

    @override
    def description(self) -> str:
        return f"Ensure the PGY2 with the most call has no more than {self.limit} more than the PGY3 with the least call"

    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        max_2 = builder.get_max_by_year(2)
        min_3 = builder.get_min_by_year(3)
        return [max_2 - min_3 <= self.limit]


class ConstraintRegistry:
    def __init__(self) -> None:
        self.constraints = {
            c.get_name(): c
            for c in [
                DistributeDayOfWeekConstraint,
                DistributeWeekendsConstraint,
                ConstrainWeekdayConstraint,
                LimitWeekdayForResidentConstraint,
                SetMinimumForDaysOfWeekForResidentConstraint,
                NoAdjacentWeekendsConstraint,
                ConstrainPGYConstraint,
                LimitVACoverageConstraint,
                DistributeQ2sConstraint,
                LimitQ2sConstraint,
                LimitTotalQ2sConstraint,
                LimitPGY23GapConstraint,
            ]
        }

    def deserialize(self, name: str, data: dict[str, Any]) -> SerializableConstraint:
        return self.constraints[name].deserialize(data)
