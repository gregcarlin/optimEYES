from pathlib import Path
from typing import override
from dataclasses import dataclass
from datetime import timedelta

from PySide6 import QtCore, QtWidgets

from structs.project import Project
from structs.field import (
    Field,
)
from optimization.call_problem_impl import CallProblemBuilderImpl
from optimization.availability import AvailabilityConstraint
from optimization.solution import Solution
from optimization.metric import SummaryMetric, ResidentMetric, DetailMetric
from optimization.constraint import ConstraintRegistry
from typeutil import none_throws
from gui.table import TableWidget, SectionHeaderWidget, AddOrEditWidget, AddNewWidget
from gui.common import center_on_screen


class ConstraintsHeaderWidget(SectionHeaderWidget):
    def __init__(self, project: Project, parent: "EditProjectWidget") -> None:
        super().__init__("Constraints")

        self.project = project
        self.edit_parent = parent

    @QtCore.Slot()
    @override
    def add_new_clicked(self):
        self.add_widget = AddConstraintWidget(self.project, self.edit_parent)
        self.add_widget.show()
        center_on_screen(self.add_widget)
        self.edit_parent.setEnabled(False)


class ObjectivesHeaderWidget(SectionHeaderWidget):
    def __init__(self) -> None:
        super().__init__("Objectives")

    @QtCore.Slot()
    @override
    def add_new_clicked(self):
        # TODO implement
        pass


class EditConstraintWidget(AddOrEditWidget):
    def __init__(
        self, project: Project, constraint_index: int, root: "EditProjectWidget"
    ) -> None:
        super().__init__(root)

        self.project = project
        self.index = constraint_index
        self.root = root
        self.setWindowTitle("Edit Constraint")

        self.populate_fields()

    @override
    def get_current_fields(self) -> tuple[Field, ...]:
        return self.project.constraints[self.index].fields(self.project)

    @override
    def save_clicked(self) -> None:
        new_fields = self._rebuild_fields()
        constraint = self.project.constraints[self.index]
        new_constraint = constraint.from_fields(new_fields)
        self.project.constraints[self.index] = new_constraint
        self.root.update_project(self.project)
        self.close()


class EditObjectiveWidget(AddOrEditWidget):
    def __init__(
        self, project: Project, objective_index: int, root: "EditProjectWidget"
    ) -> None:
        super().__init__(root)

        self.project = project
        self.index = objective_index
        self.root = root
        self.setWindowTitle("Edit Objective")

        self.populate_fields()

    @override
    def get_current_fields(self) -> tuple[Field, ...]:
        return self.project.objectives[self.index].fields(self.project)

    @override
    def save_clicked(self) -> None:
        new_fields = self._rebuild_fields()
        objective = self.project.objectives[self.index]
        new_objective = objective.from_fields(new_fields)
        self.project.objectives[self.index] = new_objective
        self.root.update_project(self.project)
        self.close()


class AddConstraintWidget(AddNewWidget):
    def __init__(self, project: Project, root: "EditProjectWidget") -> None:
        self.project = project
        self.root = root
        self.constraints = ConstraintRegistry().constraints
        super().__init__(
            root,
            [self.constraints[k].human_name() for k in sorted(self.constraints.keys())],
        )

    @override
    def get_current_fields(self) -> tuple[Field, ...]:
        selected = list(sorted(self.constraints.keys()))[self.index]
        return self.constraints[selected].default(self.project).fields(self.project)

    @override
    def save_clicked(self) -> None:
        new_fields = self._rebuild_fields()
        selected = list(sorted(self.constraints.keys()))[self.index]
        new_constraint = self.constraints[selected].from_fields(new_fields)
        self.project.constraints.append(new_constraint)
        self.root.update_project(self.project)
        self.close()


class ConstraintsWidget(TableWidget):
    def __init__(self, project: Project, parent: "EditProjectWidget") -> None:
        super().__init__(project, len(project.constraints), 2)

        self.edit_parent = parent

        for i, constraint in enumerate(project.constraints):
            self.setRow(
                i, constraint.description(), constraint.fields(self.project) != ()
            )

    @override
    def edit_clicked(self, index: int) -> None:
        self.edit_widget = EditConstraintWidget(self.project, index, self.edit_parent)
        self.edit_widget.show()
        center_on_screen(self.edit_widget)
        self.edit_parent.setEnabled(False)

    @override
    def delete_clicked(self, index: int) -> None:
        self.project.constraints.pop(index)
        self.edit_parent.update_project(self.project)


