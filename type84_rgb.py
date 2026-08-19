import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import hid
import threading
import time
import json
import os
import sys

VID = 0x0C45
PID = 0x8009
INTERFACE = 2
USAGE_PAGE = 0xFF68
USAGE = 0x61
REPORT_SIZE = 64
PACKET_DELAY = 0.020
LED_COUNT = 128


def get_settings_path():
    """
    Путь к файлу настроек.

    Важно: при запуске обычного .py скрипта используем папку рядом с файлом.
    Но когда приложение собрано в .exe (например через PyInstaller, режим
    --onefile), sys.executable/__file__ указывает на временную папку
    распаковки, которая создаётся заново при КАЖДОМ запуске — из-за этого
    настройки не сохранялись между запусками. Поэтому для собранного .exe
    используем стабильную папку в %APPDATA%.
    """
    if getattr(sys, "frozen", False):
        base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
        base_dir = os.path.join(base_dir, "Type84RGB")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        os.makedirs(base_dir, exist_ok=True)
    except Exception:
        base_dir = os.path.expanduser("~")
    return os.path.join(base_dir, "type84_rgb_settings.json")


SETTINGS_FILE = get_settings_path()

KEY_INDEX = {
    "Esc": 0, "F1": 1, "F2": 2, "F3": 3, "F4": 4, "F5": 5, "F6": 6,
    "F7": 7, "F8": 8, "F9": 9, "F10": 10, "F11": 11, "F12": 12,
    "Ё": 16, "1": 17, "2": 18, "3": 19, "4": 20, "5": 21, "6": 22,
    "7": 23, "8": 24, "9": 25, "0": 26, "-": 27, "=": 28,
    "Tab": 32, "Q": 33, "W": 34, "E": 35, "R": 36, "T": 37, "Y": 38,
    "U": 39, "I": 40, "O": 41, "P": 42, "[": 43, "]": 44,
    "Caps": 48, "A": 49, "S": 50, "D": 51, "F": 52, "G": 53, "H": 54,
    "J": 55, "K": 56, "L": 57, ";": 58, "'": 59, "\\": 60,
    "LShift": 64, "Z": 65, "X": 66, "C": 67, "V": 68, "B": 69, "N": 70,
    "M": 71, ",": 72, ".": 73, "/": 74, "RShift": 75, "Enter": 76,
    "LCtrl": 80, "Win": 81, "LAlt": 82, "Space": 83, "RAlt": 84,
    "Fn": 85, "RCtrl": 87, "Left": 88, "Down": 89, "Up": 90, "Right": 91,
    "Backspace": 92, "Insert": 103, "Home": 104, "PgUp": 105,
    "Delete": 106, "End": 107, "PgDn": 108,
}

UNIT_PX = 54          # шаг одной стандартной клавиши (1u) в пикселях
GAP_PX = 5            # зазор между клавишами
ROW_EXTRA_GAP_PX = 14  # доп. отступ между рядом F-клавиш и остальной клавиатурой
KEYBOARD_COLS_U = 18.75   # общая ширина раскладки в юнитах (для размера фрейма)
KEYBOARD_ROWS = 6

