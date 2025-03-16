from linear_problem import PulpProblem, new_binary_variable, new_continuous_variable
from functools import reduce
from solution import Solution, key_for_day
from datetime import date, timedelta
import math

START_DATE = date.fromisoformat("2025-06-01")
RESIDENT_AVAILABILITY = {
    "Sophia": [
        0, 0, 0, 0, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
    ],
    "Paris": [
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
    ],
    "Keir": [
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
    ],
}

# TODO: validate input

NUM_DAYS = len(next(iter(RESIDENT_AVAILABILITY.values())))

MAX_DAYS_PER_RESIDENT = math.ceil(NUM_DAYS / float(len(RESIDENT_AVAILABILITY.keys())))

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

problem = PulpProblem("optimEYES", minimize=True)

# For each resident, create a variable representing every day
day_vars = {resident: [] for resident in RESIDENT_AVAILABILITY.keys()}
for resident, availability in RESIDENT_AVAILABILITY.items():
    for day, is_available in enumerate(availability):
        day_var = new_binary_variable(key_for_day(day, resident))
        day_vars[resident].append(day_var)
        if is_available == 0:
            # Resident is unavailable this day
            problem.add_constraint(day_var == 0)

    # Ensure even distribution
    problem.add_constraint(sum(day_vars[resident]) <= MAX_DAYS_PER_RESIDENT)
    problem.add_constraint(sum(day_vars[resident]) >= MAX_DAYS_PER_RESIDENT - 1)

for day in range(NUM_DAYS):
    all_residents_for_day = [days_for_resident[day] for days_for_resident in day_vars.values()]
    # Ensure exactly one resident is assigned to each day
    problem.add_constraint(sum(all_residents_for_day) == 1)

# Ensure a resident doesn't work two days in a row
for days_for_resident in day_vars.values():
    for i in range(len(days_for_resident) - 1):
        problem.add_constraint(days_for_resident[i] + days_for_resident[i + 1] <= 1)
        

# Minimize Q2 calls
q2s = []
for resident, days_for_resident in day_vars.items():
    for i in range(len(days_for_resident) - 2):
        var = new_binary_variable(f"q2_{resident}_{i}")
        var_slack = new_continuous_variable(f"q2_{resident}_{i}_cont", 0, 0.9)
        problem.add_constraint(0.5 * days_for_resident[i] + 0.5 * days_for_resident[i + 2] == var + var_slack)
        q2s.append(var)
problem.set_objective(sum(q2s))

solution = problem.solve()

# Overall status, were we able to find a solution?
print("Status:", solution.get_status())

results = Solution(solution.get_variables(), NUM_DAYS, RESIDENT_AVAILABILITY.keys())

for day, resident in enumerate(results.get_assignments()):
    date = START_DATE + timedelta(days=day)
    print(f"\t{date:%a %m-%d}: {resident}")

print("Total Q2 calls = ", solution.get_objective_value())

print("Per resident stats:")
calls = results.get_calls_per_resident()
q2s = results.get_q2s_per_resident()
for resident in RESIDENT_AVAILABILITY.keys():
    print(f"\t{resident}")
    print(f"\t\tTotal calls = {calls[resident]}")
    print(f"\t\tTotal Q2s = {q2s[resident]}")

