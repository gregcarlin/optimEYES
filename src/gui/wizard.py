from typing import override

from PySide6.QtWidgets import QWizard, QWizardPage, QGridLayout, QCalendarWidget, QLabel


class DatePicker(QCalendarWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )


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
        start = DatePicker()
        layout.addWidget(start, 1, 1)
        end_label = QLabel("End")
        layout.addWidget(end_label, 2, 0)
        end = DatePicker()
        layout.addWidget(end, 2, 1)


class SetupWizard(QWizard):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("New Project")
        self.setOption(QWizard.WizardOption.NoCancelButton)
        self.addPage(DatesPage())
