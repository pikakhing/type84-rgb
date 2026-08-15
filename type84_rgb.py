import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import hid
import threading
import time
import json
import os

VID = 0x0C45
PID = 0x8009
INTERFACE = 2
USAGE_PAGE = 0xFF68
USAGE = 0x61
REPORT_SIZE = 64
PACKET_DELAY = 0.020
LED_COUNT = 128
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "type84_rgb_settings.json")

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

KEY_LAYOUT = [
    [
        ("Esc", 0, 0, 1, 1), ("F1", 1, 1, 1, 1), ("F2", 2, 2, 1, 1),
        ("F3", 3, 3, 1, 1), ("F4", 4, 4, 1, 1), ("F5", 5, 5, 1, 1),
        ("F6", 6, 6, 1, 1), ("F7", 7, 7, 1, 1), ("F8", 8, 8, 1, 1),
        ("F9", 9, 9, 1, 1), ("F10", 10, 10, 1, 1), ("F11", 11, 11, 1, 1),
        ("F12", 12, 12, 1, 1), ("VOL", None, 14, 1, 1),
        ("Home", 104, 16, 1, 1), ("End", 107, 17, 1, 1),
    ],
    [
        ("Ё", 16, 0, 1, 1), ("1", 17, 1, 1, 1), ("2", 18, 2, 1, 1),
        ("3", 19, 3, 1, 1), ("4", 20, 4, 1, 1), ("5", 21, 5, 1, 1),
        ("6", 22, 6, 1, 1), ("7", 23, 7, 1, 1), ("8", 24, 8, 1, 1),
        ("9", 25, 9, 1, 1), ("0", 26, 10, 1, 1), ("-", 27, 11, 1, 1),
        ("=", 28, 12, 1, 1), ("Backspace", 92, 13, 1, 1),
        ("Insert", 103, 16, 1, 1), ("PgUp", 105, 17, 1, 1),
    ],
    [
        ("Tab", 32, 0, 1, 1), ("Q", 33, 1, 1, 1), ("W", 34, 2, 1, 1),
        ("E", 35, 3, 1, 1), ("R", 36, 4, 1, 1), ("T", 37, 5, 1, 1),
        ("Y", 38, 6, 1, 1), ("U", 39, 7, 1, 1), ("I", 40, 8, 1, 1),
        ("O", 41, 9, 1, 1), ("P", 42, 10, 1, 1), ("[", 43, 11, 1, 1),
        ("]", 44, 12, 1, 1), ("\\", 60, 13, 1, 1),
        ("Delete", 106, 16, 1, 1), ("PgDn", 108, 17, 1, 1),
    ],
    [
        ("Caps", 48, 0, 1, 1), ("A", 49, 1, 1, 1), ("S", 50, 2, 1, 1),
        ("D", 51, 3, 1, 1), ("F", 52, 4, 1, 1), ("G", 53, 5, 1, 1),
        ("H", 54, 6, 1, 1), ("J", 55, 7, 1, 1), ("K", 56, 8, 1, 1),
        ("L", 57, 9, 1, 1), (";", 58, 10, 1, 1), ("'", 59, 11, 1, 1),
        ("Enter", 76, 12, 2, 1),
    ],
    [
        ("LShift", 64, 0, 2, 1), ("Z", 65, 2, 1, 1), ("X", 66, 3, 1, 1),
        ("C", 67, 4, 1, 1), ("V", 68, 5, 1, 1), ("B", 69, 6, 1, 1),
        ("N", 70, 7, 1, 1), ("M", 71, 8, 1, 1), (",", 72, 9, 1, 1),
        (".", 73, 10, 1, 1), ("/", 74, 11, 1, 1), ("RShift", 75, 12, 2, 1),
        ("Up", 90, 16, 1, 1),
    ],
    [
        ("LCtrl", 80, 0, 1, 1), ("Win", 81, 1, 1, 1), ("LAlt", 82, 2, 1, 1),
        ("Space", 83, 3, 6, 1), ("RAlt", 84, 9, 1, 1), ("Fn", 85, 10, 1, 1),
        ("RCtrl", 87, 11, 1, 1), ("Left", 88, 15, 1, 1), ("Down", 89, 16, 1, 1),
        ("Right", 91, 17, 1, 1),
    ],
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
        self.theme_button = tk.Button(header, text="☾ Тёмная тема", command=self.toggle_theme, relief="flat", padx=12, pady=5)
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

        self.user_mode_frame = tk.Frame(self.root, bd=1, relief="groove")
        self.user_mode_frame.pack(fill="x", padx=20, pady=(4, 8))
        tk.Label(self.user_mode_frame, text="ПОЛЬЗОВАТЕЛЬСКИЙ РЕЖИМ", font=("Segoe UI", 12, "bold")).pack(pady=(8, 2))
        self.per_key_tab = tk.Frame(self.user_mode_frame)
        self.per_key_tab.pack(fill="x", padx=8, pady=(0, 5))
        self.build_per_key_tab()

        self.cycle_sub_frame = tk.Frame(self.user_mode_frame, bd=1, relief="groove")
        self.cycle_sub_frame.pack(fill="x", padx=8, pady=(4, 8))
        tk.Label(self.cycle_sub_frame, text="ПЕРЕЛИВАЮЩИЕСЯ КЛАВИШИ", font=("Segoe UI", 11, "bold")).pack(pady=(7, 2))
        self.cycle_tab = tk.Frame(self.cycle_sub_frame)
        self.cycle_tab.pack(fill="x", padx=5, pady=3)
        self.build_cycle_tab()

    def add_separator(self):
        tk.Frame(self.root, height=1).pack(fill="x", padx=25, pady=8)

    def make_ui_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, relief="raised", bd=1, padx=8, pady=5)

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

        self.cycle_canvas = tk.Canvas(self.cycle_tab, height=250, highlightthickness=0)
        self.cycle_scroll = ttk.Scrollbar(self.cycle_tab, orient="vertical", command=self.cycle_canvas.yview)
        self.cycle_inner = tk.Frame(self.cycle_canvas)
        self.cycle_inner.bind("<Configure>", lambda e: self.cycle_canvas.configure(scrollregion=self.cycle_canvas.bbox("all")))
        self.cycle_canvas.create_window((0, 0), window=self.cycle_inner, anchor="nw")
        self.cycle_canvas.configure(yscrollcommand=self.cycle_scroll.set)
        self.cycle_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 8))
        self.cycle_scroll.pack(side="right", fill="y", padx=(0, 10), pady=(0, 8))

    # ---------------- Keyboard selection ----------------
    def build_keyboard(self):
        for row_idx, row in enumerate(KEY_LAYOUT):
            for text, index, col, colspan, rowspan in row:
                if not text or index is None:
                    continue
                self.make_key(text, index, row_idx, col, colspan, rowspan)
        for c in range(18):
            self.keyboard_frame.grid_columnconfigure(c, weight=1)

    def make_key(self, text, index, row, column, colspan=1, rowspan=1):
        b = tk.Button(
            self.keyboard_frame, text=text, width=5, height=2, font=("Segoe UI", 9, "bold"),
            relief="raised", bd=2, command=lambda: self.toggle_key_selection(text, index)
        )
        b.grid(row=row, column=column, columnspan=colspan, rowspan=rowspan, padx=2, pady=2, sticky="nsew")
        self.keyboard_buttons[index] = b

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
            # Restore the remembered visual state on connection.
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
            self.send_per_key_state()

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
        self.send_per_key_state()

    def disable_all_keys(self):
        self.per_key_colors = [(0, 0, 0) for _ in range(LED_COUNT)]
        self.custom_mode_active = True
        self.save_settings()
        self.send_per_key_state()

    def make_per_key_packets(self, colors):
        packets = []
        for start in range(0, LED_COUNT, 14):
            chunk = colors[start:start + 14]
            packet = [0] * 64
            offset = start * 4
            packet[0:8] = [0xAA, 0x24, 0x38, offset & 0xFF, (offset >> 8) & 0xFF, 0x00, 0x00, 0x00]
            pos = 8
            for i, color in enumerate(chunk, start=start):
                r, g, b = self.scale_rgb(clamp_color(color))
                packet[pos:pos + 4] = [i & 0xFF, r, g, b]
                pos += 4
            packets.append(packet)
        final = [0] * 64
        final[0:8] = [0xAA, 0x24, 0x08, 0xF8, 0x01, 0x00, 0x01, 0x00]
        final[8:12] = [126, *self.scale_rgb(clamp_color(colors[126]))]
        final[12:16] = [127, *self.scale_rgb(clamp_color(colors[127]))]
        packets.append(final)
        return packets

    def send_per_key_state(self):
        if not self.device:
            self.status.set("Пользовательский режим сохранён; клавиатура не подключена")
            return False
        with self.per_key_send_lock:
            if not self.custom_mode_active:
                if not self.send(self.make_static(*self.background, custom=True), log=False):
                    return False
                self.custom_mode_active = True
            for packet in self.make_per_key_packets(self.per_key_colors):
                if not self.send(packet, log=False):
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

    def build_cycle_command_row(self, number, command):
        row = tk.Frame(self.cycle_inner, bd=1, relief="groove", padx=7, pady=5)
        row.pack(fill="x", padx=5, pady=4)
        self.cycle_row_widgets.append(row)

        names = [name for name, idx in KEY_INDEX.items() if idx in command["keys"]]
        names_text = ", ".join(names[:7]) + (" …" if len(names) > 7 else "")
        tk.Label(row, text=f"№ {number}", width=5, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(row, text=f"Клавиши: {names_text}", width=28, anchor="w").pack(side="left", padx=4)

        color = tuple(command.get("color", [255, 0, 0]))
        color_button = tk.Button(row, text="Цвет", width=7, bg=rgb_hex(color), fg="#FFFFFF", activebackground=rgb_hex(color), command=lambda n=number - 1: self.change_cycle_command_color(n))
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
                    if not self.send_per_key_state():
                        self.cycle_stop_event.set()
                        break
                    interval = max(0.01, float(command.get("interval", 1.0)))
                    # The interval is explicitly the time until the next command.
                    if self.cycle_stop_event.wait(interval):
                        break
                if not self.cycle_loop_enabled:
                    break
        except Exception as e:
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
            # A damaged settings file must never prevent the application from starting.
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
