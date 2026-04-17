# PyInstaller Builder

Десктопное приложение с графическим интерфейсом для сборки Python-скриптов (.py) в исполняемые файлы (.exe).

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-green?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Возможности

- Сборка `.py` → `.exe` через графический интерфейс
- Режимы сборки: **Onefile** (один файл) / **Onedir** (папка)
- Включение/отключение консоли
- Установка иконки `.ico`
- Выбор имени и директории выходного файла
- Дополнительные аргу��енты PyInstaller
- Автоматическая установка PyInstaller при первом запуске
- Потоковый вывод логов в реальном времени
- Неблокирующий UI (сборка в отдельном потоке)
- Корректная работа с кириллическими путями

## Скриншот

> *Интерфейс выполнен в стиле Visual Studio — тёмная панель вывода, акцентный синий (#007ACC), шрифт Segoe UI.*

## Требования

- **Python 3.11+**
- **PySide6**

PyInstaller устанавливается автоматически при первой сборке. Ручная установка не требуется.

## Установка

```bash
git clone https://github.com/<your-username>/pyinstaller-builder.git
cd pyinstaller-builder
pip install PySide6
```

Или с виртуальным окружением:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install PySide6
```

## Запуск

```bash
python pyinstaller_gui.py
```

## Использование

1. Нажмите **«Обзор…»** и выберите `.py` файл
2. Настройте параметры сборки:
   - Имя выходного файла
   - Директория сохранения
   - Режим сборки (Onefile / Onedir)
   - Консоль (включена / отключена)
   - Иконка (опционально)
   - Дополнительные аргументы (опционально)
3. Нажмите **«Собрать»**
4. Следите за процессом в панели **Output**

## Статусы сборки

| Статус | Описание |
|--------|----------|
| Готов | Приложение готово к работе |
| ⏳ Выполняется… | Идёт сборка |
| ✅ Успешно | Сборка завершена, `.exe` создан |
| ❌ Ошибка | Сборка завершилась с ошибкой — см. лог |

## Структура проекта

```
pyinstaller-builder/
├── pyinstaller_gui.py   # Всё приложение — один файл
├── README.md
└── requirements.txt
```

## requirements.txt

```
PySide6
```

## Технические детали

- **UI**: PySide6 + Fusion style
- **Сборка**: subprocess → PyInstaller (в отдельном QThread)
- **Кодировка**: UTF-8 с `errors="replace"` для корректного отображения кириллицы
- **Автоустановка**: перед сборкой проверяется наличие PyInstaller; если отсутствует — устанавливается через `pip`

## Лицензия

MIT
