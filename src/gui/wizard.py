from typing import override, cast
from datetime import date, timedelta
from dataclasses import dataclass
from collections import defaultdict

from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QCalendarWidget,
    QLabel,
    QRadioButton,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDateEdit,
    QWidget,
    QCheckBox,
    QScrollArea,
)
from PySide6.QtCore import SignalInstance, Qt, QDate
from PySide6.QtGui import QPixmap

from typeutil import none_throws
from dateutil import Weekday


FIRST_PAGE_ID = 0
BUDDY_PAGE_ID = 5
RESIDENTS_PAGE_ID = 10
BLOCK_PAGE_ID = 20

START_FIELD = "start"
END_FIELD = "end"
BUDDY_DISABLED_FIELD = "buddy_disabled"
BUDDY_START_FIELD = "buddy_start"
BUDDY_END_FIELD = "buddy_end"


class DatePicker(QCalendarWidget):
    def __init__(self, complete_signal: SignalInstance) -> None:
        super().__init__()

        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.selectionChanged.connect(complete_signal)

    def selectedPythonDate(self) -> date:
        return cast(date, self.selectedDate().toPython())


class CompactDatePicker(QDateEdit):
    def __init__(self) -> None:
        super().__init__()

        self.setCalendarPopup(True)

    def get_date_as_python(self) -> date:
        result = self.date().toPython()
        assert isinstance(result, date)
        return result


class StartEndPage(QWizardPage):
    def __init__(self, question: str, start_field: str, end_field: str) -> None:
        super().__init__()

        self.start_field = start_field
        self.end_field = end_field

        self._layout = QGridLayout(self)
        date_description = QLabel(question)
        self._layout.addWidget(date_description, 0, 0, 1, 2)
        start_label = QLabel("Start")
        self._layout.addWidget(start_label, 1, 0)
        self.start = DatePicker(self.completeChanged)
        self._layout.addWidget(self.start, 1, 1)
        end_label = QLabel("End")
        self._layout.addWidget(end_label, 2, 0)
        self.end = DatePicker(self.completeChanged)
        self._layout.addWidget(self.end, 2, 1)

    def afterSetup(self) -> None:
        self.registerField(self.start_field, self.start, "selectedDate")
        self.registerField(self.end_field, self.end, "selectedDate")

    @override
    def isComplete(self) -> bool:
        return self.start.selectedPythonDate() < self.end.selectedPythonDate()


class DatesPage(StartEndPage):
    def __init__(self) -> None:
        super().__init__(
            "What is the first and last day to be OptimEYEsd? You cannot change this later.",
            START_FIELD,
            END_FIELD,
        )

        buddy_description = QLabel("Is there a buddy call period?")
        self._layout.addWidget(buddy_description, 3, 0, 1, 2)
        self.no = QRadioButton("No")
        self.no.setChecked(True)
        self._layout.addWidget(self.no, 4, 0)
        self.yes = QRadioButton("Yes")
        self._layout.addWidget(self.yes, 5, 0)

    @override
    def afterSetup(self) -> None:
        super().afterSetup()
        self.registerField(BUDDY_DISABLED_FIELD, self.no)

    @override
    def nextId(self) -> int:
        return RESIDENTS_PAGE_ID if self.no.isChecked() else BUDDY_PAGE_ID


class BuddyPage(StartEndPage):
    def __init__(self) -> None:
        super().__init__(
            "What is the first and last day of the buddy period?",
            BUDDY_START_FIELD,
            BUDDY_END_FIELD,
        )

    @override
    def initializePage(self) -> None:
        super().initializePage()

        overall_start = self.field(START_FIELD)
        overall_end = self.field(END_FIELD)
        self.start.setMinimumDate(overall_start)
        self.start.setMaximumDate(overall_end)
        self.end.setMinimumDate(overall_start)
        self.end.setMaximumDate(overall_end)

    @override
    def nextId(self) -> int:
        return RESIDENTS_PAGE_ID

    @override
    def isComplete(self) -> bool:
        overall_start = cast(date, self.field(START_FIELD).toPython())
        overall_end = cast(date, self.field(END_FIELD).toPython())
        return (
            super().isComplete()
            and self.start.selectedPythonDate() >= overall_start
            and self.end.selectedPythonDate() <= overall_end
        )


class PGYSpinBox(QSpinBox):
    def __init__(self) -> None:
        super().__init__()

        self.setRange(2, 4)


class ResidentsPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QGridLayout(self)
        self._layout.addWidget(QLabel("Name"), 0, 0)
        self._layout.addWidget(QLabel("PGY"), 0, 1)

        self.add_btn = QPushButton("Add")
        self.add_btn.setAutoDefault(False)
        self.add_btn.clicked.connect(self.addRow)
        self._layout.addWidget(self.add_btn, 1, 0)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setAutoDefault(False)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self.removeRow)
        self._layout.addWidget(self.remove_btn, 1, 1)

        self._layout.setColumnStretch(0, 1)
        self._layout.setColumnStretch(1, 1)

        self.row_count = 2
        self.addRow()

    def addRow(self) -> None:
        self._layout.removeWidget(self.add_btn)
        self._layout.removeWidget(self.remove_btn)

        line_edit = QLineEdit()
        line_edit.textChanged.connect(self.completeChanged)
        self._layout.addWidget(line_edit, self.row_count - 1, 0)
        pgy_edit = PGYSpinBox()
        self._layout.addWidget(pgy_edit, self.row_count - 1, 1)

        self._layout.addWidget(self.add_btn, self.row_count, 0)
        self._layout.addWidget(self.remove_btn, self.row_count, 1)

        self.row_count += 1
        if self.row_count > 3:
            self.remove_btn.setEnabled(True)
        self.completeChanged.emit()

    def removeRow(self) -> None:
        self._layout.removeWidget(self.add_btn)
        self._layout.removeWidget(self.remove_btn)

        name = none_throws(self._layout.itemAtPosition(self.row_count - 2, 0)).widget()
        pgy = none_throws(self._layout.itemAtPosition(self.row_count - 2, 1)).widget()
        name.hide()
        pgy.hide()
        self._layout.removeWidget(name)
        self._layout.removeWidget(pgy)

        self._layout.addWidget(self.add_btn, self.row_count - 2, 0)
        self._layout.addWidget(self.remove_btn, self.row_count - 2, 1)

        self.row_count -= 1
        if self.row_count <= 3:
            # Disable button so last row can't be removed
            self.remove_btn.setEnabled(False)
        self.completeChanged.emit()

    @override
    def nextId(self) -> int:
        return BLOCK_PAGE_ID

    def get_residents(self) -> list[tuple[str, int]]:
        result = []
        for i in range(1, self.row_count - 1):
            name_widget = none_throws(self._layout.itemAtPosition(i, 0)).widget()
            assert isinstance(name_widget, QLineEdit)
            name = name_widget.text().strip()
            pgy_widget = none_throws(self._layout.itemAtPosition(i, 1)).widget()
            assert isinstance(pgy_widget, QSpinBox)
            pgy = pgy_widget.value()
            result.append((name, pgy))
        return result

    @override
    def isComplete(self) -> bool:
        return all(name for name, _ in self.get_residents())


class MultiResidentSelectWidget(QWidget):
    def __init__(self, residents: list[str], complete_signal: SignalInstance) -> None:
        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)
        layout = QHBoxLayout(self)
        self.checks: dict[str, QCheckBox] = {}
        for resident in residents:
            check = QCheckBox()
            check.checkStateChanged.connect(complete_signal)
            layout.addWidget(check)
            self.checks[resident] = check
            layout.addWidget(QLabel(resident))
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def selected_residents(self) -> list[str]:
        return [name for name, checkbox in self.checks.items() if checkbox.isChecked()]


@dataclass
class BlockData:
    start: date
    end: date
    assignments: dict[Weekday, list[str]]


class BlockPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()

        self.num_blocks = 0

        self.inner = QWidget()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.inner)
        self.scroll_area.setWidgetResizable(True)
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.scroll_area)

        self._layout = QGridLayout(self.inner)

        self.add_btn = QPushButton("Add")
        self.add_btn.setAutoDefault(False)
        self.add_btn.clicked.connect(self.addBlock)
        self._layout.addWidget(self.add_btn, 0, 0)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setAutoDefault(False)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self.removeBlock)
        self._layout.addWidget(self.remove_btn, 0, 1)

    def _get_date_bounds(self) -> tuple[QDate, QDate]:
        return self.field(START_FIELD), self.field(END_FIELD)

    def _get_residents(self) -> list[str]:
        wizard = self.wizard()
        assert isinstance(wizard, SetupWizard)
        residents = wizard.get_residents()
        return [name for name, _ in residents]

    def addBlock(self) -> None:
        overall_start, overall_end = self._get_date_bounds()
        resident_names = self._get_residents()

        self._layout.removeWidget(self.add_btn)
        self._layout.removeWidget(self.remove_btn)

        weekdays = Weekday.just_weekdays()
        start_row = self.num_blocks * (3 + len(weekdays))

        self._layout.addWidget(
            QLabel(f"Block {self.num_blocks + 1}"),
            start_row,
            0,
            1,
            2,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        self._layout.addWidget(QLabel("Block Start"), start_row + 1, 0)
        start = CompactDatePicker()
        start.setMinimumDate(overall_start)
        start.setMaximumDate(overall_end)
        start.userDateChanged.connect(self.completeChanged)
        self._layout.addWidget(start, start_row + 1, 1)
        self._layout.addWidget(QLabel("Block End"), start_row + 2, 0)
        end = CompactDatePicker()
        end.setMinimumDate(overall_start)
        end.setMaximumDate(overall_end)
        end.userDateChanged.connect(self.completeChanged)
        self._layout.addWidget(end, start_row + 2, 1)
        for i, weekday in enumerate(weekdays):
            self._layout.addWidget(QLabel(weekday.human_name()), start_row + 3 + i, 0)
            combo = MultiResidentSelectWidget(resident_names, self.completeChanged)
            self._layout.addWidget(combo, start_row + 3 + i, 1)

        self._layout.addWidget(self.add_btn, start_row + 3 + len(weekdays), 0)
        self._layout.addWidget(self.remove_btn, start_row + 3 + len(weekdays), 1)

        self.num_blocks += 1
        if self.num_blocks >= 2:
            self.remove_btn.setEnabled(True)
        self.completeChanged.emit()

    def widgetAt(self, row: int, col: int) -> QWidget:
        return none_throws(self._layout.itemAtPosition(row, col)).widget()

    def removeBlock(self) -> None:
        self._layout.removeWidget(self.add_btn)
        self._layout.removeWidget(self.remove_btn)

        weekdays = len(Weekday.just_weekdays())
        start_row = (self.num_blocks - 1) * (3 + weekdays)
        for i in range(3 + weekdays):
            left = self.widgetAt(start_row + i, 0)
            right = self.widgetAt(start_row + i, 1)
            left.hide()
            right.hide()
            self._layout.removeWidget(left)
            self._layout.removeWidget(right)

        self._layout.addWidget(self.add_btn, start_row, 0)
        self._layout.addWidget(self.remove_btn, start_row, 1)

        self.num_blocks -= 1
        if self.num_blocks <= 1:
            self.remove_btn.setEnabled(False)
        self.completeChanged.emit()

    @override
    def initializePage(self) -> None:
        super().initializePage()

        self.addBlock()

    @override
    def cleanupPage(self) -> None:
        super().cleanupPage()

        while self.num_blocks > 0:
            self.removeBlock()

    def _get_data(self) -> list[BlockData]:
        weekdays = len(Weekday.just_weekdays())

        result: list[BlockData] = []
        for block in range(self.num_blocks):
            start = self.widgetAt(block * (3 + weekdays) + 1, 1)
            assert isinstance(start, CompactDatePicker)
            end = self.widgetAt(block * (3 + weekdays) + 2, 1)
            assert isinstance(end, CompactDatePicker)
            assignments: dict[Weekday, list[str]] = {}
            for i, weekday in enumerate(Weekday.just_weekdays()):
                combo = self.widgetAt(block * (3 + weekdays) + 3 + i, 1)
                assert isinstance(combo, MultiResidentSelectWidget)
                assignments[weekday] = combo.selected_residents()
            result.append(
                BlockData(
                    start=start.get_date_as_python(),
                    end=end.get_date_as_python(),
                    assignments=assignments,
                )
            )

        return sorted(result, key=lambda block: block.start)

    @override
    def isComplete(self) -> bool:
        overall_qstart, overall_qend = self._get_date_bounds()
        overall_start = cast(date, overall_qstart.toPython())
        overall_end = cast(date, overall_qend.toPython())
        resident_names = self._get_residents()

        blocks = self._get_data()

        # At least one block
        if blocks == []:
            return False
        # Start and end matches overall bounds
        if blocks[0].start != overall_start:
            return False
        if blocks[-1].end != overall_end:
            return False

        for block in blocks:
            # All blocks are within bounds
            if block.start < overall_start or block.end > overall_end:
                return False
            # End is after start
            if block.start >= block.end:
                return False

        for block_a, block_b in zip(blocks[:-1], blocks[1:]):
            # Next block should start one day after previous block
            if block_b.start != block_a.end + timedelta(days=1):
                return False

        return super().isComplete()


class SetupWizard(QWizard):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("New Project")
        self.setOption(QWizard.WizardOption.NoCancelButton)
        self.setPixmap(
            QWizard.WizardPixmap.BackgroundPixmap, QPixmap("./eye-drawing-35.jpg")
        )

        dates_page = DatesPage()
        self.setPage(FIRST_PAGE_ID, dates_page)
        buddy_page = BuddyPage()
        self.setPage(BUDDY_PAGE_ID, buddy_page)
        self.residents_page = ResidentsPage()
        self.setPage(RESIDENTS_PAGE_ID, self.residents_page)
        self.setPage(BLOCK_PAGE_ID, BlockPage())
        dates_page.afterSetup()
        buddy_page.afterSetup()

    def get_residents(self) -> list[tuple[str, int]]:
        return self.residents_page.get_residents()