class ObjectivesWidget(TableWidget):
    def __init__(self, project: Project, parent: "EditProjectWidget") -> None:
        super().__init__(project, len(project.objectives), 4)

        self.edit_parent = parent

        for i, objective in enumerate(project.objectives):
            self.setRow(
                i, objective.description(), objective.fields(self.project) != ()
            )
            # TODO add buttons to reorder objectives

    @override
    def edit_clicked(self, index: int) -> None:
        self.edit_widget = EditObjectiveWidget(self.project, index, self.edit_parent)
        self.edit_widget.show()
        center_on_screen(self.edit_widget)
        self.edit_parent.setEnabled(False)

    @override
    def delete_clicked(self, index: int) -> None:
        self.project.objectives.pop(index)
        self.edit_parent.update_project(self.project)


@dataclass
class SolveResult:
    result: Solution | str


class SolveThread(QtCore.QThread):
    done_signal = QtCore.Signal(SolveResult)

    def __init__(self, project: Project, parent: "EditProjectWidget") -> None:
        super().__init__(parent)

        self.project = project
        self.result: Solution | str | None = None

    @override
    def run(self) -> None:
        builder = CallProblemBuilderImpl(self.project)
        builder.apply_constraints([AvailabilityConstraint()])
        builder.apply_constraints(self.project.constraints)
        builder.set_objectives(self.project.objectives)
        result = builder.solve()
        self.done_signal.emit(SolveResult(result))


class ResultSummary(QtWidgets.QWidget):
    def __init__(self, project: Project, solution: Solution) -> None:
        super().__init__()

        layout = QtWidgets.QGridLayout(self)

        layout.addWidget(
            QtWidgets.QLabel(f"Total Q2 Calls: {solution.get_total_q2s()}"), 0, 0
        )
        layout.addWidget(
            QtWidgets.QLabel(f"Q2 Unfairness: {solution.get_q2_unfairness()}"), 1, 0
        )

        calls_by_year = solution.get_calls_taken_by_year()
        for i, year in enumerate(sorted(calls_by_year.keys())):
            layout.addWidget(
                QtWidgets.QLabel(
                    f"Calls taken by PGY{year}s: {calls_by_year[year]} ({calls_by_year[year] / solution.num_days * 100:.2f}%)"
                ),
                i,
                1,
            )

        va_coverage = solution.get_va_covered_days()
        if va_coverage == []:
            layout.addWidget(QtWidgets.QLabel(f"VA covered days: None"), 0, 2)
        else:
            days_str = ", ".join(f"{d:%-m/%d/%y}" for d in va_coverage)
            layout.addWidget(
                QtWidgets.QLabel(f"VA covered days ({len(va_coverage)}): {days_str}"),
                0,
                2,
            )
        metrics = [
            m
            for m in project.constraints + project.objectives
            if isinstance(m, SummaryMetric)
        ]
        assignments = solution.get_assignments()
        for i, m in enumerate(metrics):
            layout.addWidget(
                QtWidgets.QLabel(
                    f"{m.summary_metric_header()}: {m.summary_metric(assignments)}"
                ),
                1 + i,
                2,
            )


class ResultResidentSummary(QtWidgets.QTableWidget):
    def __init__(self, project: Project, solution: Solution) -> None:
        super().__init__()

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setRowCount(len(solution.residents))
        metrics = [
            m
            for m in project.constraints + project.objectives
            if isinstance(m, ResidentMetric)
        ]
        self.setColumnCount(4 + len(metrics))
        self.setHorizontalHeaderLabels(
            ["Calls", "Saturdays", "Sundays", "Q2s"]
            + [m.resident_metric_header() for m in metrics]
        )
        resident_names = list(sorted(solution.residents.keys()))
        self.setVerticalHeaderLabels(resident_names)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setDefaultSectionSize(20)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        calls = solution.get_calls_per_resident()
        saturdays = solution.get_saturdays()
        sundays = solution.get_sundays()
        q2s = solution.get_qns_per_resident(2)
        assignments = solution.get_assignments()
        other = [m.resident_metric(assignments) for m in metrics]
        for i, name in enumerate(resident_names):
            self.setCellWidget(i, 0, QtWidgets.QLabel(str(calls[name])))
            self.setCellWidget(i, 1, QtWidgets.QLabel(str(saturdays[name])))
            self.setCellWidget(i, 2, QtWidgets.QLabel(str(sundays[name])))
            self.setCellWidget(i, 3, QtWidgets.QLabel(str(q2s[name])))
            for j, metric in enumerate(other):
                self.setCellWidget(i, 4 + j, QtWidgets.QLabel(metric[name]))

    @override
    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(400, 600)