# Раскладка "как в реальности": для каждой клавиши задаётся ряд (0-5),
# смещение по X в юнитах (1u = ширина обычной клавиши) и ширина в юнитах.
# Это даёт настоящий постуступенчатый сдвиг рядов и разную ширину клавиш
# (Tab, Caps, Enter, Shift, Backspace, Space и т.д.), как на физической клавиатуре.
KEYBOARD_LAYOUT = [
    # ---- ряд 0: Esc / F1-F12 / колесо громкости / Home,End ----
    ("Esc", 0, 0, 0.00, 1.0),
    ("F1", 1, 0, 1.50, 1.0), ("F2", 2, 0, 2.50, 1.0), ("F3", 3, 0, 3.50, 1.0), ("F4", 4, 0, 4.50, 1.0),
    ("F5", 5, 0, 6.00, 1.0), ("F6", 6, 0, 7.00, 1.0), ("F7", 7, 0, 8.00, 1.0), ("F8", 8, 0, 9.00, 1.0),
    ("F9", 9, 0, 10.50, 1.0), ("F10", 10, 0, 11.50, 1.0), ("F11", 11, 0, 12.50, 1.0), ("F12", 12, 0, 13.50, 1.0),
    ("VOL", None, 0, 15.15, 0.9),
    ("Home", 104, 0, 16.75, 1.0), ("End", 107, 0, 17.75, 1.0),

    # ---- ряд 1: цифровой ряд / Insert,PgUp ----
    ("Ё", 16, 1, 0.0, 1.0), ("1", 17, 1, 1.0, 1.0), ("2", 18, 1, 2.0, 1.0), ("3", 19, 1, 3.0, 1.0),
    ("4", 20, 1, 4.0, 1.0), ("5", 21, 1, 5.0, 1.0), ("6", 22, 1, 6.0, 1.0), ("7", 23, 1, 7.0, 1.0),
    ("8", 24, 1, 8.0, 1.0), ("9", 25, 1, 9.0, 1.0), ("0", 26, 1, 10.0, 1.0), ("-", 27, 1, 11.0, 1.0),
    ("=", 28, 1, 12.0, 1.0), ("Backspace", 92, 1, 13.0, 2.0),
    ("Insert", 103, 1, 16.75, 1.0), ("PgUp", 105, 1, 17.75, 1.0),

    # ---- ряд 2: Tab-ряд / Delete,PgDn ----
    ("Tab", 32, 2, 0.0, 1.5), ("Q", 33, 2, 1.5, 1.0), ("W", 34, 2, 2.5, 1.0), ("E", 35, 2, 3.5, 1.0),
    ("R", 36, 2, 4.5, 1.0), ("T", 37, 2, 5.5, 1.0), ("Y", 38, 2, 6.5, 1.0), ("U", 39, 2, 7.5, 1.0),
    ("I", 40, 2, 8.5, 1.0), ("O", 41, 2, 9.5, 1.0), ("P", 42, 2, 10.5, 1.0), ("[", 43, 2, 11.5, 1.0),
    ("]", 44, 2, 12.5, 1.0), ("\\", 60, 2, 13.5, 1.5),
    ("Delete", 106, 2, 16.75, 1.0), ("PgDn", 108, 2, 17.75, 1.0),

    # ---- ряд 3: Caps-ряд / Enter ----
    ("Caps", 48, 3, 0.0, 1.75), ("A", 49, 3, 1.75, 1.0), ("S", 50, 3, 2.75, 1.0), ("D", 51, 3, 3.75, 1.0),
    ("F", 52, 3, 4.75, 1.0), ("G", 53, 3, 5.75, 1.0), ("H", 54, 3, 6.75, 1.0), ("J", 55, 3, 7.75, 1.0),
    ("K", 56, 3, 8.75, 1.0), ("L", 57, 3, 9.75, 1.0), (";", 58, 3, 10.75, 1.0), ("'", 59, 3, 11.75, 1.0),
    ("Enter", 76, 3, 12.75, 2.25),

    # ---- ряд 4: Shift-ряд / Up ----
    ("LShift", 64, 4, 0.0, 2.25), ("Z", 65, 4, 2.25, 1.0), ("X", 66, 4, 3.25, 1.0), ("C", 67, 4, 4.25, 1.0),
    ("V", 68, 4, 5.25, 1.0), ("B", 69, 4, 6.25, 1.0), ("N", 70, 4, 7.25, 1.0), ("M", 71, 4, 8.25, 1.0),
    (",", 72, 4, 9.25, 1.0), (".", 73, 4, 10.25, 1.0), ("/", 74, 4, 11.25, 1.0), ("RShift", 75, 4, 12.25, 2.75),
    ("Up", 90, 4, 16.75, 1.0),

    # ---- ряд 5: нижний ряд / стрелки ----
    ("LCtrl", 80, 5, 0.0, 1.25), ("Win", 81, 5, 1.25, 1.25), ("LAlt", 82, 5, 2.5, 1.25),
    ("Space", 83, 5, 3.75, 6.25), ("RAlt", 84, 5, 10.0, 1.25), ("Fn", 85, 5, 11.25, 1.0),
    ("RCtrl", 87, 5, 12.25, 1.25),
    ("Left", 88, 5, 15.75, 1.0), ("Down", 89, 5, 16.75, 1.0), ("Right", 91, 5, 17.75, 1.0),
]

LIGHT_BG = "#E7E4E8"
LIGHT_BUTTON = "#D4D0D6"
DARK_BG = "#2B2B2F"
DARK_BUTTON = "#3B3B42"
KEY_BG = "#514952"
KEY_SELECTED = "#746B77"
TEXT_LIGHT = "#202024"
TEXT_DARK = "#F0EDF2"


def clamp_color(c):
    return tuple(max(0, min(255, int(x))) for x in c)


def rgb_hex(c):
    return "#%02X%02X%02X" % tuple(c)


