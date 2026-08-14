
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import hid
import threading
import time


# ============================================================
# DEVICE
# ============================================================

VID = 0x0C45
PID = 0x8009

INTERFACE = 2
USAGE_PAGE = 0xFF68
USAGE = 0x61

REPORT_SIZE = 64

# Между OUT-пакетами.
PACKET_DELAY = 0.020

# Количество LED в Per-Key протоколе.
LED_COUNT = 128


# ============================================================
# LED INDEX MAP
# ============================================================
#
# Это НЕ порядковые номера физических клавиш.
# Это реальные LED index, которые мы получили экспериментом.
#
# Поэтому здесь специально нет никакого +1, -1,
# смещения после 20 и т.п.
#


KEY_INDEX = {

    # --------------------------------------------------------
    # F-row
    # --------------------------------------------------------

    "Esc": 0,

    "F1": 1,
    "F2": 2,
    "F3": 3,
    "F4": 4,
    "F5": 5,
    "F6": 6,
    "F7": 7,
    "F8": 8,
    "F9": 9,
    "F10": 10,
    "F11": 11,
    "F12": 12,


    # --------------------------------------------------------
    # Number row
    # --------------------------------------------------------

    "Ё": 16,

    "1": 17,
    "2": 18,
    "3": 19,
    "4": 20,
    "5": 21,
    "6": 22,
    "7": 23,
    "8": 24,
    "9": 25,
    "0": 26,

    "-": 27,
    "=": 28,


    # --------------------------------------------------------
    # Q row
    # --------------------------------------------------------

    "Tab": 32,

    "Q": 33,
    "W": 34,
    "E": 35,
    "R": 36,
    "T": 37,
    "Y": 38,
    "U": 39,
    "I": 40,
    "O": 41,
    "P": 42,

    "[": 43,
    "]": 44,


    # --------------------------------------------------------
    # A row
    # --------------------------------------------------------

    "Caps": 48,

    "A": 49,
    "S": 50,
    "D": 51,
    "F": 52,
    "G": 53,
    "H": 54,
    "J": 55,
    "K": 56,
    "L": 57,

    ";": 58,
    "'": 59,

    "\\": 60,


    # --------------------------------------------------------
    # Z row
    # --------------------------------------------------------

    "LShift": 64,

    "Z": 65,
    "X": 66,
    "C": 67,
    "V": 68,
    "B": 69,
    "N": 70,
    "M": 71,

    ",": 72,
    ".": 73,
    "/": 74,

    "RShift": 75,


    # --------------------------------------------------------
    # Bottom row
    # --------------------------------------------------------

    "Enter": 76,

    "LCtrl": 80,
    "Win": 81,
    "LAlt": 82,
    "Space": 83,
    "RAlt": 84,
    "Fn": 85,
    "RCtrl": 87,


    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------

    "Left": 88,
    "Down": 89,
    "Up": 90,
    "Right": 91,

    "Backspace": 92,

    "Insert": 103,
    "Home": 104,
    "PgUp": 105,
    "Delete": 106,
    "End": 107,
    "PgDn": 108,
}


# ============================================================
# UI KEY LABELS
# ============================================================

# Отображаемое имя → LED index.
#
# Отдельно от KEY_INDEX, чтобы можно было сделать нормальную
# клавиатурную раскладку в интерфейсе.


