from typing import Dict, Sequence, Mapping
from datetime import date, timedelta
from collections import defaultdict

from dateutil import days_until_next_weekday
from structs.output_mode import OutputMode
from structs.resident import Resident


def key_for_day(day: int, resident: str) -> str:
    return f"Day_{day}_{resident}"


class Solution:
    def __init__(
        self,
        objective_value: float,
        values: Mapping[str, float],
        start_date: date,
        num_days: int,
        residents: dict[str, Resident],
    ) -> None:
        self.objective_value = objective_value
        self.values = values
        self.start_date = start_date
        self.num_days = num_days
        self.residents = residents
        self.assignments = None

    def __getitem__(self, key: str) -> float:
        return self.values[key]

    def get_objective_value(self) -> float:
        return self.objective_value

    def get_assignments(self) -> Sequence[Sequence[str]]:
        if self.assignments is not None:
            return self.assignments

        self.assignments = []

        for day in range(self.num_days):
            assigned_residents = [
                resident
                for resident in self.residents.keys()
                if self.values[key_for_day(day, resident)] != 0.0
            ]
            assert assigned_residents != [], "No residents assigned to a day"
            self.assignments.append(assigned_residents)

        return self.assignments

    def get_calls_per_resident(self) -> Dict[str, int]:
        result = {resident: 0 for resident in self.residents.keys()}
        for assignments in self.get_assignments():
            for resident in assignments:
                result[resident] += 1
        return result

    def get_qns_per_resident(self, n: int) -> Dict[str, int]:
        assignments = self.get_assignments()
        result = {resident: 0 for resident in self.residents.keys()}
        for day in range(self.num_days - n):
            for resident in set(assignments[day]).intersection(
                set(assignments[day + n])
            ):
                result[resident] += 1
        return result

    def get_weariness_per_resident(
        self, weariness_map: dict[int, int] | None
    ) -> dict[str, tuple[int, dict[int, int]]] | None:
        """
        For each resident, returns total weariness score and breakdown of count
        of each qn.
        """
        if weariness_map is None:
            return None

        scores: dict[str, int] = {resident: 0 for resident in self.residents.keys()}
        breakdown: dict[str, dict[int, int]] = {
            resident: {} for resident in self.residents.keys()
        }
        for n, incr in weariness_map.items():
            for resident, qns in self.get_qns_per_resident(n).items():
                scores[resident] += qns * incr
                breakdown[resident][n] = qns
        return {r: (scores[r], breakdown[r]) for r in self.residents.keys()}

    def fmt_weariness(self, score_and_breakdown: tuple[int, dict[int, int]]) -> str:
        score, breakdown = score_and_breakdown
        breakdown_str = ", ".join(
            f"{breakdown[n]}x Q{n}"
            for n in sorted(breakdown.keys())
            if breakdown[n] > 0
        )
        return f"{score} ({breakdown_str})"

    def get_q2_unfairness(self) -> int:
        """
        Calculate the difference between the maximum number of q2s and the minimum.
        """
        q2s = self.get_qns_per_resident(2).values()
        return max(q2s) - min(q2s)

    def get_max_q2s(self) -> int:
        """
        Calculate the most Q2s anyone has.
        """
        q2s = self.get_qns_per_resident(2).values()
        return max(q2s)

    def get_total_q2s(self) -> int:
        q2s = self.get_qns_per_resident(2).values()
        return sum(q2s)

    def get_calls_taken_by_year(self) -> Dict[int, int]:
        result = defaultdict(lambda: 0)
        for assignments in self.get_assignments():
            for resident in assignments:
                result[self.residents[resident].pgy] += 1
        return result

    def _get_count_of_weekday(self, weekday) -> Dict[str, int]:
        assignments = self.get_assignments()
        result = {resident: 0 for resident in self.residents.keys()}
        next_day = days_until_next_weekday(self.start_date, weekday)
        while next_day < self.num_days:
            for resident in assignments[next_day]:
                result[resident] += 1
            next_day += 7
        return result

    def get_saturdays(self) -> Dict[str, int]:
        return self._get_count_of_weekday(5)

    def get_sundays(self) -> Dict[str, int]:
        return self._get_count_of_weekday(6)

    def get_va_covered_days(self) -> list[date]:
        result = []
        for day, residents in enumerate(self.get_assignments()):
            va_residents = [
                resident for resident in residents if self.residents[resident].va[day]
            ]
            if va_residents:
                result.append(self.start_date + timedelta(days=day))
        return result

    def get_changes_from_previous(self, previous: list[list[str]]) -> list[str]:
        changed = []
        for day, data in enumerate(zip(self.get_assignments(), previous)):
            current, prev = data
            if sorted(current) != sorted(prev):
                d = self.start_date + timedelta(days=day)
                changed.append(
                    f"{d:%m/%d/%Y} ({', '.join(prev)} -> {', '.join(current)})"
                )
        return changed

    def get_availability_violations(self) -> dict[int, list[str]]:
        # index of day violated -> residents now assigned to that day
        results: dict[int, list[str]] = {}
        for day in range(self.num_days):
            violated = [
                resident.name
                for resident in self.residents.values()
                if self.values[key_for_day(day, resident.name)] != 0.0
                and resident.availability[day] == 0
            ]
            if violated != []:
                results[day] = violated
        return results

    def _coverage_msg_for(self, index: int, csv: bool) -> str:
        covered = [
            (name, resident.coverage[index])
            for name, resident in self.residents.items()
            if index in resident.coverage
        ]
        if covered == []:
            return ""
        else:
            assert (
                len(covered) == 1
            ), "Multiple residents covered on day {index}: {', '.join(name for name, _ in covered)}"
            name, reason = covered[0]
            if csv:
                return f"Covering for {name} due to {reason}"
            else:
                return f" (covering for {name} due to {reason})"

    def print(
        self,
        mode: OutputMode,
        previous: list[list[str]] | None,
        weariness_map: dict[int, int] | None,
    ) -> None:
        if mode == OutputMode.LIST:
            print(
                "\n".join(
                    ",".join(sorted(residents)) for residents in self.get_assignments()
                )
            )
            return

        for day, residents in enumerate(self.get_assignments()):
            date = self.start_date + timedelta(days=day)
            cover_msg = self._coverage_msg_for(day, mode == OutputMode.CSV)
            if mode == OutputMode.CSV:
                print(f"{date:%A},{date:%m/%d/%Y},{'/'.join(residents)},{cover_msg}")
            else:
                print(f"\t[{day}] {date:%a %m-%d}: {', '.join(residents)}{cover_msg}")

        if mode == OutputMode.CSV:
            return

        print("Objective value = ", self.get_objective_value())
        print("Total Q2 calls = ", self.get_total_q2s())
        print("Q2 unfairness = ", self.get_q2_unfairness())
        calls_by_year = self.get_calls_taken_by_year()
        print(
            f"Calls taken by PGY2s =  {calls_by_year[2]}  ({calls_by_year[2] / self.num_days * 100:.2f}%)"
        )
        print(
            f"Calls taken by PGY3s =  {calls_by_year[3]}  ({calls_by_year[3] / self.num_days * 100:.2f}%)"
        )
        if previous is None:
            print("Changes from previous: N/A")
        else:
            changed = self.get_changes_from_previous(previous)
            print(f"Changes from previous ({len(changed)}): ", ", ".join(changed))
        va_covered = self.get_va_covered_days()
        print(
            f"VA coverage dates ({len(va_covered)}): ",
            ", ".join(f"{d:%m/%d/%Y}" for d in va_covered),
        )

        print("Per resident stats:")
        calls = self.get_calls_per_resident()
        saturdays = self.get_saturdays()
        sundays = self.get_sundays()
        q2s = self.get_qns_per_resident(2)
        weariness = self.get_weariness_per_resident(weariness_map)
        for resident in self.residents.keys():
            print(f"\t{resident}")
            print(f"\t\tCalls = {calls[resident]}")
            print(f"\t\tSaturdays = {saturdays[resident]}")
            print(f"\t\tSundays = {sundays[resident]}")
            print(f"\t\tQ2s = {q2s[resident]}")
            if weariness is not None:
                print(f"\t\tWeariness = {self.fmt_weariness(weariness[resident])}")