class Type84RGB:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("1180x920")
        self.root.minsize(1000, 800)

        self.device = None
        self.device_info = None

        self.background = (255, 0, 0)
        self.key_color = (255, 0, 0)
        self.brightness_level = 255
        self.per_key_colors = [(0, 0, 0) for _ in range(LED_COUNT)]

        self.selected_keys = set()
        self.selected_key_name = None
        self.selected_key_index = None

        self.custom_mode_active = False
        self.dark_mode = False

        self.cycle_commands = []
        self.cycle_loop_enabled = False
        self.cycle_running = False
        self.cycle_stop_event = threading.Event()
        self.per_key_send_lock = threading.Lock()
        self.cycle_row_widgets = []

        self.brightness_var = tk.IntVar(value=255)
        self.cycle_loop_var = tk.BooleanVar(value=False)

        self.keyboard_buttons = {}

        self.build_ui()
        self.load_settings()
        self.apply_theme()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------- UI ----------------
    def build_ui(self):
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=18, pady=(12, 6))
        self.header = header
        tk.Label(header, text="Red Square IO Type 84 RGB", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.theme_button = tk.Button(header, text="☾ Тёмная тема", command=self.toggle_theme, relief="flat", padx=12, pady=5, cursor="hand2")
        self.theme_button.pack(side="right")

        self.status = tk.StringVar(value="Устройство не подключено")
        self.status_label = tk.Label(self.root, textvariable=self.status, font=("Segoe UI", 10))
        self.status_label.pack(pady=(0, 7))

        device = tk.Frame(self.root)
        device.pack(fill="x", padx=25)
        self.device_frame = device
        self.make_ui_button(device, "1. Найти клавиатуру", self.scan).pack(side="left", fill="x", expand=True, padx=3)
        self.make_ui_button(device, "2. Подключить MI_02", self.connect).pack(side="left", fill="x", expand=True, padx=3)

        self.add_separator()

        tk.Label(self.root, text="ВСЯ КЛАВИАТУРА", font=("Segoe UI", 12, "bold")).pack()
        whole = tk.Frame(self.root)
        whole.pack(pady=5)
        self.make_ui_button(whole, "🎨 Выбрать цвет всей клавиатуры", self.choose_background).pack(side="left", padx=4)
        self.make_ui_button(whole, "👤 Пользовательский режим", self.set_custom_mode).pack(side="left", padx=4)
        tk.Label(whole, text="Яркость:").pack(side="left", padx=(18, 4))
        self.brightness_scale = tk.Scale(
            whole, from_=0, to=255, orient="horizontal", variable=self.brightness_var,
            length=220, showvalue=True, resolution=1, highlightthickness=0
        )
        self.brightness_scale.pack(side="left", padx=2)
        self.make_ui_button(whole, "Применить", self.apply_brightness).pack(side="left", padx=4)

        self.add_separator()

        selection_bar = tk.Frame(self.root)
        selection_bar.pack(fill="x", padx=25, pady=(0, 5))
        self.selected_label = tk.StringVar(value="Выбрано: 0 клавиш")
        tk.Label(selection_bar, textvariable=self.selected_label, font=("Segoe UI", 11, "bold")).pack(side="left")
        self.make_ui_button(selection_bar, "Очистить выбор", self.clear_selection).pack(side="right", padx=3)
        self.make_ui_button(selection_bar, "Выбрать все", self.select_all_keys).pack(side="right", padx=3)

        keyboard_outer = tk.Frame(self.root)
        keyboard_outer.pack(fill="x", padx=20)
        self.keyboard_frame = tk.Frame(keyboard_outer)
        self.keyboard_frame.pack()
        self.build_keyboard()

        self.add_separator()

        # Этот блок теперь растягивается вместе с окном (fill="both", expand=True),
        # чтобы блок "Переливающиеся клавиши" внутри него мог расти в высоту.
        self.user_mode_frame = tk.Frame(self.root, bd=1, relief="groove")
        self.user_mode_frame.pack(fill="both", expand=True, padx=20, pady=(4, 8))
        tk.Label(self.user_mode_frame, text="ПОЛЬЗОВАТЕЛЬСКИЙ РЕЖИМ", font=("Segoe UI", 12, "bold")).pack(pady=(8, 2))

        self.per_key_tab = tk.Frame(self.user_mode_frame)
        self.per_key_tab.pack(fill="x", padx=8, pady=(0, 5))
        self.build_per_key_tab()

        self.cycle_sub_frame = tk.Frame(self.user_mode_frame, bd=1, relief="groove")
        self.cycle_sub_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        tk.Label(self.cycle_sub_frame, text="ПЕРЕЛИВАЮЩИЕСЯ КЛАВИШИ", font=("Segoe UI", 11, "bold")).pack(pady=(7, 2))

        self.cycle_tab = tk.Frame(self.cycle_sub_frame)
        self.cycle_tab.pack(fill="both", expand=True, padx=5, pady=3)
        self.build_cycle_tab()

    def add_separator(self):
        tk.Frame(self.root, height=1).pack(fill="x", padx=25, pady=8)

    def make_ui_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, relief="raised", bd=1, padx=8, pady=5, cursor="hand2")

    def build_per_key_tab(self):
        controls = tk.Frame(self.per_key_tab)
        controls.pack(pady=6)
        self.make_ui_button(controls, "🎨 Цвет выбранных", self.choose_key_color).grid(row=0, column=0, padx=4)
        self.make_ui_button(controls, "🌈 Цвет всех клавиш", self.choose_all_custom_color).grid(row=0, column=1, padx=4)
        self.make_ui_button(controls, "⬛ Выключить выбранные", self.disable_selected_key).grid(row=0, column=2, padx=4)
        self.make_ui_button(controls, "⬛ Выключить все", self.disable_all_keys).grid(row=0, column=3, padx=4)
        tk.Label(self.per_key_tab, text="Можно выбрать одну или несколько клавиш на виртуальной клавиатуре.").pack(pady=(0, 5))

    def build_cycle_tab(self):
        top = tk.Frame(self.cycle_tab)
        top.pack(fill="x", padx=10, pady=6)
        tk.Label(
            top,
            text="Команды выполняются строго по порядку. Выбери клавиши, выбери цвет и нажми «+ Добавить команду». Интервал — время до следующей команды."
        ).pack(side="left", fill="x", expand=True)
        self.make_ui_button(top, "+ Добавить команду", self.add_cycle_command).pack(side="right", padx=3)

        controls = tk.Frame(self.cycle_tab)
        controls.pack(fill="x", padx=10, pady=(0, 5))
        self.make_ui_button(controls, "▶ Запустить последовательность", self.start_cycle_sequence).pack(side="left", padx=3)
        self.make_ui_button(controls, "■ Остановить", self.stop_cycle_sequence).pack(side="left", padx=3)
        tk.Checkbutton(
            controls, text="Цикличность", variable=self.cycle_loop_var,
            command=self.on_cycle_loop_changed
        ).pack(side="left", padx=14)
        tk.Label(controls, text="Если цикличность выключена, после последней команды последовательность остановится.").pack(side="left", padx=4)

        # fill="both", expand=True — блок со списком команд растягивается вместе с окном.
        self.cycle_canvas = tk.Canvas(self.cycle_tab, height=250, highlightthickness=0)
        self.cycle_scroll = ttk.Scrollbar(self.cycle_tab, orient="vertical", command=self.cycle_canvas.yview)
        self.cycle_inner = tk.Frame(self.cycle_canvas)
        self.cycle_inner.bind("<Configure>", lambda e: self.cycle_canvas.configure(scrollregion=self.cycle_canvas.bbox("all")))
        self.cycle_canvas_window = self.cycle_canvas.create_window((0, 0), window=self.cycle_inner, anchor="nw")
        # Ширина внутреннего фрейма подстраивается под ширину канваса, чтобы
        # строки команд тоже растягивались по горизонтали вместе с окном.
        self.cycle_canvas.bind(
            "<Configure>",
            lambda e: self.cycle_canvas.itemconfigure(self.cycle_canvas_window, width=e.width)
        )
        self.cycle_canvas.configure(yscrollcommand=self.cycle_scroll.set)
        self.cycle_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 8))
        self.cycle_scroll.pack(side="right", fill="y", padx=(0, 10), pady=(0, 8))

        # Прокрутка колесом мыши в любой точке блока, а не только на скроллбаре.
        self.enable_mousewheel_scroll(self.cycle_tab)

    # ---------------- Mousewheel scrolling ----------------
    def enable_mousewheel_scroll(self, widget):
        """Рекурсивно навешивает обработчик колеса мыши на widget и всех
        его текущих потомков, чтобы прокрутка cycle_canvas работала при
        наведении курсора в любой точке блока."""
        widget.bind("<MouseWheel>", self._on_cycle_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_cycle_mousewheel_up, add="+")
        widget.bind("<Button-5>", self._on_cycle_mousewheel_down, add="+")
        for child in widget.winfo_children():
            self.enable_mousewheel_scroll(child)

    def _on_cycle_mousewheel(self, event):
        # Windows/macOS: event.delta кратен 120 (или является дробным на macOS).
        self.cycle_canvas.yview_scroll(int(-1 * (event.delta / 120)) or (-1 if event.delta > 0 else 1), "units")

    def _on_cycle_mousewheel_up(self, event):
        # Linux
        self.cycle_canvas.yview_scroll(-3, "units")

    def _on_cycle_mousewheel_down(self, event):
        # Linux
        self.cycle_canvas.yview_scroll(3, "units")

    # ---------------- Keyboard selection ----------------
    def build_keyboard(self):
        """
        Строит виртуальную клавиатуру через place() с точными пиксельными
        координатами (а не через grid с одинаковыми ячейками) — так ряды
        получают настоящий постуступенчатый сдвиг, а клавиши — реальную
        ширину (Tab, Caps, Enter, Shift, Backspace, Space и т.д.), как на
        физической клавиатуре.
        """
        total_width = round(KEYBOARD_COLS_U * UNIT_PX)
        total_height = KEYBOARD_ROWS * UNIT_PX + ROW_EXTRA_GAP_PX
        self.keyboard_frame.configure(width=total_width, height=total_height)
        self.keyboard_frame.pack_propagate(False)

        for text, index, row, xu, wu in KEYBOARD_LAYOUT:
            if text == "VOL" and index is None:
                # Не отдельная клавиша, а колесо громкости — рисуем серый
                # кружок вместо пропуска ячейки, как на физической клавиатуре.
                self.make_volume_indicator(row, xu, wu)
                continue
            if not text or index is None:
                continue
            self.make_key(text, index, row, xu, wu)

    def key_pixel_rect(self, row, xu, wu):
        y = row * UNIT_PX + (ROW_EXTRA_GAP_PX if row >= 1 else 0)
        x = xu * UNIT_PX
        w = wu * UNIT_PX - GAP_PX
        h = UNIT_PX - GAP_PX
        return round(x + GAP_PX / 2), round(y + GAP_PX / 2), round(w), round(h)

    def make_key(self, text, index, row, xu, wu):
        x, y, w, h = self.key_pixel_rect(row, xu, wu)
        b = tk.Button(
            self.keyboard_frame, text=text, font=("Segoe UI", 9, "bold"),
            relief="raised", bd=2, cursor="hand2", command=lambda: self.toggle_key_selection(text, index)
        )
        b.place(x=x, y=y, width=w, height=h)
        self.keyboard_buttons[index] = b

    def make_volume_indicator(self, row, xu, wu):
        """Просто декоративный серый кружок на месте колеса громкости —
        не клавиша, не выбирается и не участвует в подсветке."""
        x, y, w, h = self.key_pixel_rect(row, xu, wu)
        size = min(w, h)
        canvas = tk.Canvas(self.keyboard_frame, width=size, height=size, highlightthickness=0, bd=0, bg=KEY_BG)
        pad = max(2, size // 9)
        canvas.create_oval(pad, pad, size - pad, size - pad, fill="#9A97A0", outline="#C7C4CC", width=1)
        canvas.place(x=x + (w - size) // 2, y=y + (h - size) // 2)
        return canvas

    def toggle_key_selection(self, name, index):
        if index in self.selected_keys:
            self.selected_keys.remove(index)
        else:
            self.selected_keys.add(index)
        self.selected_key_name = name if index in self.selected_keys else self.selected_key_name
        self.selected_key_index = index if index in self.selected_keys else (next(iter(self.selected_keys)) if self.selected_keys else None)
        self.update_selection_label()
        self.refresh_key_buttons()
        self.save_settings()

    def select_all_keys(self):
        self.selected_keys = set(KEY_INDEX.values())
        self.selected_key_index = next(iter(self.selected_keys), None)
        self.selected_key_name = next((n for n, i in KEY_INDEX.items() if i == self.selected_key_index), None)
        self.update_selection_label()
        self.refresh_key_buttons()
        self.save_settings()

    def clear_selection(self):
        self.selected_keys.clear()
        self.selected_key_index = None
        self.selected_key_name = None
        self.update_selection_label()
        self.refresh_key_buttons()
        self.save_settings()

    def update_selection_label(self):
        if not self.selected_keys:
            self.selected_label.set("Выбрано: 0 клавиш")
            return
        names = [name for name, idx in KEY_INDEX.items() if idx in self.selected_keys]
        preview = ", ".join(names[:8]) + (" …" if len(names) > 8 else "")
        self.selected_label.set(f"Выбрано: {len(self.selected_keys)} • {preview}")

    def refresh_key_buttons(self):
        for idx, b in self.keyboard_buttons.items():
            selected = idx in self.selected_keys
            b.configure(
                bg=KEY_SELECTED if selected else KEY_BG,
                fg="#FFFFFF",
                activebackground=KEY_SELECTED if selected else KEY_BG,
                activeforeground="#FFFFFF"
            )

    # ---------------- Device ----------------
    def find_device(self):
        for d in hid.enumerate(VID, PID):
            if d.get("interface_number") == INTERFACE and d.get("usage_page") == USAGE_PAGE and d.get("usage") == USAGE:
                return d
        return None

    def scan(self):
        info = self.find_device()
        if not info:
            self.status.set("❌ Type 84 не найдена")
            return
        self.device_info = info
        self.status.set("✅ Type 84 найдена")

    def connect(self):
        if not self.device_info:
            self.device_info = self.find_device()
        if not self.device_info:
            messagebox.showerror("Ошибка", "Сначала найди клавиатуру.")
            return
        try:
            if self.device:
                self.device.close()
            self.device = hid.device()
            self.device.open_path(self.device_info["path"])
            self.status.set("🟢 MI_02 подключён")
            # Восстанавливаем сохранённое визуальное состояние при подключении.
            if self.custom_mode_active:
                self.send_per_key_state()
            else:
                self.send(self.make_static(*self.background), log=False)
        except Exception as e:
            self.device = None
            self.status.set("❌ Ошибка подключения")
            messagebox.showerror("Ошибка подключения", str(e))

    # ---------------- Brightness / static ----------------
    def apply_brightness(self):
        self.brightness_level = int(self.brightness_var.get())
        self.save_settings()
        if not self.device:
            self.status.set(f"💡 Яркость сохранена: {self.brightness_level}")
            return
        if self.custom_mode_active:
            ok = self.send_per_key_state()
        else:
            ok = self.send(self.make_static(*self.background), log=False)
        if ok:
            self.status.set(f"💡 Яркость применена: {self.brightness_level}")

    def scale_rgb(self, color):
        level = max(0, min(255, self.brightness_level))
        factor = level / 255.0
        return tuple(max(0, min(255, round(c * factor))) for c in color)

    # ---------------- HID protocol ----------------
    def send(self, packet, log=False):
        if not self.device:
            messagebox.showwarning("Нет подключения", "Сначала подключи MI_02.")
            return False
        if len(packet) != REPORT_SIZE:
            raise ValueError("HID report должен быть 64 байта")
        result = self.device.write([0] + list(packet))
        time.sleep(PACKET_DELAY)
        return result >= 0

    def make_static(self, r, g, b, custom=False):
        r, g, b = self.scale_rgb((r, g, b))
        packet = [0] * 64
        packet[0:8] = [0xAA, 0x23, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00]
        packet[8] = 0x80 if custom else 0x01
        packet[9:13] = [r, g, b, 0xFF]
        packet[13:21] = [0x00, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00]
        packet[21:23] = [0xAA, 0x55]
        return packet

    def set_custom_mode(self):
        if self.send(self.make_static(*self.background, custom=True)):
            self.custom_mode_active = True
            self.save_settings()
            self.status.set("👤 Пользовательский режим включён")

    def choose_background(self):
        result = colorchooser.askcolor(initialcolor=rgb_hex(self.background), title="Цвет всей клавиатуры")
        if result and result[0]:
            self.background = tuple(map(int, result[0]))
            self.save_settings()
            if self.send(self.make_static(*self.background)):
                self.custom_mode_active = False
                self.save_settings()
                self.status.set(f"🟢 RGB: {rgb_hex(self.background)}")

    # ---------------- Per-key custom mode ----------------
    def require_selection(self):
        if not self.selected_keys:
            messagebox.showwarning("Клавиши", "Сначала выбери одну или несколько клавиш на виртуальной клавиатуре.")
            return False
        return True

    def choose_key_color(self):
        if not self.require_selection():
            return
        result = colorchooser.askcolor(initialcolor=rgb_hex(self.key_color), title="Цвет выбранных клавиш")
        if result and result[0]:
            self.key_color = tuple(map(int, result[0]))
            for idx in self.selected_keys:
                self.per_key_colors[idx] = self.key_color
            self.custom_mode_active = True
            self.save_settings()
            # Отправляем только те клавиши, которые реально изменились —
            # они меняют цвет одновременно, а не по очереди.
            self.send_per_key_state(changed_indices=self.selected_keys)

    def choose_all_custom_color(self):
        result = colorchooser.askcolor(initialcolor=rgb_hex(self.key_color), title="Цвет всех клавиш в пользовательском режиме")
        if not result or not result[0]:
            return
        self.key_color = tuple(map(int, result[0]))
        self.per_key_colors = [self.key_color for _ in range(LED_COUNT)]
        self.custom_mode_active = True
        self.save_settings()
        self.send_per_key_state()

    def disable_selected_key(self):
        if not self.require_selection():
            return
        for idx in self.selected_keys:
            self.per_key_colors[idx] = (0, 0, 0)
        self.custom_mode_active = True
        self.save_settings()
        self.send_per_key_state(changed_indices=self.selected_keys)

    def disable_all_keys(self):
        self.per_key_colors = [(0, 0, 0) for _ in range(LED_COUNT)]
        self.custom_mode_active = True
        self.save_settings()
        self.send_per_key_state()

    def make_chunk_packet(self, start):
        """Пакет с цветами для 14 клавиш, начиная с индекса start."""
        chunk = self.per_key_colors[start:start + 14]
        packet = [0] * 64
        offset = start * 4
        packet[0:8] = [0xAA, 0x24, 0x38, offset & 0xFF, (offset >> 8) & 0xFF, 0x00, 0x00, 0x00]
        pos = 8
        for i, color in enumerate(chunk, start=start):
            r, g, b = self.scale_rgb(clamp_color(color))
            packet[pos:pos + 4] = [i & 0xFF, r, g, b]
            pos += 4
        return packet

    def make_final_packet(self):
        """Финальный пакет, фиксирующий состояние (всегда отправляется последним)."""
        final = [0] * 64
        final[0:8] = [0xAA, 0x24, 0x08, 0xF8, 0x01, 0x00, 0x01, 0x00]
        final[8:12] = [126, *self.scale_rgb(clamp_color(self.per_key_colors[126]))]
        final[12:16] = [127, *self.scale_rgb(clamp_color(self.per_key_colors[127]))]
        return final

    def send_per_key_state(self, changed_indices=None):
        """
        Отправляет текущее состояние self.per_key_colors на клавиатуру.

        changed_indices — если указан, отправляются только те чанки по 14
        клавиш, в которые попадают изменённые индексы (плюс обязательный
        финальный пакет). Это сильно уменьшает число HID-пакетов, когда
        меняется всего несколько клавиш, и делает смену цвета визуально
        одновременной, а не "по очереди". Если None — отправляется полное
        состояние всех 128 клавиш (используется при переключении режима,
        смене яркости, "выбрать все" и т.п.).
        """
        if not self.device:
            self.status.set("Пользовательский режим сохранён; клавиатура не подключена")
            return False
        with self.per_key_send_lock:
            force_full = not self.custom_mode_active
            if force_full:
                if not self.send(self.make_static(*self.background, custom=True), log=False):
                    return False
                self.custom_mode_active = True

            if changed_indices is None or force_full:
                starts = range(0, LED_COUNT, 14)
            else:
                starts = sorted({(idx // 14) * 14 for idx in changed_indices if 0 <= idx < LED_COUNT})

            for start in starts:
                if not self.send(self.make_chunk_packet(start), log=False):
                    return False

            if not self.send(self.make_final_packet(), log=False):
                return False
        return True

    # ---------------- Sequential cycle commands ----------------
    def add_cycle_command(self):
        if not self.require_selection():
            return
        result = colorchooser.askcolor(initialcolor=rgb_hex(self.key_color), title="Цвет команды")
        if not result or not result[0]:
            return
        color = tuple(map(int, result[0]))
        self.key_color = color
        command = {
            "keys": sorted(int(i) for i in self.selected_keys),
            "color": list(color),
            "interval": 1.0,
        }
        self.cycle_commands.append(command)
        self.rebuild_cycle_rows()
        self.save_settings()
        self.status.set(f"Команда №{len(self.cycle_commands)} добавлена")

    def rebuild_cycle_rows(self):
        for widget in self.cycle_inner.winfo_children():
            widget.destroy()
        self.cycle_row_widgets.clear()
        for number, command in enumerate(self.cycle_commands, start=1):
            self.build_cycle_command_row(number, command)
        self.cycle_inner.update_idletasks()
        self.cycle_canvas.configure(scrollregion=self.cycle_canvas.bbox("all"))
        # Новые строки создаются динамически — навешиваем на них прокрутку колесом заново.
        self.enable_mousewheel_scroll(self.cycle_inner)
        # Новые строки рождаются со стандартными (светлыми) цветами Tk,
        # поэтому сразу же прокрашиваем их в текущую тему (тёмную/светлую).
        bg = DARK_BG if self.dark_mode else LIGHT_BG
        button = DARK_BUTTON if self.dark_mode else LIGHT_BUTTON
        fg = TEXT_DARK if self.dark_mode else TEXT_LIGHT
        for row in self.cycle_row_widgets:
            self.style_widget_tree(row, bg, button, fg)
        self.refresh_cycle_color_buttons()

    def build_cycle_command_row(self, number, command):
        row = tk.Frame(self.cycle_inner, bd=1, relief="groove", padx=7, pady=5)
        row.pack(fill="x", padx=5, pady=4)
        self.cycle_row_widgets.append(row)

        names = [name for name, idx in KEY_INDEX.items() if idx in command["keys"]]
        names_text = ", ".join(names[:7]) + (" …" if len(names) > 7 else "")

        tk.Label(row, text=f"№ {number}", width=5, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(row, text=f"Клавиши: {names_text}", width=28, anchor="w").pack(side="left", padx=4)

        color = tuple(command.get("color", [255, 0, 0]))
        color_button = tk.Button(row, text="Цвет", width=7, bg=rgb_hex(color), fg="#FFFFFF", activebackground=rgb_hex(color), cursor="hand2", command=lambda n=number - 1: self.change_cycle_command_color(n))
        color_button._cycle_color_button = True
        color_button.pack(side="left", padx=5)

        interval_var = tk.DoubleVar(value=float(command.get("interval", 1.0)))
        tk.Label(row, text="До следующей:").pack(side="left", padx=(7, 2))
        spin = ttk.Spinbox(row, from_=0.01, to=9999.0, increment=0.1, width=7, textvariable=interval_var)
        spin.pack(side="left")
        tk.Label(row, text="с").pack(side="left", padx=2)
        spin.bind("<FocusOut>", lambda e, n=number - 1, v=interval_var: self.update_cycle_interval(n, v))
        spin.bind("<Return>", lambda e, n=number - 1, v=interval_var: self.update_cycle_interval(n, v))

        self.make_ui_button(row, "↑", lambda n=number - 1: self.move_cycle_command(n, -1)).pack(side="left", padx=(8, 2))
        self.make_ui_button(row, "↓", lambda n=number - 1: self.move_cycle_command(n, 1)).pack(side="left", padx=2)
        self.make_ui_button(row, "✕", lambda n=number - 1: self.remove_cycle_command(n)).pack(side="right", padx=2)

    def change_cycle_command_color(self, index):
        if index < 0 or index >= len(self.cycle_commands):
            return
        old = tuple(self.cycle_commands[index]["color"])
        result = colorchooser.askcolor(initialcolor=rgb_hex(old), title=f"Цвет команды №{index + 1}")
        if result and result[0]:
            self.cycle_commands[index]["color"] = list(map(int, result[0]))
            self.rebuild_cycle_rows()
            self.save_settings()

    def update_cycle_interval(self, index, var):
        try:
            value = max(0.01, float(var.get()))
        except (ValueError, tk.TclError):
            value = 1.0
        self.cycle_commands[index]["interval"] = value
        self.save_settings()

    def remove_cycle_command(self, index):
        if 0 <= index < len(self.cycle_commands):
            self.cycle_commands.pop(index)
            self.rebuild_cycle_rows()
            self.save_settings()

    def move_cycle_command(self, index, direction):
        target = index + direction
        if 0 <= index < len(self.cycle_commands) and 0 <= target < len(self.cycle_commands):
            self.cycle_commands[index], self.cycle_commands[target] = self.cycle_commands[target], self.cycle_commands[index]
            self.rebuild_cycle_rows()
            self.save_settings()

    def on_cycle_loop_changed(self):
        self.cycle_loop_enabled = bool(self.cycle_loop_var.get())
        self.save_settings()

    def start_cycle_sequence(self):
        if not self.cycle_commands:
            messagebox.showwarning("Последовательность", "Сначала добавь хотя бы одну команду.")
            return
        if self.cycle_running:
            return
        self.cycle_stop_event = threading.Event()
        self.cycle_running = True
        self.custom_mode_active = True
        self.save_settings()
        threading.Thread(target=self.cycle_sequence_worker, daemon=True).start()
        self.status.set("▶ Последовательность запущена")

    def stop_cycle_sequence(self):
        self.cycle_stop_event.set()
        self.cycle_running = False
        self.status.set("⏹ Последовательность остановлена")

    def cycle_sequence_worker(self):
        try:
            while not self.cycle_stop_event.is_set():
                for command in list(self.cycle_commands):
                    if self.cycle_stop_event.is_set():
                        break
                    keys = [int(i) for i in command.get("keys", [])]
                    color = clamp_color(command.get("color", [255, 0, 0]))
                    for idx in keys:
                        if 0 <= idx < LED_COUNT:
                            self.per_key_colors[idx] = color
                    self.custom_mode_active = True
                    # Все клавиши этой команды отправляются одним проходом
                    # (минимум пакетов) — они меняют цвет в один момент.
                    if not self.send_per_key_state(changed_indices=keys):
                        self.cycle_stop_event.set()
                        break
                    interval = max(0.01, float(command.get("interval", 1.0)))
                    # Интервал — это явно время до следующей команды.
                    if self.cycle_stop_event.wait(interval):
                        break
                if not self.cycle_loop_enabled:
                    break
        except Exception:
            self.root.after(0, lambda: self.status.set("❌ Ошибка последовательности"))
        finally:
            self.cycle_running = False
            self.save_settings()
            if not self.cycle_stop_event.is_set():
                self.root.after(0, lambda: self.status.set("⏹ Последовательность завершена"))

    # ---------------- Theme ----------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.save_settings()
        self.apply_theme()

    def apply_theme(self):
        bg = DARK_BG if self.dark_mode else LIGHT_BG
        button = DARK_BUTTON if self.dark_mode else LIGHT_BUTTON
        fg = TEXT_DARK if self.dark_mode else TEXT_LIGHT
        self.root.configure(bg=bg)
        for widget in self.root.winfo_children():
            self.style_widget_tree(widget, bg, button, fg)
        self.theme_button.configure(text="☀ Светлая тема" if self.dark_mode else "☾ Тёмная тема", bg=button, fg=fg)
        self.keyboard_frame.configure(bg=bg)
        self.cycle_canvas.configure(bg=bg)
        self.refresh_key_buttons()
        self.refresh_cycle_color_buttons()

    def style_widget_tree(self, widget, bg, button, fg):
        try:
            cls = widget.winfo_class()
            if cls in ("Frame", "Labelframe"):
                widget.configure(bg=bg)
            elif cls == "Label":
                widget.configure(bg=bg, fg=fg)
            elif cls == "Entry":
                widget.configure(bg=button, fg=fg, insertbackground=fg)
            elif cls == "Scale":
                widget.configure(bg=bg, fg=fg, troughcolor=button, activebackground=button, highlightbackground=bg)
            elif cls == "Checkbutton":
                widget.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg, selectcolor=button)
            elif cls == "Button":
                if widget in self.keyboard_buttons.values():
                    return
                if getattr(widget, "_cycle_color_button", False):
                    return
                widget.configure(bg=button, fg=fg, activebackground=button, activeforeground=fg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self.style_widget_tree(child, bg, button, fg)

    def refresh_cycle_color_buttons(self):
        for row, command in zip(self.cycle_row_widgets, self.cycle_commands):
            for child in row.winfo_children():
                if getattr(child, "_cycle_color_button", False):
                    color = tuple(command.get("color", [255, 0, 0]))
                    child.configure(bg=rgb_hex(color), activebackground=rgb_hex(color), fg="#FFFFFF")

    # ---------------- Persistence ----------------
    def save_settings(self):
        data = {
            "background": list(self.background),
            "key_color": list(self.key_color),
            "brightness": int(self.brightness_level),
            "per_key_colors": [list(c) for c in self.per_key_colors],
            "selected_keys": sorted(int(i) for i in self.selected_keys),
            "custom_mode_active": bool(self.custom_mode_active),
            "dark_mode": bool(self.dark_mode),
            "cycle_loop_enabled": bool(self.cycle_loop_var.get()) if hasattr(self, "cycle_loop_var") else bool(self.cycle_loop_enabled),
            "cycle_commands": self.cycle_commands,
        }
        try:
            tmp = SETTINGS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, SETTINGS_FILE)
        except Exception:
            pass

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            self.update_selection_label()
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.background = clamp_color(data.get("background", self.background))
            self.key_color = clamp_color(data.get("key_color", self.key_color))
            self.brightness_level = max(0, min(255, int(data.get("brightness", 255))))
            self.brightness_var.set(self.brightness_level)

            saved_colors = data.get("per_key_colors", [])
            if isinstance(saved_colors, list) and len(saved_colors) == LED_COUNT:
                self.per_key_colors = [clamp_color(c) for c in saved_colors]

            self.selected_keys = {int(i) for i in data.get("selected_keys", []) if int(i) in KEY_INDEX.values()}
            self.custom_mode_active = bool(data.get("custom_mode_active", False))
            self.dark_mode = bool(data.get("dark_mode", False))

            self.cycle_loop_enabled = bool(data.get("cycle_loop_enabled", False))
            self.cycle_loop_var.set(self.cycle_loop_enabled)

            loaded_commands = []
            for command in data.get("cycle_commands", []):
                keys = [int(i) for i in command.get("keys", []) if 0 <= int(i) < LED_COUNT]
                if not keys:
                    continue
                color = list(clamp_color(command.get("color", [255, 0, 0])))
                interval = max(0.01, float(command.get("interval", 1.0)))
                loaded_commands.append({"keys": keys, "color": color, "interval": interval})
            self.cycle_commands = loaded_commands

            if self.selected_keys:
                self.selected_key_index = next(iter(self.selected_keys))
                self.selected_key_name = next((n for n, i in KEY_INDEX.items() if i == self.selected_key_index), None)

            self.update_selection_label()
            self.rebuild_cycle_rows()
        except Exception:
            # Повреждённый файл настроек не должен мешать запуску приложения.
            self.cycle_commands = []
            self.selected_keys.clear()
            self.update_selection_label()

    # ---------------- Close ----------------
    def close(self):
        self.stop_cycle_sequence()
        self.save_settings()
        try:
            if self.device:
                self.device.close()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    Type84RGB(root)
    root.mainloop()


if __name__ == "__main__":
    main()
