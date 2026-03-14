from typing import override, cast
from datetime import date

from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QGridLayout,
    QCalendarWidget,
    QLabel,
    QRadioButton,
)
from PySide6.QtCore import SignalInstance
from PySide6.QtGui import QPixmap


FIRST_PAGE_ID = 0
BUDDY_PAGE_ID = 5
BLOCK_PAGE_ID = 10


class DatePicker(QCalendarWidget):
    def __init__(self, complete_signal: SignalInstance) -> None:
        super().__init__()

        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.selectionChanged.connect(complete_signal)

    def selectedPythonDate(self) -> date:
        return cast(date, self.selectedDate().toPython())


class StartEndPage(QWizardPage):
    def __init__(self, question: str, start_field: str, end_field: str) -> None:
        super().__init__()

        self._layout = QGridLayout(self)
        date_description = QLabel(question)
        self._layout.addWidget(date_description, 0, 0, 1, 2)
        start_label = QLabel("Start")
        self._layout.addWidget(start_label, 1, 0)
        self.start = DatePicker(self.completeChanged)
        self._layout.addWidget(self.start, 1, 1)
        self.registerField(start_field, self.start)
        end_label = QLabel("End")
        self._layout.addWidget(end_label, 2, 0)
        self.end = DatePicker(self.completeChanged)
        self.registerField(end_field, self.end)
        self._layout.addWidget(self.end, 2, 1)

    @override
    def isComplete(self) -> bool:
        return self.start.selectedPythonDate() < self.end.selectedPythonDate()


class BuddyPage(StartEndPage):
    def __init__(self) -> None:
        super().__init__(
            "What is the first and last day of the buddy period?",
            "buddy_start*",
            "buddy_end*",
        )

    @override
    def nextId(self) -> int:
        return BLOCK_PAGE_ID


class DatesPage(StartEndPage):
    def __init__(self) -> None:
        super().__init__(
            "What is the first and last day to be OptimEYEsd? You cannot change this later.",
            "start*",
            "end*",
        )

        buddy_description = QLabel("Is there a buddy call period?")
        self._layout.addWidget(buddy_description, 3, 0, 1, 2)
        self.no = QRadioButton("No")
        self.no.setChecked(True)
        self._layout.addWidget(self.no, 4, 0)
        self.yes = QRadioButton("Yes")
        self._layout.addWidget(self.yes, 5, 0)

    @override
    def nextId(self) -> int:
        return BLOCK_PAGE_ID if self.no.isChecked() else BUDDY_PAGE_ID


class BlockPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()


class SetupWizard(QWizard):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("New Project")
        self.setOption(QWizard.WizardOption.NoCancelButton)
        self.setPixmap(
            QWizard.WizardPixmap.BackgroundPixmap, QPixmap("./eye-drawing-35.jpg")
        )

        self.setPage(FIRST_PAGE_ID, DatesPage())
        self.setPage(BUDDY_PAGE_ID, BuddyPage())
        self.setPage(BLOCK_PAGE_ID, BlockPage())
