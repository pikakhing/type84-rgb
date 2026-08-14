import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import hid
import threading
import time

VID = 0x0C45
PID = 0x8009
INTERFACE = 2
USAGE_PAGE = 0xFF68
USAGE = 0x61
REPORT_SIZE = 64
PACKET_DELAY = 0.020
LED_COUNT = 128

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

# Keyboard positions. Empty cells are intentional gaps in the physical layout.
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
        self.selected_key_name = None
        self.selected_key_index = None
        self.running = False
        self.key_cycle_running = False
        self.key_cycle_thread_obj = None
        self.cycle_jobs = {}
        self.cycle_job_counter = 0
        self.per_key_send_lock = threading.Lock()
        self.custom_mode_active = False
        self.dark_mode = False
        self.cycle_colors = [(255, 0, 0), (0, 0, 255)]
        self.cycle_interval = 1.0
        self.cycle_rows = []

        self.build_ui()
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

        self.make_ui_button(
            whole, "🎨 Выбрать цвет всей клавиатуры", self.choose_background
        ).pack(side="left", padx=4)

        self.make_ui_button(
            whole, "👤 Пользовательский режим", self.set_custom_mode
        ).pack(side="left", padx=4)

        tk.Label(whole, text="Яркость:").pack(side="left", padx=(18, 4))
        self.brightness_var = tk.StringVar(value="255")
        self.brightness_entry = tk.Entry(
            whole, textvariable=self.brightness_var, width=8, justify="center"
        )
        self.brightness_entry.pack(side="left", padx=2)

        self.make_ui_button(
            whole, "Применить", self.apply_brightness
        ).pack(side="left", padx=4)

        self.add_separator()

        self.selected_label = tk.StringVar(value="Клавиша не выбрана")
        tk.Label(self.root, textvariable=self.selected_label, font=("Segoe UI", 11, "bold")).pack(pady=(0, 5))

        keyboard_outer = tk.Frame(self.root)
        keyboard_outer.pack(fill="x", padx=20)
        self.keyboard_frame = tk.Frame(keyboard_outer)
        self.keyboard_frame.pack()
        self.keyboard_buttons = {}
        self.build_keyboard()

        self.add_separator()

        self.user_mode_frame = tk.Frame(self.root, bd=1, relief="groove")
        self.user_mode_frame.pack(fill="x", padx=20, pady=(4, 8))

        tk.Label(
            self.user_mode_frame,
            text="ПОЛЬЗОВАТЕЛЬСКИЙ РЕЖИМ",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(8, 2))

        self.per_key_tab = tk.Frame(self.user_mode_frame)
        self.per_key_tab.pack(fill="x", padx=8, pady=(0, 5))

        self.build_per_key_tab()

        self.cycle_sub_frame = tk.Frame(self.user_mode_frame, bd=1, relief="groove")
        self.cycle_sub_frame.pack(fill="x", padx=8, pady=(4, 8))

        tk.Label(
            self.cycle_sub_frame,
            text="ПЕРЕЛИВАЮЩИЕСЯ КЛАВИШИ",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(7, 2))

        self.cycle_tab = tk.Frame(self.cycle_sub_frame)
        self.cycle_tab.pack(fill="x", padx=5, pady=3)

        self.build_cycle_tab()

        self.log_box = tk.Text(self.root, height=7, state="disabled", wrap="none")
        self.log_box.pack(fill="both", expand=True, padx=25, pady=(4, 12))

    def add_separator(self):
        tk.Frame(self.root, height=1).pack(fill="x", padx=25, pady=8)

    def make_ui_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, relief="raised", bd=1, padx=8, pady=5)

    def build_per_key_tab(self):
        controls = tk.Frame(self.per_key_tab)
        controls.pack(pady=6)
        self.make_ui_button(controls, "🎨 Выбрать цвет", self.choose_key_color).grid(row=0, column=0, padx=4)
        self.make_ui_button(controls, "⬛ Выключить", self.disable_selected_key).grid(row=0, column=1, padx=4)
        self.make_ui_button(controls, "⬛ Выключить все", self.disable_all_keys).grid(row=0, column=2, padx=4)

    def build_cycle_tab(self):
        top = tk.Frame(self.cycle_tab)
        top.pack(fill="x", padx=10, pady=6)
        tk.Label(top, text="Для каждой клавиши: 2–5 цветов, свой интервал и отдельный ▶/■. Можно добавлять сколько угодно клавиш.").pack(side="left")
        self.make_ui_button(top, "+ Добавить клавишу", self.add_cycle_row).pack(side="right")

        self.cycle_canvas = tk.Canvas(self.cycle_tab, height=220, highlightthickness=0)
        self.cycle_scroll = ttk.Scrollbar(self.cycle_tab, orient="vertical", command=self.cycle_canvas.yview)
        self.cycle_inner = tk.Frame(self.cycle_canvas)
        self.cycle_inner.bind("<Configure>", lambda e: self.cycle_canvas.configure(scrollregion=self.cycle_canvas.bbox("all")))
        self.cycle_canvas.create_window((0, 0), window=self.cycle_inner, anchor="nw")
        self.cycle_canvas.configure(yscrollcommand=self.cycle_scroll.set)
        self.cycle_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 8))
        self.cycle_scroll.pack(side="right", fill="y", padx=(0, 10), pady=(0, 8))
        self.add_cycle_row()

    def add_cycle_row(self):
        row = tk.Frame(self.cycle_inner, bd=1, relief="groove", padx=7, pady=5)
        row.pack(fill="x", padx=5, pady=4)
        key_var = tk.StringVar(value=self.selected_key_name or "A")
        count_var = tk.IntVar(value=2)
        colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0), (255, 0, 255)]
        color_buttons = []

        tk.Label(row, text="Клавиша:").pack(side="left")
        combo = ttk.Combobox(row, textvariable=key_var, values=list(KEY_INDEX.keys()), state="readonly", width=10)
        combo.pack(side="left", padx=4)

        tk.Label(row, text="Цветов:").pack(side="left", padx=(10, 2))
        count = ttk.Combobox(row, textvariable=count_var, values=(2, 3, 4, 5), state="readonly", width=4)
        count.pack(side="left")

        color_frame = tk.Frame(row)
        color_frame.pack(side="left", padx=8)

        def redraw_colors():
            for w in color_frame.winfo_children():
                w.destroy()
            color_buttons.clear()
            for i in range(count_var.get()):
                b = tk.Button(color_frame, text=f"{i+1}", width=4, command=lambda i=i: choose_cycle_color(i, colors, color_buttons))
                b.pack(side="left", padx=2)
                color_buttons.append(b)
                b.configure(bg=rgb_hex(colors[i]), activebackground=rgb_hex(colors[i]))

        def choose_cycle_color(i, colors_ref, buttons_ref):
            result = colorchooser.askcolor(initialcolor=rgb_hex(colors_ref[i]), title=f"Цвет {i+1}")
            if result and result[0]:
                colors_ref[i] = tuple(map(int, result[0]))
                buttons_ref[i].configure(bg=rgb_hex(colors_ref[i]), activebackground=rgb_hex(colors_ref[i]))

        count.bind("<<ComboboxSelected>>", lambda e: redraw_colors())
        redraw_colors()

        interval_var = tk.DoubleVar(value=1.0)
        tk.Label(row, text="Интервал:").pack(side="left", padx=(8, 2))
        ttk.Spinbox(row, from_=0.1, to=60.0, increment=0.1, width=6, textvariable=interval_var).pack(side="left")
        tk.Label(row, text="с").pack(side="left", padx=2)

        job_id = None

        def start_row():
            nonlocal job_id
            if job_id is not None:
                self.stop_cycle_job(job_id)
            job_id = self.start_cycle_for_config(key_var.get(), colors, interval_var.get())

        def stop_row():
            nonlocal job_id
            if job_id is not None:
                self.stop_cycle_job(job_id)
                job_id = None

        def remove_row():
            stop_row()
            row.destroy()

        self.make_ui_button(row, "▶ Запустить", start_row).pack(side="left", padx=7)
        self.make_ui_button(row, "■ Стоп", stop_row).pack(side="left", padx=2)
        self.make_ui_button(row, "✕", remove_row).pack(side="right", padx=2)
        row.colors = colors

    # ---------------- Keyboard ----------------
    def build_keyboard(self):
        for row in KEY_LAYOUT:
            for text, index, col, colspan, rowspan in row:
                if not text or index is None:
                    continue
                self.make_key(text, index, row=KEY_LAYOUT.index(row), column=col, colspan=colspan, rowspan=rowspan)
        for c in range(18):
            self.keyboard_frame.grid_columnconfigure(c, weight=1)

    def make_key(self, text, index, row, column, colspan=1, rowspan=1):
        b = tk.Button(self.keyboard_frame, text=text, width=5, height=2, font=("Segoe UI", 9, "bold"),
                      relief="raised", bd=2, command=lambda: self.select_key(text, index))
        b.grid(row=row, column=column, columnspan=colspan, rowspan=rowspan, padx=2, pady=2, sticky="nsew")
        self.keyboard_buttons[index] = b

    def select_key(self, name, index):
        self.selected_key_name = name
        self.selected_key_index = index
        self.selected_label.set(f"Выбрано: {name}  •  LED index {index}")
        self.refresh_key_buttons()

    def refresh_key_buttons(self):
        for idx, b in self.keyboard_buttons.items():
            b.configure(bg=KEY_SELECTED if idx == self.selected_key_index else KEY_BG,
                        fg="#FFFFFF", activebackground=KEY_SELECTED if idx == self.selected_key_index else KEY_BG,
                        activeforeground="#FFFFFF")

    # ---------------- Device ----------------
    def find_device(self):
        for d in hid.enumerate(VID, PID):
            if d.get("interface_number") == INTERFACE and d.get("usage_page") == USAGE_PAGE and d.get("usage") == USAGE:
                return d
        return None

    def scan(self):
        self.log("Поиск Type 84...")
        info = self.find_device()
        if not info:
            self.status.set("❌ Type 84 не найдена")
            self.log("MI_02 не найден.")
            return
        self.device_info = info
        self.status.set("✅ Type 84 найдена")
        self.log(f"Product: {info.get('product_string')}")
        self.log("VID: 0x0C45  PID: 0x8009  Interface: 2  Usage: 0x61")
        self.log(f"Path: {info.get('path')}")

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
            self.log("=== CONNECTED ===")
            self.log("RGB-команды доступны.")
        except Exception as e:
            self.device = None
            self.status.set("❌ Ошибка подключения")
            self.log("Ошибка: " + repr(e))

    # ---------------- Brightness ----------------
    def apply_brightness(self):
        raw = self.brightness_var.get().strip()
        try:
            level = int(raw)
        except ValueError:
            messagebox.showwarning("Яркость", "Введи целое число.")
            return

        # UI does not impose a limit. HID RGB channels themselves are 0..255,
        # so the effective multiplier is safely bounded when creating packets.
        self.brightness_level = level
        if self.custom_mode_active:
            ok = self.send_per_key_state()
        else:
            ok = self.send(self.make_static(*self.background), log=True)

        if ok:
            self.status.set(f"💡 Яркость применена: {level}")

    def scale_rgb(self, color):
        # Treat 255 as full brightness. Values outside the RGB range are
        # accepted in the UI and simply produce the nearest representable
        # output level.
        level = max(0, min(255, self.brightness_level))
        factor = level / 255.0
        return tuple(max(0, min(255, round(c * factor))) for c in color)

    # ---------------- HID protocol ----------------
    def send(self, packet, log=True):
        if not self.device:
            messagebox.showwarning("Нет подключения", "Сначала подключи MI_02.")
            return False
        if len(packet) != REPORT_SIZE:
            raise ValueError("HID report должен быть 64 байта")
        result = self.device.write([0] + list(packet))
        if log:
            self.log("TX: " + " ".join(f"{x:02X}" for x in packet))
            self.log("write() = " + str(result))
        time.sleep(PACKET_DELAY)
        return result >= 0

    def make_static(self, r, g, b, custom=False):
        # Verified layout: AA 23 10 00 00 00 01 00 [01/80] R G B FF 00 00 00 00 05 ... AA 55
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
            self.status.set("👤 Пользовательский режим включён")

    def choose_background(self):
        result = colorchooser.askcolor(initialcolor=rgb_hex(self.background), title="Цвет всей клавиатуры")
        if result and result[0]:
            self.background = tuple(map(int, result[0]))
            if self.send(self.make_static(*self.background)):
                self.custom_mode_active = False
                self.status.set(f"🟢 RGB отправлен: {rgb_hex(self.background)}")

    def choose_key_color(self):
        if self.selected_key_index is None:
            messagebox.showwarning("Клавиша", "Сначала выбери клавишу на виртуальной клавиатуре.")
            return
        result = colorchooser.askcolor(initialcolor=rgb_hex(self.key_color), title="Цвет клавиши")
        if result and result[0]:
            self.key_color = tuple(map(int, result[0]))
            self.send_selected_key()

    def make_per_key_packets(self, colors):
        # Protocol observed in Wireshark: AA 24 38 + byte offset (little-endian) + 00 00 00,
        # then 14 records of [LED index, R, G, B]. Final packet is AA 24 08 F8 01 00 01 00.
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
        # The last report carries LED 126 and 127, exactly like the captured report.
        final[8:12] = [126, *self.scale_rgb(clamp_color(colors[126]))]
        final[12:16] = [127, *self.scale_rgb(clamp_color(colors[127]))]
        packets.append(final)
        return packets

    def send_per_key_state(self):
        if not self.device:
            messagebox.showwarning("Нет подключения", "Сначала подключи MI_02.")
            return False
        with self.per_key_send_lock:
            if not self.custom_mode_active:
                if not self.send(self.make_static(*self.background, custom=True), log=False):
                    return False
                self.custom_mode_active = True
            for packet in self.make_per_key_packets(self.per_key_colors):
                if not self.send(packet, log=False):
                    return False
        self.log("Per-Key state отправлен: 10 data-пакетов + final packet.")
        return True

    def send_selected_key(self):
        if self.selected_key_index is None:
            messagebox.showwarning("Клавиша", "Сначала выбери клавишу.")
            return
        self.per_key_colors[self.selected_key_index] = self.key_color
        self.send_per_key_state()

    def disable_selected_key(self):
        if self.selected_key_index is None:
            messagebox.showwarning("Клавиша", "Сначала выбери клавишу.")
            return
        self.per_key_colors[self.selected_key_index] = (0, 0, 0)
        self.send_per_key_state()

    def disable_all_keys(self):
        self.per_key_colors = [(0, 0, 0) for _ in range(LED_COUNT)]
        self.send_per_key_state()

    # ---------------- Per-key cycles ----------------
    def start_cycle_for_config(self, key_name, colors, interval):
        if key_name not in KEY_INDEX:
            messagebox.showwarning("Клавиша", "Выбрана неизвестная клавиша.")
            return None
        idx = KEY_INDEX[key_name]
        cycle_colors = [tuple(c) for c in colors[:5]]
        interval = max(0.1, float(interval))
        self.cycle_job_counter += 1
        job_id = self.cycle_job_counter
        stop_event = threading.Event()
        self.cycle_jobs[job_id] = stop_event
        self.status.set(f"🌈 Цикл добавлен: {key_name} (LED {idx})")
        thread = threading.Thread(target=self.key_cycle_worker,
                                  args=(job_id, idx, cycle_colors, interval, stop_event), daemon=True)
        thread.start()
        return job_id

    def key_cycle_worker(self, job_id, idx, colors, interval, stop_event):
        n = 0
        try:
            while not stop_event.is_set():
                self.per_key_colors[idx] = colors[n % len(colors)]
                self.send_per_key_state()
                n += 1
                stop_event.wait(interval)
        except Exception as e:
            self.log("Per-key cycle error: " + repr(e))
        finally:
            self.cycle_jobs.pop(job_id, None)

    def stop_cycle_job(self, job_id):
        event = self.cycle_jobs.get(job_id)
        if event:
            event.set()

    def stop_key_cycle(self):
        for event in list(self.cycle_jobs.values()):
            event.set()
        self.cycle_jobs.clear()
        self.key_cycle_running = False
        self.status.set("⏹ Циклы клавиш остановлены")

    # ---------------- Theme ----------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
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

    def style_widget_tree(self, widget, bg, button, fg):
        try:
            cls = widget.winfo_class()
            if cls in ("Frame", "Labelframe"):
                widget.configure(bg=bg)
            elif cls == "Label":
                widget.configure(bg=bg, fg=fg)
            elif cls == "Text":
                widget.configure(bg=button, fg=fg, insertbackground=fg)
            elif cls == "Entry":
                widget.configure(bg=button, fg=fg, insertbackground=fg)
            elif cls == "Button":
                if widget is not self.theme_button and widget in self.keyboard_buttons.values():
                    return
                widget.configure(bg=button, fg=fg, activebackground=button, activeforeground=fg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self.style_widget_tree(child, bg, button, fg)

    # ---------------- Logging / close ----------------
    def log(self, text):
        try:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except tk.TclError:
            pass

    def close(self):
        self.running = False
        self.key_cycle_running = False
        for event in list(self.cycle_jobs.values()):
            event.set()
        self.cycle_jobs.clear()
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
