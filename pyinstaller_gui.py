import sys
import os
import shlex
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QGroupBox,
    QRadioButton, QCheckBox, QPlainTextEdit, QButtonGroup,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QTextCharFormat


STYLESHEET = """
QMainWindow, QWidget {
    background-color: #F3F3F3;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    color: #1E1E1E;
}
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: #1E1E1E;
}
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    padding: 5px 8px;
    selection-background-color: #007ACC;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #007ACC;
}
QPushButton {
    background-color: #E5E5E5;
    border: 1px solid #C0C0C0;
    padding: 5px 18px;
    font-size: 13px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #D8D8D8;
    border-color: #007ACC;
}
QPushButton:pressed {
    background-color: #C8C8C8;
}
QPushButton:disabled {
    color: #A0A0A0;
    background-color: #ECECEC;
    border-color: #D8D8D8;
}
QPushButton#buildBtn {
    background-color: #007ACC;
    color: #FFFFFF;
    border: none;
    font-size: 14px;
    font-weight: 600;
    padding: 8px 36px;
    min-height: 28px;
}
QPushButton#buildBtn:hover {
    background-color: #005FA3;
}
QPushButton#buildBtn:pressed {
    background-color: #004578;
}
QPushButton#buildBtn:disabled {
    background-color: #80BDE5;
}
QRadioButton, QCheckBox {
    spacing: 6px;
    font-size: 13px;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 15px; height: 15px;
}
QPlainTextEdit {
    background-color: #1E1E1E;
    color: #DCDCDC;
    border: 1px solid #D0D0D0;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 12px;
    selection-background-color: #264F78;
}
QLabel#statusLabel {
    font-size: 13px;
    font-weight: 600;
    padding: 2px 0;
}
"""


def _pip_exe() -> str:
    """Путь к pip текущего интерпретатора."""
    scripts = os.path.dirname(sys.executable)
    pip = os.path.join(scripts, "pip.exe" if sys.platform == "win32" else "pip")
    if os.path.isfile(pip):
        return pip
    return pip


