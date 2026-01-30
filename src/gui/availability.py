from datetime import timedelta

from PySide6 import QtCore, QtWidgets, QtGui

from structs.project import Project

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
