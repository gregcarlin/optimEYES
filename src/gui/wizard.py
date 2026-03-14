from typing import override, cast
from datetime import date

from PySide6.QtWidgets import QWizard, QWizardPage, QGridLayout, QCalendarWidget, QLabel
from PySide6.QtCore import SignalInstance


class DatePicker(QCalendarWidget):
    def __init__(self, complete_signal: SignalInstance) -> None:
        super().__init__()

        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.selectionChanged.connect(complete_signal)

    def selectedPythonDate(self) -> date:
        return cast(date, self.selectedDate().toPython())


class DatesPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()

        layout = QGridLayout(self)
        date_description = QLabel(
            "What is the first and last date to be OptimEYEsd? You cannot change this later."
        )
        layout.addWidget(date_description, 0, 0, 1, 2)
        start_label = QLabel("Start")
        layout.addWidget(start_label, 1, 0)
        self.start = DatePicker(self.completeChanged)
        layout.addWidget(self.start, 1, 1)
        self.registerField("start*", self.start)
        end_label = QLabel("End")
        layout.addWidget(end_label, 2, 0)
        self.end = DatePicker(self.completeChanged)
        self.registerField("end*", self.end)
        layout.addWidget(self.end, 2, 1)

    @override
    def isComplete(self) -> bool:
        return self.start.selectedPythonDate() < self.end.selectedPythonDate()


class SetupWizard(QWizard):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("New Project")
        self.setOption(QWizard.WizardOption.NoCancelButton)
        self.addPage(DatesPage())
