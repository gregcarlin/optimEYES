from pathlib import Path
from typing import override, Any

from PySide6 import QtCore, QtWidgets, QtGui

from structs.project import Project
from gui.table import TableWidget, SectionHeaderWidget
from gui.common import center_on_screen, BinaryMessage
from gui.field import TextFieldEdit, DropDownEdit
from structs.field import (
    OptionField,
    TextInputField,
)

class ConstraintsHeaderWidget(SectionHeaderWidget):
    def __init__(self) -> None:
        super().__init__("Constraints")

    @QtCore.Slot()
    @override
    def add_new_clicked(self):
        # TODO implement
        pass


class ObjectivesHeaderWidget(SectionHeaderWidget):
    def __init__(self) -> None:
        super().__init__("Objectives")

    @QtCore.Slot()
    @override
    def add_new_clicked(self):
        # TODO implement
        pass

class EditConstraintWidget(QtWidgets.QWidget):
    def __init__(
        self, project: Project, constraint_index: int, root: "EditProjectWidget"
    ) -> None:
        super().__init__()

        self.project = project
        self.constraint_index = constraint_index
        self.root = root

        self.setWindowTitle("Edit Constraint")
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_clicked)

        layout = QtWidgets.QGridLayout(self)

        self.field_widgets: list[DropDownEdit | TextFieldEdit] = []
        fields = project.constraints[constraint_index].fields(self.project)
        for i, field in enumerate(fields):
            label = QtWidgets.QLabel(field.name)
            layout.addWidget(label, i, 0)
            match field:
                case OptionField():
                    edit = DropDownEdit(
                        field.allowed_value_labels(),
                        field.allowed_values.index(field.value),
                    )
                case TextInputField():
                    edit = TextFieldEdit(field, save_button)
                case _:
                    raise ValueError(f"Unknown field type: {field}")
            layout.addWidget(edit, i, 1)
            self.field_widgets.append(edit)

        layout.addWidget(save_button)

    @override
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        old_fields = self.project.constraints[self.constraint_index].fields(
            self.project
        )
        try:
            new_fields = self._rebuild_fields()
        except AssertionError:
            # Fields are dirty, and invalid
            new_fields = None
        if new_fields == old_fields:
            # Fields are unchanged, close
            self.root.setEnabled(True)
            event.accept()
        else:
            message = BinaryMessage("Discard unsaved changes?", self)
            result = message.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Discard:
                self.root.setEnabled(True)
                event.accept()
            else:
                event.ignore()

    @staticmethod
    def _rebuild_field(
        field: OptionField | TextInputField, widget: DropDownEdit | TextFieldEdit
    ) -> OptionField | TextInputField:
        if isinstance(field, OptionField):
            assert isinstance(widget, DropDownEdit)
            return field.parse(widget.currentIndex())
        else:
            assert isinstance(widget, TextFieldEdit)
            new_field = field.parse(widget.text())
            assert isinstance(new_field, TextInputField)
            return new_field

    def _rebuild_fields(self) -> tuple[Any, ...]:
        constraint = self.project.constraints[self.constraint_index]
        old_fields = constraint.fields(self.project)
        return tuple(
            EditConstraintWidget._rebuild_field(old_field, widget)
            for old_field, widget in zip(old_fields, self.field_widgets)
        )

    def save_clicked(self) -> None:
        new_fields = self._rebuild_fields()
        constraint = self.project.constraints[self.constraint_index]
        new_constraint = constraint.from_fields(new_fields)
        self.project.constraints[self.constraint_index] = new_constraint
        self.root.update_project(self.project)
        self.close()


class ConstraintsWidget(TableWidget):
    def __init__(self, project: Project, parent: "EditProjectWidget") -> None:
        super().__init__(project, len(project.constraints), 2)

        self.edit_parent = parent

        for i, constraint in enumerate(project.constraints):
            self.setRow(i, constraint.description(), constraint.fields(self.project) != ())

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
            self.setRow(i, objective.description(), False)

    @override
    def edit_clicked(self, index: int) -> None:
        pass # TODO

    @override
    def delete_clicked(self, index: int) -> None:
        self.project.objectives.pop(index)
        self.edit_parent.update_project(self.project)

class EditProjectWidget(QtWidgets.QWidget):
    def __init__(self, project_path: str, project: Project) -> None:
        super().__init__()

        self.project_path = Path(project_path)
        self.project = project

        self.setWindowTitle(self.project_path.name)

        availability_button = QtWidgets.QPushButton("Edit Availability")

        self.constraints_header = ConstraintsHeaderWidget()
        self.constraints = ConstraintsWidget(self.project, self)
        self.objectives_header = ObjectivesHeaderWidget()
        self.objectives = ObjectivesWidget(self.project, self)

        self._layout = QtWidgets.QGridLayout(self)
        self._layout.addWidget(availability_button, 0, 0, 1, 2)
        self._layout.addWidget(self.constraints_header, 1, 0)
        self._layout.addWidget(self.constraints, 2, 0)
        self._layout.addWidget(self.objectives_header, 1, 1)
        self._layout.addWidget(self.objectives, 2, 1)

        availability_button.clicked.connect(self.edit_availability_clicked)

    def update_project(self, project: Project) -> None:
        old_constraints = self.constraints
        self.constraints = ConstraintsWidget(self.project, self)
        self._layout.replaceWidget(old_constraints, self.constraints)

        old_objectives = self.objectives
        self.objectives = ObjectivesWidget(self.project, self)
        self._layout.replaceWidget(old_objectives, self.objectives)

    @QtCore.Slot()
    def edit_availability_clicked(self):
        # TODO implement
        pass

