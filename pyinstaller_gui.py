import sys
import os
import ast
import shlex
import shutil
import tempfile
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QGroupBox,
    QRadioButton, QPlainTextEdit, QButtonGroup, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QIcon


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
QRadioButton {
    spacing: 6px;
    font-size: 13px;
}
QRadioButton::indicator {
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

STDLIB_MODULES: set[str] = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
    "atexit", "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
    "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code",
    "codecs", "codeop", "collections", "colorsys", "compileall", "concurrent",
    "configparser", "contextlib", "contextvars", "copy", "copyreg", "cProfile",
    "crypt", "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm",
    "decimal", "difflib", "dis", "distutils", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io",
    "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc", "nis",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform",
    "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats",
    "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri",
    "random", "re", "readline", "reprlib", "resource", "rlcompleter", "runpy",
    "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil",
    "signal", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "spwd", "sqlite3", "sre_compile", "sre_constants", "sre_parse", "ssl",
    "stat", "statistics", "string", "stringprep", "struct", "subprocess",
    "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile",
    "telnetlib", "tempfile", "termios", "test", "textwrap", "threading",
    "time", "timeit", "tkinter", "token", "tokenize", "trace", "traceback",
    "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib",
    "_thread", "__future__",
}

IMPORT_TO_PACKAGE: dict[str, str] = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "attr": "attrs",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "gi": "PyGObject",
    "google": "google-api-python-client",
    "yaml": "PyYAML",
    "serial": "pyserial",
    "usb": "pyusb",
    "wx": "wxPython",
    "Crypto": "pycryptodome",
    "nacl": "PyNaCl",
    "jwt": "PyJWT",
    "lxml": "lxml",
}

ICON_PATCH_CODE = '''
# --- PyInstaller Builder: auto icon patch ---
import sys as _sys
if _sys.platform == "win32":
    try:
        import ctypes as _ctypes
        _ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("pyinstaller.builder.app")
    except Exception:
        pass
# --- end icon patch ---
'''


def _find_python() -> str | None:
    if not getattr(sys, "frozen", False):
        return sys.executable

    for name in ("python.exe", "python3.exe", "python"):
        found = shutil.which(name)
        if found:
            try:
                r = subprocess.run(
                    [found, "--version"],
                    capture_output=True, text=True, timeout=5,
                    encoding="utf-8", errors="replace",
                    creationflags=_popen_flags(),
                )
                if r.returncode == 0 and "Python" in r.stdout:
                    return found
            except Exception:
                continue

    if sys.platform == "win32":
        local_python = os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Programs", "Python"
        )
        if os.path.isdir(local_python):
            for d in sorted(os.listdir(local_python), reverse=True):
                candidate = os.path.join(local_python, d, "python.exe")
                if os.path.isfile(candidate):
                    return candidate

        for base in [os.path.expanduser("~"), "C:\\"]:
            pdir = os.path.join(base, "Python")
            if not os.path.isdir(pdir):
                continue
            for root_dir, dirs, files in os.walk(pdir):
                if "python.exe" in files:
                    candidate = os.path.join(root_dir, "python.exe")
                    try:
                        r = subprocess.run(
                            [candidate, "--version"],
                            capture_output=True, text=True, timeout=5,
                            encoding="utf-8", errors="replace",
                            creationflags=_popen_flags(),
                        )
                        if r.returncode == 0 and "Python" in r.stdout:
                            return candidate
                    except Exception:
                        continue
                dirs[:] = [dd for dd in dirs if not dd.startswith(".")]
                if len(dirs) > 20:
                    break

    return None


def detect_imports(py_path: str) -> list[str]:
    try:
        source = Path(py_path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=py_path)
    except Exception:
        return []

    top_level: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                top_level.add(node.module.split(".")[0])

    return sorted(
        pkg for pkg in top_level
        if pkg not in STDLIB_MODULES and not pkg.startswith("_")
    )


def _safe_icon_path(icon_path: str) -> tuple[str, str | None]:
    try:
        icon_path.encode("ascii")
        return icon_path, None
    except UnicodeEncodeError:
        pass
    tmp_dir = tempfile.mkdtemp(prefix="pyibuild_ico_")
    ext = os.path.splitext(icon_path)[1] or ".ico"
    safe_path = os.path.join(tmp_dir, f"icon{ext}")
    shutil.copy2(icon_path, safe_path)
    return safe_path, tmp_dir


