import sys
import json
from datetime import timedelta

from PySide6 import QtCore, QtWidgets, QtGui
from cli import main as cli_main

from project import Project


"""
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello world", alignment=QtCore.Qt.AlignCenter)

        self.layout2 = QtWidgets.QVBoxLayout(self)
        self.layout2.addWidget(self.text)
        self.layout2.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText("loading num...")
        solution = cli_main()[0]
        v = solution.solution.get_objective_value()
        self.text.setText(f"the num is: {v}")
"""


def make_availability_widget(project: Project) -> QtWidgets.QTableWidget:
    num_days = (
        0 if project.availability == [] else len(project.availability[0].availability)
    )

    table = QtWidgets.QTableWidget()
    table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
    table.setRowCount(0 if project.availability == [] else num_days)
    table.setColumnCount(len(project.availability))
    table.setHorizontalHeaderLabels(
        [resident.name for resident in project.availability]
    )
    table.setVerticalHeaderLabels(
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

            table.setCellWidget(day_index, resident_index, widget)

    # Set all columns to the width of the longest resident's name
    table.resizeColumnsToContents()
    column_width = max(table.columnWidth(i) for i in range(len(project.availability)))
    for i in range(len(project.availability)):
        table.setColumnWidth(i, column_width)

    return table


def main() -> int:
    app = QtWidgets.QApplication([])
    app.setApplicationName("OptimEYES")
    app.setApplicationDisplayName("OptimEYES")

    with open("test_project.json", "r") as project_file:
        project_data = json.loads(project_file.read())
        project = Project.deserialize(project_data)

    availability_widget = make_availability_widget(project)
    availability_widget.resize(800, 600)
    availability_widget.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
