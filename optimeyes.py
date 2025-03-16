from problem import Problem, new_integer_variable, new_binary_variable, new_continuous_variable
from functools import reduce
import math

NUM_WEEKS = 4
# TODO: incorporate availability
RESIDENT_AVAILABILITY = {
    "Sophia": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ],
    "Paris": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ],
    "Keir": [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ],
}

MAX_DAYS_PER_RESIDENT = math.ceil(NUM_WEEKS * 7 / float(len(RESIDENT_AVAILABILITY.keys())))

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

def var_sum(vs):
    return reduce(lambda x, y: x + y, vs)

def key_for_day(week: int, day: int, resident: str) -> str:
    return f"Week_{week}_{day}_{resident}"

problem = Problem("optimEYES", minimize=True)

# For each resident, create a variable representing every day
day_vars = {resident: [] for resident in RESIDENT_AVAILABILITY.keys()}
for resident in RESIDENT_AVAILABILITY.keys():
    for week in range(NUM_WEEKS):
        for day in DAYS_OF_WEEK:
            day_vars[resident].append(new_binary_variable(key_for_day(week, day, resident)))

    # Ensure even distribution
    problem.add_constraint(var_sum(day_vars[resident]) <= MAX_DAYS_PER_RESIDENT)

for day in range(NUM_WEEKS * 7):
    all_residents_for_day = [days_for_resident[day] for days_for_resident in day_vars.values()]
    # Ensure exactly one resident is assigned to each day
    problem.add_constraint(var_sum(all_residents_for_day) == 1)

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
problem.set_objective(var_sum(q2s))

solution = problem.solve()

# Overall status, were we able to find a solution?
print("Status:", solution.get_status())

results = solution.get_variables()
for week in range(NUM_WEEKS):
    print(f"Week {week}:")
    for day in DAYS_OF_WEEK:
        assigned_resident = None
        for resident in RESIDENT_AVAILABILITY.keys():
            if results[key_for_day(week, day, resident)] != 0.0:
                assert assigned_resident is None, "Two residents assigned to the same day"
                assigned_resident = resident
        assert assigned_resident is not None, "No residents assigned to a day"
        print(f"\t{day}: {assigned_resident}")

"""
for name, val in results.items():
    if name.startswith("q2_"):
        print(f"{name} = {val}")
"""

print("Total Q2 calls = ", solution.get_objective_value())