def _create_patched_script(py_path: str) -> tuple[str, str]:
    source = Path(py_path).read_text(encoding="utf-8", errors="replace")

    if "SetCurrentProcessExplicitAppUserModelID" in source:
        return py_path, ""

    lines = source.splitlines(keepends=True)
    insert_pos = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped.startswith("#!"):
            insert_pos = 1
            continue
        if i <= 1 and stripped.startswith("#") and "coding" in stripped:
            insert_pos = i + 1
            continue
        break

    rest = "".join(lines[insert_pos:]).lstrip()
    if rest.startswith(('"""', "'''", '"', "'")):
        try:
            tree = ast.parse(source)
            if (tree.body and isinstance(tree.body[0], ast.Expr)
                    and isinstance(tree.body[0].value, (ast.Constant, ast.Str))):
                insert_pos = tree.body[0].end_lineno
        except Exception:
            pass

    patched = "".join(lines[:insert_pos]) + ICON_PATCH_CODE + "".join(lines[insert_pos:])

    tmp_dir = tempfile.mkdtemp(prefix="pyibuild_src_")
    tmp_file = os.path.join(tmp_dir, os.path.basename(py_path))
    Path(tmp_file).write_text(patched, encoding="utf-8")
    return tmp_file, tmp_dir


def _popen_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class BuildWorker(QThread):
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, python_exe: str, py_file: str, command: list[str],
                 packages: list[str] | None = None,
                 cwd: str | None = None, temp_dirs: list[str] | None = None):
        super().__init__()
        self.python_exe = python_exe
        self.py_file = py_file
        self.command = command
        self.packages = packages or []
        self.cwd = cwd
        self.temp_dirs = temp_dirs or []

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
                [self.python_exe, "-m", "PyInstaller", "--version"],
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
            [self.python_exe, "-m", "pip", "install", "pyinstaller"],
            "pip install pyinstaller",
        )
        if code != 0:
            self.error_signal.emit(
                "Не удалось установить PyInstaller. "
                "Проверьте подключение к интернету и права доступа."
            )
            return False
        self.log_signal.emit("\nPyInstaller успешно установлен.\n")
        return True

    def _ensure_packages(self) -> bool:
        """Проверяет каждый пакет в целевом Python и доустанавливает недостающие."""
        if not self.packages:
            return True

        missing: list[str] = []
        for pkg in self.packages:
            pip_name = IMPORT_TO_PACKAGE.get(pkg, pkg)
            try:
                r = subprocess.run(
                    [self.python_exe, "-c", f"import {pkg}"],
                    capture_output=True, text=True,
                    encoding="utf-8", errors="replace",
                    timeout=15,
                    creationflags=_popen_flags(),
                )
                if r.returncode != 0:
                    missing.append((pkg, pip_name))
            except Exception:
                missing.append((pkg, pip_name))

        if not missing:
            self.log_signal.emit("✅ Все зависимости уже установлены в целевом Python\n")
            return True

        missing_names = [f"{imp} (pip: {pip})" for imp, pip in missing]
        self.log_signal.emit(
            f"📥 Недостающие пакеты в целевом Python: {', '.join(missing_names)}\n"
        )

        pip_packages = list(dict.fromkeys(pip for _, pip in missing))
        code = self._run_process(
            [self.python_exe, "-m", "pip", "install"] + pip_packages,
            "pip install deps",
        )
        if code != 0:
            self.error_signal.emit(
                f"Не удалось установить пакеты: {', '.join(pip_packages)}. "
                "Проверьте подключение к интернету."
            )
            return False

        self.log_signal.emit("\n✅ Все зависимости установлены.\n")
        return True

    def _cleanup_temp(self):
        for d in self.temp_dirs:
            if d:
                try:
                    shutil.rmtree(d, ignore_errors=True)
                except Exception:
                    pass

    def run(self):
        if not self._ensure_pyinstaller():
            self._cleanup_temp()
            self.finished_signal.emit(-1)
            return

        if not self._ensure_packages():
            self._cleanup_temp()
            self.finished_signal.emit(-1)
            return

        code = self._run_process(self.command, "PyInstaller")
        self._cleanup_temp()
        self.finished_signal.emit(code)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyInstaller Builder")
        self.setMinimumSize(720, 860)
        self.resize(800, 960)
        self.worker: BuildWorker | None = None
        self._detected_packages: list[str] = []
        self._python_exe: str | None = None
        self._build_ui()
        self._connect_signals()
        self._detect_python()
        self._update_build_btn()

    def _detect_python(self):
        self._python_exe = _find_python()
        if self._python_exe:
            self.python_path_edit.setText(self._python_exe)
            self.python_info.setText(f"🐍 Python: {self._python_exe}")
            self.python_info.setStyleSheet("color: #16825D; font-size: 12px; padding: 2px 4px;")
        else:
            self.python_info.setText(
                "⚠️ Python не найден! Укажите путь вручную через «Обзор»"
            )
            self.python_info.setStyleSheet("color: #D32F2F; font-size: 12px; padding: 2px 4px;")
        self.python_info.setVisible(True)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # ── Python interpreter ──
        grp_python = QGroupBox("Python Interpreter")
        hp = QHBoxLayout(grp_python)
        hp.setContentsMargins(10, 8, 10, 8)
        self.python_path_edit = QLineEdit()
        self.python_path_edit.setPlaceholderText("Определяется автоматически…")
        self.python_path_edit.setReadOnly(True)
        btn_python = QPushButton("Обзор…")
        btn_python.setFixedWidth(90)
        btn_python.clicked.connect(self._browse_python)
        hp.addWidget(self.python_path_edit)
        hp.addWidget(btn_python)
        root.addWidget(grp_python)

        self.python_info = QLabel("")
        self.python_info.setWordWrap(True)
        self.python_info.setVisible(False)
        root.addWidget(self.python_info)

        # ── Исходный файл ──
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

        # ── Build Settings ──
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

        # ── Build Mode + Console ──
        h_row1 = QHBoxLayout()
        h_row1.setSpacing(8)

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
        h_row1.addWidget(grp_mode)

        grp_console = QGroupBox("Console Options")
        vc = QVBoxLayout(grp_console)
        vc.setContentsMargins(10, 8, 10, 8)
        self.radio_console = QRadioButton("Консоль (--console)")
        self.radio_windowed = QRadioButton("Без консоли (--windowed)")
        self.radio_console.setChecked(True)
        self._console_group = QButtonGroup(self)
        self._console_group.addButton(self.radio_console)
        self._console_group.addButton(self.radio_windowed)
        vc.addWidget(self.radio_console)
        vc.addWidget(self.radio_windowed)
        h_row1.addWidget(grp_console)

        root.addLayout(h_row1)

        # ── Dependencies + Icon Embed ──
        h_row2 = QHBoxLayout()
        h_row2.setSpacing(8)

        grp_deps = QGroupBox("Dependencies")
        vd = QVBoxLayout(grp_deps)
        vd.setContentsMargins(10, 8, 10, 8)
        self.radio_deps_auto = QRadioButton("Авто (PyInstaller решает)")
        self.radio_deps_collect = QRadioButton("Собрать всё (--collect-all)")
        self.radio_deps_auto.setChecked(True)
        self._deps_group = QButtonGroup(self)
        self._deps_group.addButton(self.radio_deps_auto)
        self._deps_group.addButton(self.radio_deps_collect)
        vd.addWidget(self.radio_deps_auto)
        vd.addWidget(self.radio_deps_collect)
        h_row2.addWidget(grp_deps)

        grp_embed = QGroupBox("Иконка в заголовке окна")
        ve = QVBoxLayout(grp_embed)
        ve.setContentsMargins(10, 8, 10, 8)
        self.radio_icon_off = QRadioButton("Не менять (по умолчанию)")
        self.radio_icon_embed = QRadioButton("Привязать иконку .exe к окну")
        self.radio_icon_off.setChecked(True)
        self._icon_embed_group = QButtonGroup(self)
        self._icon_embed_group.addButton(self.radio_icon_off)
        self._icon_embed_group.addButton(self.radio_icon_embed)
        ve.addWidget(self.radio_icon_off)
        ve.addWidget(self.radio_icon_embed)
        h_row2.addWidget(grp_embed)

        root.addLayout(h_row2)

        # ── Обнаруженные пакеты ──
        self.deps_info = QLabel("")
        self.deps_info.setWordWrap(True)
        self.deps_info.setStyleSheet("color: #555; font-size: 12px; padding: 2px 4px;")
        self.deps_info.setVisible(False)
        root.addWidget(self.deps_info)

        # ── Icon ──
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

        # ── Advanced Settings ──
        grp_adv = QGroupBox("Advanced Settings")
        va = QVBoxLayout(grp_adv)
        va.setContentsMargins(10, 8, 10, 8)
        va.addWidget(QLabel("Дополнительные аргументы PyInstaller:"))
        self.extra_args = QLineEdit()
        self.extra_args.setPlaceholderText("--hidden-import=module --add-data=src;dst …")
        va.addWidget(self.extra_args)
        root.addWidget(grp_adv)

        # ── Execution ──
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

        # ── Output ──
        grp_log = QGroupBox("Output")
        vl = QVBoxLayout(grp_log)
        vl.setContentsMargins(4, 4, 4, 4)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(140)
        self.log_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vl.addWidget(self.log_view)
        root.addWidget(grp_log, stretch=1)

    def _connect_signals(self):
        self.btn_build.clicked.connect(self._start_build)
        self.input_path.textChanged.connect(self._update_build_btn)
        self.input_path.textChanged.connect(self._scan_imports)
        self.icon_path.textChanged.connect(self._update_window_icon)

    def _update_build_btn(self):
        has_file = bool(self.input_path.text().strip())
        has_python = self._python_exe is not None
        self.btn_build.setEnabled(has_file and has_python)

    def _update_window_icon(self):
        ico = self.icon_path.text().strip()
        if ico and os.path.isfile(ico):
            self.setWindowIcon(QIcon(ico))
        else:
            self.setWindowIcon(QIcon())

    def _scan_imports(self):
        path = self.input_path.text().strip()
        if not path:
            self.deps_info.setVisible(False)
            self._detected_packages = []
            return
        self._detected_packages = detect_imports(path)
        if self._detected_packages:
            self.deps_info.setText(
                f"📦 Обнаружены сторонние пакеты ({len(self._detected_packages)}): "
                f"{', '.join(self._detected_packages)}"
            )
        else:
            self.deps_info.setText("📦 Сторонние пакеты не обнаружены")
        self.deps_info.setVisible(True)

    # ── Browse ──
    def _browse_python(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите python.exe", "",
            "Python (python.exe python3.exe);;All Files (*)"
        )
        if path:
            self._python_exe = path
            self.python_path_edit.setText(path)
            self.python_info.setText(f"🐍 Python (вручную): {path}")
            self.python_info.setStyleSheet("color: #16825D; font-size: 12px; padding: 2px 4px;")
            self._update_build_btn()

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Python-файл", "", "Python Files (*.py *.pyw)"
        )
        if path:
            self.input_path.setText(path)
            if not self.output_name.text():
                self.output_name.setText(os.path.splitext(os.path.basename(path))[0])

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

    # ── Build ──
    def _build_command(self) -> tuple[list[str], list[str]]:
        temp_dirs: list[str] = []
        python = self._python_exe
        src = self.input_path.text().strip()

        if self.radio_icon_embed.isChecked():
            patched_src, tmp_src = _create_patched_script(src)
            if tmp_src:
                temp_dirs.append(tmp_src)
            build_src = patched_src
        else:
            build_src = src

        cmd = [python, "-m", "PyInstaller"]
        cmd.append("--onefile" if self.radio_onefile.isChecked() else "--onedir")
        cmd.append("--console" if self.radio_console.isChecked() else "--windowed")
        cmd.append("--noconfirm")

        name = self.output_name.text().strip()
        if name:
            cmd += ["--name", name]

        dist = self.output_dir.text().strip()
        if dist:
            cmd += ["--distpath", dist]

        icon = self.icon_path.text().strip()
        if icon and os.path.isfile(icon):
            safe_icon, tmp_ico = _safe_icon_path(icon)
            if tmp_ico:
                temp_dirs.append(tmp_ico)
            cmd += ["--icon", safe_icon]

        if self.radio_deps_collect.isChecked():
            for pkg in self._detected_packages:
                cmd += ["--hidden-import", pkg]
                cmd += ["--collect-all", pkg]
                pip_name = IMPORT_TO_PACKAGE.get(pkg)
                if pip_name and pip_name != pkg:
                    cmd += ["--collect-all", pip_name]

        extra = self.extra_args.text().strip()
        if extra:
            cmd += shlex.split(extra)

        cmd.append(build_src)
        return cmd, temp_dirs

    def _set_ui_locked(self, locked: bool):
        for w in (
            self.btn_build, self.input_path, self.output_name,
            self.output_dir, self.icon_path, self.extra_args,
            self.radio_onefile, self.radio_onedir,
            self.radio_console, self.radio_windowed,
            self.radio_deps_auto, self.radio_deps_collect,
            self.radio_icon_off, self.radio_icon_embed,
        ):
            w.setEnabled(not locked)
        if not locked:
            self._update_build_btn()

    def _set_status(self, text: str, color: str = "#1E1E1E"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 600;")

    def _start_build(self):
        if not self._python_exe:
            self._log_error("Python не найден! Укажите путь в секции Python Interpreter.")
            return

        self.log_view.clear()
        cmd, temp_dirs = self._build_command()
        self._set_status("⏳ Выполняется…", "#E8A317")
        self._set_ui_locked(True)

        self._log(f"🐍 Используется Python: {self._python_exe}\n")

        if self.radio_deps_collect.isChecked() and self._detected_packages:
            self._log(f"📦 --hidden-import + --collect-all для: {', '.join(self._detected_packages)}\n")

        icon = self.icon_path.text().strip()
        if icon:
            self._log(f"🎨 Иконка: {icon}\n")

        if self.radio_icon_embed.isChecked():
            self._log("🔗 Привязка иконки к окну: включена (auto-patch)\n")

        # Передаём список пакетов для автоустановки
        packages = self._detected_packages if self.radio_deps_collect.isChecked() else []

        src = self.input_path.text().strip()
        self.worker = BuildWorker(
            self._python_exe, src, cmd,
            packages=packages,
            cwd=os.path.dirname(src) or None,
            temp_dirs=temp_dirs,
        )
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