def _popen_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class BuildWorker(QThread):
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, py_file: str, command: list[str], cwd: str | None = None):
        super().__init__()
        self.py_file = py_file
        self.command = command
        self.cwd = cwd

    def _run_process(self, cmd: list[str], label: str) -> int:
        self.log_signal.emit(f"[{label}] > {' '.join(cmd)}\n")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=self.cwd,
                creationflags=_popen_flags(),
            )
            for line in proc.stdout:
                self.log_signal.emit(line.rstrip("\n"))
            proc.wait()
            return proc.returncode
        except FileNotFoundError:
            self.error_signal.emit(f"{label}: исполняемый файл не найден — {cmd[0]}")
            return -1
        except Exception as e:
            self.error_signal.emit(f"{label}: {e}")
            return -1

    def _ensure_pyinstaller(self) -> bool:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--version"],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                creationflags=_popen_flags(),
            )
            if r.returncode == 0:
                ver = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "ok"
                self.log_signal.emit(f"PyInstaller уже установлен (v{ver})\n")
                return True
        except Exception:
            pass

        self.log_signal.emit("PyInstaller не найден — устанавливаю автоматически…\n")
        code = self._run_process(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            "pip install",
        )
        if code != 0:
            self.error_signal.emit(
                "Не удалось установить PyInstaller. "
                "Проверьте подключение к интернету и права доступа."
            )
            return False
        self.log_signal.emit("\nPyInstaller успешно установлен.\n")
        return True

    def run(self):
        if not self._ensure_pyinstaller():
            self.finished_signal.emit(-1)
            return

        code = self._run_process(self.command, "PyInstaller")
        self.finished_signal.emit(code)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyInstaller Builder")
        self.setMinimumSize(720, 780)
        self.resize(780, 860)
        self.worker: BuildWorker | None = None
        self._build_ui()
        self._connect_signals()
        self._update_build_btn()

    # ── UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # Input
        grp_input = QGroupBox("Исходный файл")
        h = QHBoxLayout(grp_input)
        h.setContentsMargins(10, 8, 10, 8)
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Путь к .py файлу…")
        self.input_path.setReadOnly(True)
        btn_browse = QPushButton("Обзор…")
        btn_browse.setFixedWidth(90)
        btn_browse.clicked.connect(self._browse_input)
        h.addWidget(self.input_path)
        h.addWidget(btn_browse)
        root.addWidget(grp_input)

        # Build Settings
        grp_build = QGroupBox("Build Settings")
        g = QVBoxLayout(grp_build)
        g.setContentsMargins(10, 8, 10, 8)
        g.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Имя выходного файла:"))
        self.output_name = QLineEdit()
        self.output_name.setPlaceholderText("my_app")
        row1.addWidget(self.output_name)
        g.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Директория сохранения:"))
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("По умолчанию — рядом с .py")
        self.output_dir.setReadOnly(True)
        btn_dir = QPushButton("Обзор…")
        btn_dir.setFixedWidth(90)
        btn_dir.clicked.connect(self._browse_output_dir)
        row2.addWidget(self.output_dir)
        row2.addWidget(btn_dir)
        g.addLayout(row2)
        root.addWidget(grp_build)

        # Build Mode + Console
        h_mc = QHBoxLayout()
        h_mc.setSpacing(8)

        grp_mode = QGroupBox("Build Mode")
        vm = QVBoxLayout(grp_mode)
        vm.setContentsMargins(10, 8, 10, 8)
        self.radio_onefile = QRadioButton("Onefile (один .exe)")
        self.radio_onedir = QRadioButton("Onedir (папка)")
        self.radio_onefile.setChecked(True)
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.radio_onefile)
        self._mode_group.addButton(self.radio_onedir)
        vm.addWidget(self.radio_onefile)
        vm.addWidget(self.radio_onedir)
        h_mc.addWidget(grp_mode)

        grp_console = QGroupBox("Console Options")
        vc = QVBoxLayout(grp_console)
        vc.setContentsMargins(10, 8, 10, 8)
        self.check_console = QRadioButton("Консоль (--console)")
        self.check_windowed = QRadioButton("Без консоли (--windowed)")
        self.check_console.setChecked(True)
        self._console_group = QButtonGroup(self)
        self._console_group.addButton(self.check_console)
        self._console_group.addButton(self.check_windowed)
        vc.addWidget(self.check_console)
        vc.addWidget(self.check_windowed)
        h_mc.addWidget(grp_console)
        root.addLayout(h_mc)

        # Icon
        grp_icon = QGroupBox("Icon Settings")
        hi = QHBoxLayout(grp_icon)
        hi.setContentsMargins(10, 8, 10, 8)
        self.icon_path = QLineEdit()
        self.icon_path.setPlaceholderText("Путь к .ico файлу (необязательно)")
        self.icon_path.setReadOnly(True)
        btn_icon = QPushButton("Обзор…")
        btn_icon.setFixedWidth(90)
        btn_icon.clicked.connect(self._browse_icon)
        hi.addWidget(self.icon_path)
        hi.addWidget(btn_icon)
        root.addWidget(grp_icon)

        # Advanced
        grp_adv = QGroupBox("Advanced Settings")
        va = QVBoxLayout(grp_adv)
        va.setContentsMargins(10, 8, 10, 8)
        va.addWidget(QLabel("Дополнительные аргументы PyInstaller:"))
        self.extra_args = QLineEdit()
        self.extra_args.setPlaceholderText("--hidden-import=module --add-data=src;dst …")
        va.addWidget(self.extra_args)
        root.addWidget(grp_adv)

        # Execution
        exec_row = QHBoxLayout()
        exec_row.setSpacing(12)
        self.btn_build = QPushButton("Собрать")
        self.btn_build.setObjectName("buildBtn")
        self.btn_build.setFixedWidth(160)
        self.status_label = QLabel("Готов")
        self.status_label.setObjectName("statusLabel")
        exec_row.addWidget(self.btn_build)
        exec_row.addWidget(self.status_label)
        exec_row.addStretch()
        root.addLayout(exec_row)

        # Log
        grp_log = QGroupBox("Output")
        vl = QVBoxLayout(grp_log)
        vl.setContentsMargins(4, 4, 4, 4)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(180)
        self.log_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vl.addWidget(self.log_view)
        root.addWidget(grp_log, stretch=1)

    # ── Signals ─────────────────────────────────────────────────────
    def _connect_signals(self):
        self.btn_build.clicked.connect(self._start_build)
        self.input_path.textChanged.connect(self._update_build_btn)

    def _update_build_btn(self):
        self.btn_build.setEnabled(bool(self.input_path.text().strip()))

    # ── Browse dialogs ──────────────────────────────────────────────
    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Python-файл", "", "Python Files (*.py *.pyw)"
        )
        if path:
            self.input_path.setText(path)
            if not self.output_name.text():
                self.output_name.setText(
                    os.path.splitext(os.path.basename(path))[0]
                )

    def _browse_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите директорию")
        if d:
            self.output_dir.setText(d)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите иконку", "", "Icon Files (*.ico)"
        )
        if path:
            self.icon_path.setText(path)

    # ── Build ───────────────────────────────────────────────────────
    def _build_command(self) -> list[str]:
        cmd = [sys.executable, "-m", "PyInstaller"]
        cmd.append("--onefile" if self.radio_onefile.isChecked() else "--onedir")
        cmd.append("--console" if self.check_console.isChecked() else "--windowed")

        name = self.output_name.text().strip()
        if name:
            cmd += ["--name", name]

        dist = self.output_dir.text().strip()
        if dist:
            cmd += ["--distpath", dist]

        icon = self.icon_path.text().strip()
        if icon:
            cmd += ["--icon", icon]

        extra = self.extra_args.text().strip()
        if extra:
            cmd += shlex.split(extra)

        cmd.append(self.input_path.text().strip())
        return cmd

    def _set_ui_locked(self, locked: bool):
        for w in (
            self.btn_build, self.input_path, self.output_name,
            self.output_dir, self.icon_path, self.extra_args,
            self.radio_onefile, self.radio_onedir,
            self.check_console, self.check_windowed,
        ):
            w.setEnabled(not locked)
        if not locked:
            self._update_build_btn()

    def _set_status(self, text: str, color: str = "#1E1E1E"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 600;")

    def _start_build(self):
        self.log_view.clear()
        cmd = self._build_command()
        self._set_status("⏳ Выполняется…", "#E8A317")
        self._set_ui_locked(True)

        src = self.input_path.text().strip()
        self.worker = BuildWorker(src, cmd, cwd=os.path.dirname(src) or None)
        self.worker.log_signal.connect(self._log)
        self.worker.error_signal.connect(self._log_error)
        self.worker.finished_signal.connect(self._build_finished)
        self.worker.start()

    def _log(self, text: str):
        self.log_view.appendPlainText(text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _log_error(self, text: str):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#F44747"))
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _build_finished(self, code: int):
        self._set_ui_locked(False)
        if code == 0:
            self._set_status("✅ Успешно", "#16825D")
            self._log("\n✅ Сборка завершена успешно.")
        else:
            self._set_status("❌ Ошибка", "#D32F2F")
            self._log_error(f"\n❌ Сборка завершилась с кодом {code}.")
        self.worker = None


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()