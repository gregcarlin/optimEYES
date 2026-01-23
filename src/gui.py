import sys
import json
from typing import override
from datetime import timedelta
from pathlib import Path

from PySide6 import QtCore, QtWidgets, QtGui

from structs.project import Project


class AlertMessage(QtWidgets.QMessageBox):
    def __init__(self, text: str, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setText(text)


def show_alert(message: str, parent: QtWidgets.QWidget) -> None:
    alert = AlertMessage(message, parent)
    alert.show()


class OpenProjectDialog(QtWidgets.QFileDialog):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__()

        self.setNameFilter("*.json")
        self.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)


class ConstraintsHeaderWidget(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()

        constraints_label = QtWidgets.QLabel(
            "Constraints", alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )
        constraints_label.setContentsMargins(0, 4, 0, 0)
        new_constraint_button = QtWidgets.QPushButton("+")
        new_constraint_button.setFixedWidth(20)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(constraints_label)
        layout.addWidget(new_constraint_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)


class ConstraintsWidget(QtWidgets.QTableWidget):
    def __init__(self, project: Project) -> None:
        super().__init__()

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)

        self.setRowCount(len(project.constraints))
        self.setColumnCount(1)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        for i, constraint in enumerate(project.constraints):
            text = QtWidgets.QLabel(constraint.description())
            text.setMargin(5)
            text.setWordWrap(True)
            self.setCellWidget(i, 0, text)

    @override
    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(400, 600)


class EditProjectWidget(QtWidgets.QWidget):
    def __init__(self, project_path: str, project: Project) -> None:
        super().__init__(None, QtCore.Qt.WindowType.Window)

        self.project_path = Path(project_path)
        self.project = project

        self.setWindowTitle(self.project_path.name)

        availability_button = QtWidgets.QPushButton("Edit Availability")

        self.constraints_header = ConstraintsHeaderWidget()
        self.constraints = ConstraintsWidget(self.project)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(availability_button)
        layout.addWidget(self.constraints_header)
        layout.addWidget(self.constraints)

        availability_button.clicked.connect(self.edit_availability_clicked)

    @QtCore.Slot()
    def edit_availability_clicked(self):
        # TODO implement
        pass


class IntroWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        text = QtWidgets.QLabel(
            "Welcome to OptimEYES", alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        new_button = QtWidgets.QPushButton("New Project")
        open_button = QtWidgets.QPushButton("Open Existing")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(text)
        layout.addWidget(new_button)
        layout.addWidget(open_button)

        new_button.clicked.connect(self.new_project_clicked)
        open_button.clicked.connect(self.open_project_clicked)

    @QtCore.Slot()
    def new_project_clicked(self):
        # TODO implement (needs availability builder)
        pass

    @QtCore.Slot()
    def open_project_clicked(self):
        dialog = OpenProjectDialog(self)
        result = dialog.exec()
        if not result:
            return

        selected_file = dialog.selectedFiles()[0]
        try:
            project = Project.read_from_file(selected_file)
            # Make it a property of self so it doesn't get garbage collected
            self.edit = EditProjectWidget(selected_file, project)
            self.edit.show()
            self.close()
            center_on_screen(self.edit)
        except Exception as e:
            print(e)
            show_alert(f"Unable to read file {selected_file}", self)


class AvailabilityWidget(QtWidgets.QTableWidget):
    def __init__(self, project: Project) -> None:
        super().__init__()
        num_days = (
            0
            if project.availability == []
            else len(project.availability[0].availability)
        )

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.setRowCount(0 if project.availability == [] else num_days)
        self.setColumnCount(len(project.availability))
        self.setHorizontalHeaderLabels(
            [resident.name for resident in project.availability]
        )
        self.setVerticalHeaderLabels(
            []
            if project.availability == []
            else [
                f"{project.start_date + timedelta(days=i):%a %m-%d}"
                for i in range(num_days)
            ]
        )
        for resident_index, resident in enumerate(project.availability):
            for day_index, (available, va) in enumerate(
                zip(resident.availability, resident.va)
            ):
                check = QtWidgets.QCheckBox()
                check.setChecked(available != 0)

                # Magic needed to center check box
                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(widget)
                layout.addWidget(check)
                layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)

                if va != 0:
                    p = widget.palette()
                    p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(255, 0, 0))
                    widget.setAutoFillBackground(True)
                    widget.setPalette(p)

                self.setCellWidget(day_index, resident_index, widget)

        # Set all columns to the width of the longest resident's name
        self.resizeColumnsToContents()
        column_width = max(
            self.columnWidth(i) for i in range(len(project.availability))
        )
        for i in range(len(project.availability)):
            self.setColumnWidth(i, column_width)


def center_on_screen(widget: QtWidgets.QWidget) -> None:
    # Widget must already be visible
    screen_geometry = widget.screen().availableGeometry()
    x = int((screen_geometry.width() - widget.width()) / 2)
    y = int((screen_geometry.height() - widget.height()) / 2)
    widget.move(x, y)


def main() -> int:
    app = QtWidgets.QApplication([])
    app.setApplicationName("OptimEYES")
    app.setApplicationDisplayName("OptimEYES")

    if len(sys.argv) >= 2:
        # Convenience for running program directly in edit mode
        project_path = sys.argv[1]
        project = Project.read_from_file(project_path)
        edit = EditProjectWidget(project_path, project)
        edit.show()
        center_on_screen(edit)
    else:
        intro = IntroWidget()
        intro.show()
        center_on_screen(intro)

    """
    availability_widget = AvailabilityWidget(project)
    availability_widget.resize(800, 600)
    availability_widget.show()
    """

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