class ResultDetail(QtWidgets.QTableWidget):
    def __init__(self, project: Project, solution: Solution) -> None:
        super().__init__()

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setRowCount(solution.num_days)
        metrics = [
            m
            for m in project.constraints + project.objectives
            if isinstance(m, DetailMetric)
        ]
        self.setColumnCount(2 + len(metrics))
        self.setHorizontalHeaderLabels(
            ["Resident", "Coverage"] + [m.detail_metric_header() for m in metrics]
        )
        none_throws(self.horizontalHeaderItem(0)).setToolTip(
            "Resident(s) assigned to be on call"
        )
        none_throws(self.horizontalHeaderItem(1)).setToolTip(
            "Who they're covering for, if any"
        )
        for i, metric in enumerate(metrics):
            none_throws(self.horizontalHeaderItem(2 + i)).setToolTip(
                metric.detail_metric_tooltip()
            )
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        dates = [
            solution.start_date + timedelta(days=day)
            for day in range(solution.num_days)
        ]
        self.setVerticalHeaderLabels([f"{date:%a %-m/%d/%y}" for date in dates])
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setDefaultSectionSize(20)

        assignments = solution.get_assignments()
        metric_vals = [m.detail_metric(assignments) for m in metrics]
        for i, assigned in enumerate(solution.get_assignments()):
            assignment_widget = QtWidgets.QLabel(", ".join(sorted(assigned)))
            self.setCellWidget(i, 0, assignment_widget)
            # TODO no coverage shown, fix
            coverage_widget = QtWidgets.QLabel(solution._coverage_msg_for(i, True))
            self.setCellWidget(i, 1, coverage_widget)
            for j, metric in enumerate(metric_vals):
                self.setCellWidget(i, 2 + j, QtWidgets.QLabel(metric[i]))


class ScheduleResult(QtWidgets.QWidget):
    def __init__(self, project: Project, solution: Solution) -> None:
        super().__init__()

        layout = QtWidgets.QGridLayout(self)
        self.summary = ResultSummary(project, solution)
        layout.addWidget(self.summary, 0, 0, 1, 2)
        resident_header = QtWidgets.QLabel("Resident Breakdown")
        layout.addWidget(resident_header, 1, 0)
        self.resident_summary = ResultResidentSummary(project, solution)
        layout.addWidget(self.resident_summary, 2, 0)
        schedule_header = QtWidgets.QLabel("Schedule")
        layout.addWidget(schedule_header, 1, 1)
        self.schedule = ResultDetail(project, solution)
        layout.addWidget(self.schedule, 2, 1)


class EditProjectWidget(QtWidgets.QWidget):
    def __init__(self, project_path: str, project: Project) -> None:
        super().__init__()

        self.project_path = Path(project_path)
        self.project = project

        self.setWindowTitle(self.project_path.name)

        availability_button = QtWidgets.QPushButton("Edit Availability")

        self.constraints_header = ConstraintsHeaderWidget(self.project, self)
        self.constraints = ConstraintsWidget(self.project, self)
        self.objectives_header = ObjectivesHeaderWidget()
        self.objectives = ObjectivesWidget(self.project, self)

        self.generate_button = QtWidgets.QPushButton("Generate schedule")

        self._layout = QtWidgets.QGridLayout(self)
        self._layout.addWidget(availability_button, 0, 0, 1, 2)
        self._layout.addWidget(self.constraints_header, 1, 0)
        self._layout.addWidget(self.constraints, 2, 0)
        self._layout.addWidget(self.objectives_header, 1, 1)
        self._layout.addWidget(self.objectives, 2, 1)
        self._layout.addWidget(self.generate_button, 3, 0, 1, 2)

        availability_button.clicked.connect(self.edit_availability_clicked)
        self.generate_button.clicked.connect(self.generate_clicked)

        self.result = None

    def update_project(self, project: Project) -> None:
        old_constraints = self.constraints
        self.constraints = ConstraintsWidget(self.project, self)
        old = self._layout.replaceWidget(old_constraints, self.constraints)
        old.widget().deleteLater()

        old_objectives = self.objectives
        self.objectives = ObjectivesWidget(self.project, self)
        old = self._layout.replaceWidget(old_objectives, self.objectives)
        old.widget().deleteLater()

    @QtCore.Slot()
    def edit_availability_clicked(self) -> None:
        # TODO implement
        pass

    def _set_result(self, new_result: QtWidgets.QWidget) -> None:
        if self.result is None:
            self.result = new_result
            self._layout.addWidget(self.result, 4, 0, 1, 2)
        else:
            old_result = self.result
            self.result = new_result
            old = self._layout.replaceWidget(old_result, self.result)
            old.widget().deleteLater()

    @QtCore.Slot()
    def generate_clicked(self) -> None:
        self.generate_button.setEnabled(False)
        self._set_result(QtWidgets.QLabel("Loading..."))
        solver = SolveThread(self.project, self)
        solver.done_signal.connect(self.result_ready)
        solver.start()

    @QtCore.Slot()
    def result_ready(self, result: SolveResult) -> None:
        self.generate_button.setEnabled(True)
        if isinstance(result.result, str):
            self._set_result(QtWidgets.QLabel("Failed"))
            # TODO attempt to generate hint to source of failure
            print("Failed")
        else:
            self._set_result(ScheduleResult(self.project, result.result))
