from PySide6 import QtCore, QtWidgets

from structs.project import Project
from gui.common import center_on_screen, show_alert
from gui.project import EditProjectWidget


class OpenProjectDialog(QtWidgets.QFileDialog):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__()

        self.setNameFilter("*.json")
        self.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)


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


def main(args: list[str]) -> int:
    app = QtWidgets.QApplication([])
    app.setApplicationName("OptimEYES")
    app.setApplicationDisplayName("OptimEYES")

    if len(args) >= 2:
        # Convenience for running program directly in edit mode
        project_path = args[1]
        project = Project.read_from_file(project_path)
        edit = EditProjectWidget(project_path, project)
        edit.show()
        center_on_screen(edit)
    else:
        intro = IntroWidget()
        intro.show()
        center_on_screen(intro)

    return app.exec()