class Type84RGB:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Red Square IO Type 84 RGB"
        )

        self.root.geometry(
            "1050x900"
        )

        self.root.minsize(
            900,
            750
        )


        # ----------------------------------------------------
        # Device
        # ----------------------------------------------------

        self.device = None
        self.device_info = None


        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.background = (
            255,
            0,
            0
        )

        self.key_color = (
            255,
            0,
            0
        )


        # ----------------------------------------------------
        # ВСЕ 128 LED.
        #
        # Очень важно:
        # при изменении одной клавиши остальные цвета
        # НЕ должны превращаться в 00 00 00.
        # ----------------------------------------------------

        self.per_key_colors = [
            (0, 0, 0)
            for _ in range(LED_COUNT)
        ]


        # ----------------------------------------------------
        # Selected key
        # ----------------------------------------------------

        self.selected_key_name = None
        self.selected_key_index = None


        # ----------------------------------------------------
        # Custom cycle
        # ----------------------------------------------------

        self.key_cycle_running = False

        self.key_cycle_thread_obj = None

        self.key_cycle_color_1 = (
            255,
            0,
            0
        )

        self.key_cycle_color_2 = (
            0,
            0,
            255
        )


        # ----------------------------------------------------
        # Whole keyboard cycle
        # ----------------------------------------------------

        self.running = False


        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.build_ui()


        # ----------------------------------------------------
        # Close
        # ----------------------------------------------------

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )


    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        ttk.Label(
            self.root,
            text="Red Square IO Type 84 RGB",
            font=(
                "Segoe UI",
                18,
                "bold"
            )
        ).pack(
            pady=(12, 3)
        )


        ttk.Label(
            self.root,
            text="USB 0C45:8009 • MI_02 • FF68/61"
        ).pack()


        self.status = tk.StringVar(
            value="Устройство не подключено"
        )


        ttk.Label(
            self.root,
            textvariable=self.status,
            font=(
                "Segoe UI",
                11
            )
        ).pack(
            pady=8
        )


        # ----------------------------------------------------
        # Device buttons
        # ----------------------------------------------------

        device_frame = ttk.Frame(
            self.root
        )

        device_frame.pack(
            fill="x",
            padx=25
        )


        ttk.Button(
            device_frame,
            text="1. Найти клавиатуру",
            command=self.scan
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=3
        )


        ttk.Button(
            device_frame,
            text="2. Подключить MI_02",
            command=self.connect
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=3
        )


        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=25,
            pady=10
        )


        # ----------------------------------------------------
        # Whole keyboard
        # ----------------------------------------------------

        ttk.Label(
            self.root,
            text="ВСЯ КЛАВИАТУРА",
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        ).pack()


        whole_frame = ttk.Frame(
            self.root
        )

        whole_frame.pack(
            pady=5
        )


        ttk.Button(
            whole_frame,
            text="🎨 Выбрать цвет всей клавиатуры",
            command=self.choose_background
        ).pack(
            side="left",
            padx=4
        )


        ttk.Button(
            whole_frame,
            text="👤 Пользовательский режим",
            command=self.set_custom_mode
        ).pack(
            side="left",
            padx=4
        )


        ttk.Button(
            whole_frame,
            text="🌈 Цикл всей клавиатуры",
            command=self.toggle_cycle
        ).pack(
            side="left",
            padx=4
        )


        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=25,
            pady=10
        )


        # ----------------------------------------------------
        # Selected key information
        # ----------------------------------------------------

        self.selected_label = tk.StringVar(
            value="Клавиша не выбрана"
        )


        ttk.Label(
            self.root,
            textvariable=self.selected_label,
            font=(
                "Segoe UI",
                11,
                "bold"
            )
        ).pack(
            pady=(2, 5)
        )


        # ----------------------------------------------------
        # Keyboard panel
        # ----------------------------------------------------

        keyboard_outer = ttk.Frame(
            self.root
        )

        keyboard_outer.pack(
            fill="x",
            padx=20
        )


        self.keyboard_frame = tk.Frame(
            keyboard_outer
        )

        self.keyboard_frame.pack()


        self.keyboard_buttons = {}


        self.build_keyboard()


        # ----------------------------------------------------
        # Per-Key controls
        # ----------------------------------------------------

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=25,
            pady=10
        )


        ttk.Label(
            self.root,
            text="PER-KEY",
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        ).pack()


        controls = ttk.Frame(
            self.root
        )

        controls.pack(
            pady=5
        )


        ttk.Button(
            controls,
            text="🎨 Выбрать цвет",
            command=self.choose_key_color
        ).grid(
            row=0,
            column=0,
            padx=4
        )


        ttk.Button(
            controls,
            text="🟢 Отправить цвет",
            command=self.send_selected_key
        ).grid(
            row=0,
            column=1,
            padx=4
        )


        ttk.Button(
            controls,
            text="⬛ Выключить",
            command=self.disable_selected_key
        ).grid(
            row=0,
            column=2,
            padx=4
        )


        ttk.Button(
            controls,
            text="⬛ Выключить все",
            command=self.disable_all_keys
        ).grid(
            row=0,
            column=3,
            padx=4
        )


        # ----------------------------------------------------
        # Cycle controls
        # ----------------------------------------------------

        cycle_frame = ttk.LabelFrame(
            self.root,
            text="Цикл выбранной клавиши"
        )

        cycle_frame.pack(
            pady=7,
            padx=20
        )


        ttk.Button(
            cycle_frame,
            text="Цвет 1",
            command=self.choose_cycle_color_1
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )


        self.cycle_color_1_label = tk.StringVar(
            value="#FF0000"
        )


        ttk.Label(
            cycle_frame,
            textvariable=self.cycle_color_1_label
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Button(
            cycle_frame,
            text="Цвет 2",
            command=self.choose_cycle_color_2
        ).grid(
            row=0,
            column=2,
            padx=5
        )


        self.cycle_color_2_label = tk.StringVar(
            value="#0000FF"
        )


        ttk.Label(
            cycle_frame,
            textvariable=self.cycle_color_2_label
        ).grid(
            row=0,
            column=3,
            padx=5
        )


        ttk.Label(
            cycle_frame,
            text="Интервал:"
        ).grid(
            row=0,
            column=4,
            padx=(15, 3)
        )


        self.cycle_interval_var = tk.DoubleVar(
            value=1.0
        )


        ttk.Spinbox(
            cycle_frame,
            from_=0.1,
            to=60.0,
            increment=0.1,
            textvariable=self.cycle_interval_var,
            width=7
        ).grid(
            row=0,
            column=5,
            padx=3
        )


        ttk.Label(
            cycle_frame,
            text="сек."
        ).grid(
            row=0,
            column=6,
            padx=3
        )


        self.cycle_button = ttk.Button(
            cycle_frame,
            text="▶ Запустить цикл",
            command=self.toggle_selected_key_cycle
        )


        self.cycle_button.grid(
            row=0,
            column=7,
            padx=8
        )


        # ----------------------------------------------------
        # Log
        # ----------------------------------------------------

        self.log_box = tk.Text(
            self.root,
            height=8,
            state="disabled"
        )


        self.log_box.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(5, 15)
        )


    # ========================================================
    # VISUAL KEYBOARD
    # ========================================================

    def make_key(
        self,
        text,
        index,
        row,
        column,
        width=5,
        colspan=1
    ):

        button = tk.Button(
            self.keyboard_frame,
            text=text,
            width=width,
            height=2,
            relief="raised",
            command=lambda: self.select_key(
                text,
                index
            )
        )


        button.grid(
            row=row,
            column=column,
            columnspan=colspan,
            padx=2,
            pady=2,
            sticky="nsew"
        )


        self.keyboard_buttons[index] = button


    def build_keyboard(self):

        # ----------------------------------------------------
        # F-row
        # ----------------------------------------------------

        self.make_key(
            "Esc",
            0,
            0,
            0,
            width=6
        )


        for i in range(1, 13):

            self.make_key(
                f"F{i}",
                i,
                0,
                i,
                width=4
            )


        # ----------------------------------------------------
        # Number row
        # ----------------------------------------------------

        number_keys = [
            ("Ё", 16),
            ("1", 17),
            ("2", 18),
            ("3", 19),
            ("4", 20),
            ("5", 21),
            ("6", 22),
            ("7", 23),
            ("8", 24),
            ("9", 25),
            ("0", 26),
            ("-", 27),
            ("=", 28),
        ]


        for col, (text, index) in enumerate(
            number_keys
        ):

            self.make_key(
                text,
                index,
                1,
                col,
                width=5
            )


        self.make_key(
            "Backspace",
            92,
            1,
            13,
            width=11
        )


        # ----------------------------------------------------
        # Q row
        # ----------------------------------------------------

        q_keys = [
            ("Tab", 32),
            ("Q", 33),
            ("W", 34),
            ("E", 35),
            ("R", 36),
            ("T", 37),
            ("Y", 38),
            ("U", 39),
            ("I", 40),
            ("O", 41),
            ("P", 42),
            ("[", 43),
            ("]", 44),
        ]


        for col, (text, index) in enumerate(
            q_keys
        ):

            self.make_key(
                text,
                index,
                2,
                col,
                width=5
            )


        self.make_key(
            "Enter",
            76,
            2,
            13,
            width=7
        )


        # ----------------------------------------------------
        # A row
        # ----------------------------------------------------

        a_keys = [
            ("Caps", 48),
            ("A", 49),
            ("S", 50),
            ("D", 51),
            ("F", 52),
            ("G", 53),
            ("H", 54),
            ("J", 55),
            ("K", 56),
            ("L", 57),
            (";", 58),
            ("'", 59),
            ("\\", 60),
        ]


        for col, (text, index) in enumerate(
            a_keys
        ):

            self.make_key(
                text,
                index,
                3,
                col,
                width=5
            )


        # ----------------------------------------------------
        # Z row
        # ----------------------------------------------------

        z_keys = [
            ("LShift", 64),
            ("Z", 65),
            ("X", 66),
            ("C", 67),
            ("V", 68),
            ("B", 69),
            ("N", 70),
            ("M", 71),
            (",", 72),
            (".", 73),
            ("/", 74),
            ("RShift", 75),
        ]


        for col, (text, index) in enumerate(
            z_keys
        ):

            self.make_key(
                text,
                index,
                4,
                col,
                width=5
            )


        # ----------------------------------------------------
        # Bottom row
        # ----------------------------------------------------

        bottom = [
            ("LCtrl", 80),
            ("Win", 81),
            ("LAlt", 82),
            ("Space", 83),
            ("RAlt", 84),
            ("Fn", 85),
            ("RCtrl", 87),
        ]


        col = 0


        for text, index in bottom:

            width = 6

            if text == "Space":
                width = 28

            self.make_key(
                text,
                index,
                5,
                col,
                width=width
            )

            col += 1


        # ----------------------------------------------------
        # Navigation
        # ----------------------------------------------------

        self.make_key(
            "Insert",
            103,
            6,
            10,
            width=7
        )


        self.make_key(
            "Home",
            104,
            6,
            11,
            width=7
        )


        self.make_key(
            "PgUp",
            105,
            6,
            12,
            width=7
        )


        self.make_key(
            "Delete",
            106,
            7,
            10,
            width=7
        )


        self.make_key(
            "End",
            107,
            7,
            11,
            width=7
        )


        self.make_key(
            "PgDn",
            108,
            7,
            12,
            width=7
        )


        # ----------------------------------------------------
        # Arrows
        # ----------------------------------------------------

        self.make_key(
            "↑",
            90,
            7,
            8,
            width=5
        )


        self.make_key(
            "←",
            88,
            8,
            7,
            width=5
        )


        self.make_key(
            "↓",
            89,
            8,
            8,
            width=5
        )


        self.make_key(
            "→",
            91,
            8,
            9,
            width=5
        )


    # ========================================================
    # KEY SELECTION
    # ========================================================

    def select_key(
        self,
        name,
        index
    ):

        # Убираем выделение с предыдущей клавиши.

        if (
            self.selected_key_index is not None
            and
            self.selected_key_index
            in self.keyboard_buttons
        ):

            old_button = self.keyboard_buttons[
                self.selected_key_index
            ]

            old_button.config(
                relief="raised",
                bd=2
            )


        self.selected_key_name = name
        self.selected_key_index = index


        # Выделяем новую.

        button = self.keyboard_buttons[
            index
        ]

        button.config(
            relief="sunken",
            bd=4
        )


        self.selected_label.set(
            f"Выбрано: {name}   "
            f"LED index: {index}   "
            f"0x{index:02X}"
        )


        r, g, b = self.per_key_colors[
            index
        ]


        self.log(
            f"Выбрана {name}: "
            f"LED {index} "
            f"(0x{index:02X}), "
            f"цвет #{r:02X}{g:02X}{b:02X}"
        )


    # ========================================================
    # LOG
    # ========================================================

    def log(
        self,
        text
    ):

        self.log_box.config(
            state="normal"
        )

        self.log_box.insert(
            "end",
            text + "\n"
        )

        self.log_box.see(
            "end"
        )

        self.log_box.config(
            state="disabled"
        )


    # ========================================================
    # DEVICE
    # ========================================================

    def find_device(self):

        devices = hid.enumerate(
            VID,
            PID
        )


        for d in devices:

            if (
                d.get("interface_number")
                == INTERFACE

                and

                d.get("usage_page")
                == USAGE_PAGE

                and

                d.get("usage")
                == USAGE
            ):

                return d


        return None


    def scan(self):

        self.log(
            "Поиск Type 84..."
        )


        info = self.find_device()


        if not info:

            self.status.set(
                "❌ Type 84 не найдена"
            )

            self.log(
                "MI_02 не найден."
            )

            return


        self.device_info = info


        self.status.set(
            "✅ Type 84 найдена"
        )


        self.log("")
        self.log(
            "=== DEVICE ==="
        )

        self.log(
            "Product: "
            + str(
                info.get(
                    "product_string"
                )
            )
        )

        self.log(
            "VID: 0x0C45"
        )

        self.log(
            "PID: 0x8009"
        )

        self.log(
            "Interface: 2"
        )

        self.log(
            "Usage Page: 0xFF68"
        )

        self.log(
            "Usage: 0x61"
        )

        self.log(
            "Path: "
            + str(
                info.get("path")
            )
        )


    def connect(self):

        if not self.device_info:

            self.device_info = (
                self.find_device()
            )


        if not self.device_info:

            messagebox.showerror(
                "Ошибка",
                "Сначала нажми «Найти клавиатуру»."
            )

            return


        try:

            if self.device:

                self.device.close()


            self.device = hid.device()


            self.device.open_path(
                self.device_info["path"]
            )


            self.status.set(
                "🟢 MI_02 подключён"
            )


            self.log("")
            self.log(
                "=== CONNECTED ==="
            )


            try:

                self.log(
                    "Manufacturer: "
                    + str(
                        self.device.get_manufacturer_string()
                    )
                )

                self.log(
                    "Product: "
                    + str(
                        self.device.get_product_string()
                    )
                )

            except Exception:

                pass


        except Exception as e:

            self.device = None


            self.status.set(
                "❌ Ошибка подключения"
            )


            self.log(
                "Ошибка: "
                + repr(e)
            )


    # ========================================================
    # HID SEND
    # ========================================================

    def send(
        self,
        packet,
        delay=True
    ):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return False


        if len(packet) != REPORT_SIZE:

            raise ValueError(
                "HID report должен быть "
                "ровно 64 байта"
            )


        # Для данного интерфейса hidapi
        # перед payload добавляется report ID 0.

        result = self.device.write(
            [0] + packet
        )


        self.log(
            "TX: "
            + " ".join(
                f"{x:02X}"
                for x in packet
            )
        )


        self.log(
            "write() = "
            + str(result)
        )


        if delay:

            time.sleep(
                PACKET_DELAY
            )


        return result >= 0


    # ========================================================
    # STATIC MODE
    # ========================================================

    def make_static(
        self,
        r,
        g,
        b
    ):

        packet = [
            0
        ] * REPORT_SIZE


        # AA 23 10
        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10


        # 00 00 00 01 00
        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00


        # 01 = static
        packet[8] = 0x01


        packet[9] = r
        packet[10] = g
        packet[11] = b
        packet[12] = 0xFF


        # 00 00 00 00 05
        packet[13] = 0x00
        packet[14] = 0x00
        packet[15] = 0x00
        packet[16] = 0x00
        packet[17] = 0x05


        packet[18] = 0x00
        packet[19] = 0x00
        packet[20] = 0x00


        packet[21] = 0xAA
        packet[22] = 0x55


        return packet


    # ========================================================
    # CUSTOM MODE
    # ========================================================

    def make_custom_mode(
        self,
        r=0xB6,
        g=0x4C,
        b=0xFD
    ):

        packet = [
            0
        ] * REPORT_SIZE


        # AA 23 10
        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10


        # 00 00 00 01 00
        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00


        # 80 = пользовательский режим
        packet[8] = 0x80


        packet[9] = r
        packet[10] = g
        packet[11] = b
        packet[12] = 0xFF


        # 00 00 00 00 05
        packet[13] = 0x00
        packet[14] = 0x00
        packet[15] = 0x00
        packet[16] = 0x00
        packet[17] = 0x05


        packet[18] = 0x00
        packet[19] = 0x00
        packet[20] = 0x00


        packet[21] = 0xAA
        packet[22] = 0x55


        return packet


    def set_custom_mode(self):

        try:

            packet = self.make_custom_mode(
                *self.background
            )


            if self.send(packet):

                self.status.set(
                    "🟢 Пользовательский режим включён"
                )

                self.log(
                    "Custom mode = 0x80"
                )


        except Exception as e:

            self.log(
                "CUSTOM MODE ERROR: "
                + repr(e)
            )

            messagebox.showerror(
                "Ошибка",
                repr(e)
            )


    # ========================================================
    # WHOLE KEYBOARD COLOR
    # ========================================================

    def set_static(
        self,
        r,
        g,
        b
    ):

        self.background = (
            r,
            g,
            b
        )


        try:

            packet = self.make_static(
                r,
                g,
                b
            )


            if self.send(packet):

                self.status.set(
                    f"🟢 RGB: "
                    f"#{r:02X}{g:02X}{b:02X}"
                )


        except Exception as e:

            self.log(
                "RGB ERROR: "
                + repr(e)
            )


            messagebox.showerror(
                "RGB ошибка",
                repr(e)
            )


    def choose_background(self):

        color = colorchooser.askcolor(
            title="Цвет всей клавиатуры"
        )


        if not color or not color[0]:

            return


        r, g, b = map(
            int,
            color[0]
        )


        self.set_static(
            r,
            g,
            b
        )


    # ========================================================
    # KEY COLOR
    # ========================================================

    def choose_key_color(self):

        color = colorchooser.askcolor(
            title="Цвет выбранной клавиши"
        )


        if not color or not color[0]:

            return


        self.key_color = tuple(
            map(
                int,
                color[0]
            )
        )


        r, g, b = self.key_color


        self.log(
            "Цвет выбранной клавиши: "
            f"#{r:02X}{g:02X}{b:02X}"
        )


    # ========================================================
    # MAKE PER-KEY PACKETS
    # ========================================================

    def make_per_key_packets(self):

        packets = []


        # 128 LED.
        #
        # В каждом обычном пакете 14 записей.
        #
        # 9 * 14 = 126
        # последний пакет содержит 126 и 127.
        #

        for packet_number in range(10):

            packet = [
                0
            ] * REPORT_SIZE


            start_index = (
                packet_number * 14
            )


            offset = (
                start_index * 4
            )


            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            packet[0] = 0xAA
            packet[1] = 0x24


            if packet_number == 9:

                # Последний пакет:
                # AA 24 08 ...

                packet[2] = 0x08

            else:

                # Остальные:
                # AA 24 38 ...

                packet[2] = 0x38


            # offset
            packet[3] = (
                offset & 0xFF
            )

            packet[4] = (
                (offset >> 8)
                & 0xFF
            )


            packet[5] = 0x00


            # Только последний пакет имеет 01.
            packet[6] = (
                0x01
                if packet_number == 9
                else 0x00
            )


            packet[7] = 0x00


            # ------------------------------------------------
            # 14 LED records
            # ------------------------------------------------

            for slot in range(14):

                index = (
                    start_index
                    + slot
                )


                if index >= LED_COUNT:

                    break


                pos = (
                    8
                    + slot * 4
                )


                r, g, b = (
                    self.per_key_colors[
                        index
                    ]
                )


                # index
                packet[pos] = index


                # RGB
                packet[pos + 1] = r
                packet[pos + 2] = g
                packet[pos + 3] = b


            packets.append(
                packet
            )


        return packets


    # ========================================================
    # SEND ALL PER-KEY PACKETS
    # ========================================================

    def send_all_per_key_packets(self):

        packets = (
            self.make_per_key_packets()
        )


        for number, packet in enumerate(
            packets,
            start=1
        ):

            if not self.send(
                packet,
                delay=True
            ):

                return False


            self.log(
                f"Per-Key packet "
                f"{number}/10 отправлен"
            )


        return True


    # ========================================================
    # SEND SELECTED KEY
    # ========================================================

    def send_selected_key(self):

        if self.selected_key_index is None:

            messagebox.showwarning(
                "Клавиша не выбрана",
                "Сначала нажми на клавишу "
                "на панели."
            )

            return


        index = (
            self.selected_key_index
        )


        r, g, b = (
            self.key_color
        )


        # ----------------------------------------------------
        # Сохраняем цвет.
        #
        # Это ключевой момент:
        # остальные LED НЕ обнуляются.
        # ----------------------------------------------------

        self.per_key_colors[index] = (
            r,
            g,
            b
        )


        self.log(
            f"LED {index} "
            f"({self.selected_key_name}) "
            f"= #{r:02X}{g:02X}{b:02X}"
        )


        try:

            # Перед изменением отдельных клавиш
            # пользовательский режим должен быть включён.

            if not self.send_all_per_key_packets():

                self.status.set(
                    "❌ Ошибка Per-Key"
                )

                return


            self.status.set(
                f"🟢 {self.selected_key_name}: "
                f"#{r:02X}{g:02X}{b:02X}"
            )


        except Exception as e:

            self.log(
                "PER-KEY ERROR: "
                + repr(e)
            )


            messagebox.showerror(
                "Per-Key ошибка",
                repr(e)
            )


    # ========================================================
    # DISABLE SELECTED
    # ========================================================

    def disable_selected_key(self):

        if self.selected_key_index is None:

            messagebox.showwarning(
                "Клавиша не выбрана",
                "Сначала выбери клавишу."
            )

            return


        index = (
            self.selected_key_index
        )


        # RGB 0 = выключено.
        self.per_key_colors[index] = (
            0,
            0,
            0
        )


        self.log(
            f"LED {index} "
            f"({self.selected_key_name}) "
            f"выключен"
        )


        try:

            if self.send_all_per_key_packets():

                self.status.set(
                    f"⬛ {self.selected_key_name} выключена"
                )


        except Exception as e:

            self.log(
                "DISABLE ERROR: "
                + repr(e)
            )


    # ========================================================
    # DISABLE ALL
    # ========================================================

    def disable_all_keys(self):

        for i in range(
            LED_COUNT
        ):

            self.per_key_colors[i] = (
                0,
                0,
                0
            )


        try:

            if self.send_all_per_key_packets():

                self.status.set(
                    "⬛ Все LED выключены"
                )


        except Exception as e:

            self.log(
                "DISABLE ALL ERROR: "
                + repr(e)
            )


    # ========================================================
    # CYCLE COLOR PICKERS
    # ========================================================

    def choose_cycle_color_1(self):

        color = colorchooser.askcolor(
            title="Первый цвет цикла"
        )


        if not color or not color[0]:

            return


        self.key_cycle_color_1 = tuple(
            map(
                int,
                color[0]
            )
        )


        r, g, b = (
            self.key_cycle_color_1
        )


        self.cycle_color_1_label.set(
            f"#{r:02X}{g:02X}{b:02X}"
        )


    def choose_cycle_color_2(self):

        color = colorchooser.askcolor(
            title="Второй цвет цикла"
        )


        if not color or not color[0]:

            return


        self.key_cycle_color_2 = tuple(
            map(
                int,
                color[0]
            )
        )


        r, g, b = (
            self.key_cycle_color_2
        )


        self.cycle_color_2_label.set(
            f"#{r:02X}{g:02X}{b:02X}"
        )


    # ========================================================
    # SELECTED KEY CYCLE
    # ========================================================

    def toggle_selected_key_cycle(self):

        if self.selected_key_index is None:

            messagebox.showwarning(
                "Клавиша не выбрана",
                "Сначала выбери клавишу."
            )

            return


        if self.key_cycle_running:

            self.key_cycle_running = False

            self.cycle_button.config(
                text="▶ Запустить цикл"
            )


            self.status.set(
                "⏹ Цикл клавиши остановлен"
            )


            return


        try:

            interval = float(
                self.cycle_interval_var.get()
            )

        except Exception:

            messagebox.showerror(
                "Ошибка",
                "Интервал должен быть числом."
            )

            return


        if interval < 0.1:

            messagebox.showerror(
                "Ошибка",
                "Минимальный интервал: 0.1 сек."
            )

            return


        self.key_cycle_running = True


        self.cycle_button.config(
            text="⏹ Остановить цикл"
        )


        self.status.set(
            f"🌈 Цикл: "
            f"{self.selected_key_name}"
        )


        self.key_cycle_thread_obj = (
            threading.Thread(
                target=self.selected_key_cycle_thread,
                args=(interval,),
                daemon=True
            )
        )


        self.key_cycle_thread_obj.start()


    def selected_key_cycle_thread(
        self,
        interval
    ):

        color_index = 0


        while self.key_cycle_running:

            # ------------------------------------------------
            # Очень важно:
            # фиксируем выбранную клавишу в начале итерации.
            # ------------------------------------------------

            index = (
                self.selected_key_index
            )


            if index is None:

                break


            if color_index == 0:

                color = (
                    self.key_cycle_color_1
                )

            else:

                color = (
                    self.key_cycle_color_2
                )


            r, g, b = color


            # Сохраняем только эту клавишу.
            #
            # Остальные значения уже находятся
            # в self.per_key_colors.

            self.per_key_colors[index] = (
                r,
                g,
                b
            )


            try:

                packets = (
                    self.make_per_key_packets()
                )


                for packet in packets:

                    if not self.key_cycle_running:

                        break


                    if not self.device:

                        self.key_cycle_running = False

                        break


                    result = (
                        self.device.write(
                            [0] + packet
                        )
                    )


                    if result < 0:

                        self.log(
                            "Cycle write error"
                        )

                        self.key_cycle_running = False

                        break


                    time.sleep(
                        PACKET_DELAY
                    )


            except Exception as e:

                self.log(
                    "KEY CYCLE ERROR: "
                    + repr(e)
                )


                self.key_cycle_running = False

                break


            color_index = (
                1 - color_index
            )


            # Интервал между сменами цветов.
            #
            # Здесь не используем time.sleep(interval)
            # одним большим куском, чтобы остановка
            # цикла реагировала быстрее.

            elapsed = 0.0


            while (
                elapsed < interval
                and
                self.key_cycle_running
            ):

                time.sleep(
                    0.05
                )

                elapsed += 0.05


        # Tkinter должен изменяться из главного потока.
        self.root.after(
            0,
            lambda: self.cycle_button.config(
                text="▶ Запустить цикл"
            )
        )


    # ========================================================
    # WHOLE KEYBOARD CYCLE
    # ========================================================

    def toggle_cycle(self):

        if self.running:

            self.running = False

            self.status.set(
                "⏹ Цикл остановлен"
            )

            return


        self.running = True

        self.status.set(
            "🌈 Цикл всей клавиатуры"
        )


        threading.Thread(
            target=self.cycle_thread,
            daemon=True
        ).start()


    def cycle_thread(self):

        # Это старый цикл всей клавиатуры.
        #
        # Он оставлен отдельно от нового Per-Key цикла.

        colors = [
            (255, 0, 0),
            (255, 80, 0),
            (255, 255, 0),
            (0, 255, 0),
            (0, 255, 255),
            (0, 80, 255),
            (120, 0, 255),
            (255, 0, 255),
        ]


        while self.running:

            for r, g, b in colors:

                if not self.running:

                    break


                try:

                    packet = self.make_static(
                        r,
                        g,
                        b
                    )


                    if self.device:

                        self.device.write(
                            [0] + packet
                        )


                    self.background = (
                        r,
                        g,
                        b
                    )


                except Exception as e:

                    self.log(
                        "Cycle error: "
                        + repr(e)
                    )


                    self.running = False

                    break


                time.sleep(
                    1.0
                )


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.running = False

        self.key_cycle_running = False


        try:

            if self.device:

                self.device.close()

        except Exception:

            pass


        self.root.destroy()


# ============================================================
# MAIN
# ============================================================

def main():

    root = tk.Tk()

    app = Type84RGB(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()

