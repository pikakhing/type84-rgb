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


# =========================================================
# ЗАДЕРЖКИ
# =========================================================

# Для Per-Key сейчас оставляем 20 мс,
# потому что с этой задержкой передача идёт
# стабильно и похоже на официальную.
PER_KEY_DELAY = 0.020

STATIC_DELAY = 0.004


# =========================================================
# STATIC / USER MODE
# =========================================================

MODE_STATIC = 0x01
MODE_USER = 0x80


# =========================================================
# PER-KEY AA 24
# =========================================================

PER_KEY_COUNT = 128

PER_KEY_HEADER = 0xAA
PER_KEY_COMMAND = 0x24
PER_KEY_SUBCOMMAND = 0x38

PER_KEY_LAST_COMMAND = 0x08
PER_KEY_LAST_OFFSET = 0x01


class Type84RGB:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Red Square IO Type 84 RGB"
        )

        self.root.geometry(
            "820x760"
        )

        self.device = None
        self.device_info = None

        self.running = False

        self.background = (
            255,
            0,
            0
        )

        # -------------------------------------------------
        # 128 LED entries
        # -------------------------------------------------

        self.key_colors = [
            (0, 0, 0)
            for _ in range(PER_KEY_COUNT)
        ]

        self.selected_key = 0

        self.selected_color = (
            255,
            0,
            0
        )

        self.build_ui()


    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        title = ttk.Label(
            self.root,
            text="Red Square IO Type 84 RGB",
            font=("Segoe UI", 18, "bold")
        )

        title.pack(
            pady=(18, 5)
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
            font=("Segoe UI", 11)
        ).pack(
            pady=12
        )


        # =================================================
        # DEVICE
        # =================================================

        top = ttk.Frame(
            self.root
        )

        top.pack(
            fill="x",
            padx=30
        )


        ttk.Button(
            top,
            text="1. Найти клавиатуру",
            command=self.scan
        ).pack(
            fill="x",
            pady=4
        )


        ttk.Button(
            top,
            text="2. Подключить MI_02",
            command=self.connect
        ).pack(
            fill="x",
            pady=4
        )


        # =================================================
        # РЕЖИМ ВСЕЙ КЛАВИАТУРЫ
        # =================================================

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=30,
            pady=15
        )


        ttk.Label(
            self.root,
            text="ВСЯ КЛАВИАТУРА",
            font=("Segoe UI", 12, "bold")
        ).pack()


        whole_keyboard = ttk.Frame(
            self.root
        )

        whole_keyboard.pack(
            pady=8
        )


        ttk.Button(
            whole_keyboard,
            text="🎨 Выбрать цвет",
            command=self.choose_background
        ).grid(
            row=0,
            column=0,
            padx=5
        )


        ttk.Button(
            whole_keyboard,
            text="🎯 Статический режим",
            command=self.set_static_mode
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Button(
            whole_keyboard,
            text="🔧 Пользовательский режим",
            command=self.set_user_mode
        ).grid(
            row=0,
            column=2,
            padx=5
        )


        ttk.Button(
            self.root,
            text="🌈 Цикл всей клавиатуры",
            command=self.toggle_cycle
        ).pack(
            pady=10
        )


        # =================================================
        # PER KEY
        # =================================================

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=30,
            pady=15
        )


        ttk.Label(
            self.root,
            text="PER-KEY RGB",
            font=("Segoe UI", 12, "bold")
        ).pack()


        ttk.Label(
            self.root,
            text="Протокол AA 24 • 128 LED entries"
        ).pack(
            pady=3
        )


        perkey = ttk.Frame(
            self.root
        )

        perkey.pack(
            pady=8
        )


        ttk.Label(
            perkey,
            text="Индекс LED:"
        ).grid(
            row=0,
            column=0,
            padx=5
        )


        self.key_var = tk.IntVar(
            value=0
        )


        self.key_spin = tk.Spinbox(
            perkey,
            from_=0,
            to=127,
            width=8,
            textvariable=self.key_var,
            command=self.update_selected_key
        )

        self.key_spin.grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Button(
            perkey,
            text="Выбрать цвет",
            command=self.choose_key_color
        ).grid(
            row=0,
            column=2,
            padx=5
        )


        ttk.Button(
            perkey,
            text="Выключить клавишу",
            command=self.clear_selected_key
        ).grid(
            row=0,
            column=3,
            padx=5
        )


        ttk.Button(
            perkey,
            text="🧪 Отправить Per-Key",
            command=self.send_per_key
        ).grid(
            row=0,
            column=4,
            padx=5
        )


        # =================================================
        # PRESETS
        # =================================================

        presets = ttk.Frame(
            self.root
        )

        presets.pack(
            pady=5
        )


        ttk.Button(
            presets,
            text="A = красный",
            command=lambda:
                self.set_key_preset(
                    0x31,
                    255,
                    0,
                    0
                )
        ).pack(
            side="left",
            padx=5
        )


        ttk.Button(
            presets,
            text="A = синий",
            command=lambda:
                self.set_key_preset(
                    0x31,
                    0,
                    0,
                    255
                )
        ).pack(
            side="left",
            padx=5
        )


        ttk.Button(
            presets,
            text="Все выключить",
            command=self.clear_all_keys
        ).pack(
            side="left",
            padx=5
        )


        # =================================================
        # DELAY
        # =================================================

        delay_frame = ttk.Frame(
            self.root
        )

        delay_frame.pack(
            pady=5
        )


        ttk.Label(
            delay_frame,
            text="Задержка между OUT:"
        ).pack(
            side="left",
            padx=5
        )


        self.delay_var = tk.StringVar(
            value="20"
        )


        ttk.Entry(
            delay_frame,
            textvariable=self.delay_var,
            width=8
        ).pack(
            side="left"
        )


        ttk.Label(
            delay_frame,
            text="мс"
        ).pack(
            side="left",
            padx=5
        )


        # =================================================
        # LOG
        # =================================================

        self.log_box = tk.Text(
            self.root,
            height=18,
            state="disabled"
        )


        self.log_box.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(10, 20)
        )


    # =====================================================
    # LOG
    # =====================================================

    def log(self, text):

        def write_log():

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


        try:

            self.root.after(
                0,
                write_log
            )

        except Exception:
            pass


    # =====================================================
    # DEVICE
    # =====================================================

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
                info.get(
                    "path"
                )
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


            self.log(
                "Manufacturer: "
                + str(
                    self.device
                    .get_manufacturer_string()
                )
            )


            self.log(
                "Product: "
                + str(
                    self.device
                    .get_product_string()
                )
            )


            self.log(
                "RGB-команды доступны."
            )


        except Exception as e:

            self.device = None


            self.status.set(
                "❌ Ошибка подключения"
            )


            self.log(
                "Ошибка: "
                + repr(e)
            )


    # =====================================================
    # HID SEND
    # =====================================================

    def send(self, packet):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return False


        if len(packet) != REPORT_SIZE:

            raise ValueError(
                "HID report должен быть 64 байта"
            )


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


        return result >= 0


    # =====================================================
    # STATIC MODE
    # =====================================================

    def make_static(self, r, g, b):

        packet = [0] * 64


        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10
        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x01
        packet[6] = 0x00
        packet[7] = 0x01


        packet[8] = r
        packet[9] = g
        packet[10] = b
        packet[11] = 0xFF


        packet[12] = 0x00
        packet[13] = 0x00
        packet[14] = 0x00
        packet[15] = 0x05
        packet[16] = 0x00
        packet[17] = 0x00
        packet[18] = 0x00
        packet[19] = 0x00


        packet[20] = 0xAA
        packet[21] = 0x55


        return packet


    def set_static(self, r, g, b):

        self.background = (
            r,
            g,
            b
        )


        try:

            ok = self.send(
                self.make_static(
                    r,
                    g,
                    b
                )
            )


            if ok:

                self.status.set(
                    f"🟢 RGB отправлен: "
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


    # =====================================================
    # USER MODE
    #
    # Официальный пакет:
    #
    # AA 23 10 00 00 01 00 80
    # B6 4C FD FF
    # 00 00 00 05
    # 00 00 00 00
    # AA 55
    #
    # Главное отличие от static:
    # packet[7] = 0x80
    # =====================================================

    def make_user_mode(self):

        packet = [0] * 64


        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10
        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x01
        packet[6] = 0x00
        packet[7] = 0x80


        # Это значение мы видим
        # в официальном пакете пользователя.
        #
        # Пока оставляем его таким,
        # потому что это подтверждено
        # реальным захватом Wireshark.

        packet[8] = 0xB6
        packet[9] = 0x4C
        packet[10] = 0xFD
        packet[11] = 0xFF


        packet[12] = 0x00
        packet[13] = 0x00
        packet[14] = 0x00
        packet[15] = 0x05
        packet[16] = 0x00
        packet[17] = 0x00
        packet[18] = 0x00
        packet[19] = 0x00


        packet[20] = 0xAA
        packet[21] = 0x55


        return packet


    def set_user_mode(self):

        try:

            ok = self.send(
                self.make_user_mode()
            )


            if ok:

                self.status.set(
                    "🎯 Пользовательский режим включён"
                )


                self.log(
                    "User mode: "
                    "AA 23 10 ... 80 ..."
                )


        except Exception as e:

            self.log(
                "USER MODE ERROR: "
                + repr(e)
            )


            messagebox.showerror(
                "Ошибка пользовательского режима",
                repr(e)
            )


    def set_static_mode(self):

        r, g, b = self.background


        try:

            ok = self.send(
                self.make_static(
                    r,
                    g,
                    b
                )
            )


            if ok:

                self.status.set(
                    "💡 Статический режим включён"
                )


        except Exception as e:

            self.log(
                "STATIC MODE ERROR: "
                + repr(e)
            )


    # =====================================================
    # COLOR PICKER
    # =====================================================

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


    # =====================================================
    # CYCLE
    # =====================================================

    def toggle_cycle(self):

        if self.running:

            self.running = False


            self.status.set(
                "⏹ Цикл остановлен"
            )


            return


        self.running = True


        self.status.set(
            "🌈 Цикл запущен"
        )


        threading.Thread(
            target=self.cycle_thread,
            daemon=True
        ).start()


    def cycle_thread(self):

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


    # =====================================================
    # PER-KEY PACKET
    # =====================================================

    def make_per_key_packet(
        self,
        start_index,
        values
    ):

        packet = [0] * 64


        packet[0] = 0xAA
        packet[1] = 0x24
        packet[2] = 0x38


        # Адрес / offset блока
        offset = start_index


        packet[3] = (
            offset
            & 0xFF
        )


        packet[4] = (
            (offset >> 8)
            & 0xFF
        )


        # Остальная структура
        # соответствует найденному
        # официальному AA 24 38.

        pos = 8


        for index, value in values:

            if pos + 3 > 63:

                break


            packet[pos] = (
                index
                & 0xFF
            )

            packet[pos + 1] = value[0]
            packet[pos + 2] = value[1]


            pos += 4


        return packet


    # =====================================================
    # BUILD OFFICIAL PER-KEY
    # =====================================================

    def build_per_key_packets(self):

        packets = []


        # -------------------------------------------------
        # Первые 126 LED
        # -------------------------------------------------

        entries = []


        for index in range(126):

            color = self.key_colors[index]


            if color == (0, 0, 0):

                # Выключенная клавиша:
                # индекс + 000000
                entries.append(
                    (
                        index,
                        (0, 0, 0)
                    )
                )

            else:

                r, g, b = color


                entries.append(
                    (
                        index,
                        (
                            r,
                            g
                        )
                    )
                )


        # -------------------------------------------------
        # Реальная структура официального
        # протокола состоит из блоков по 14 entries.
        #
        # Каждый entry:
        #
        # INDEX + 3 bytes data
        # -------------------------------------------------

        for block_start in range(
            0,
            126,
            14
        ):

            packet = [0] * 64


            packet[0] = 0xAA
            packet[1] = 0x24
            packet[2] = 0x38


            # Официальный offset:
            #
            # 00 00
            # 38
            # 70
            # A8
            # E0
            # 18 01
            # 50 01
            # 88 01
            # C0 01

            offset = (
                block_start * 4
            )


            packet[3] = (
                offset
                & 0xFF
            )


            packet[4] = (
                (offset >> 8)
                & 0xFF
            )


            packet[5] = 0x00
            packet[6] = 0x00
            packet[7] = 0x00


            pos = 8


            for i in range(14):

                index = (
                    block_start + i
                )


                r, g, b = (
                    self.key_colors[index]
                )


                packet[pos] = index


                # Для текущего эксперимента
                # используем RGB как три байта.

                packet[pos + 1] = r
                packet[pos + 2] = g
                packet[pos + 3] = b


                pos += 4


            packets.append(
                packet
            )


        # -------------------------------------------------
        # Последний пакет
        # -------------------------------------------------

        packet = [0] * 64


        packet[0] = 0xAA
        packet[1] = 0x24
        packet[2] = 0x08
        packet[3] = 0xF8
        packet[4] = 0x01
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00


        # Остаток LED 126-127

        packet[8] = 126
        packet[9] = 0
        packet[10] = 0
        packet[11] = 0


        packet[12] = 127
        packet[13] = 0
        packet[14] = 0
        packet[15] = 0


        packets.append(
            packet
        )


        return packets


    # =====================================================
    # SEND PER-KEY
    # =====================================================

    def send_per_key(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return


        try:

            delay_ms = float(
                self.delay_var.get()
            )


            delay = (
                delay_ms / 1000.0
            )


        except Exception:

            delay = (
                PER_KEY_DELAY
            )


        try:

            packets = (
                self.build_per_key_packets()
            )


            self.log(
                ""
            )

            self.log(
                "=== PER-KEY SEND ==="
            )


            for number, packet in enumerate(
                packets,
                start=1
            ):

                self.device.write(
                    [0] + packet
                )


                self.log(
                    f"Per-Key OUT "
                    f"{number}/{len(packets)}: "
                    + " ".join(
                        f"{x:02X}"
                        for x in packet
                    )
                )


                time.sleep(
                    delay
                )


            self.status.set(
                "🟢 Per-Key отправлен"
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


    # =====================================================
    # KEY SELECTION
    # =====================================================

    def update_selected_key(self):

        try:

            value = int(
                self.key_var.get()
            )


            if 0 <= value < PER_KEY_COUNT:

                self.selected_key = value


                self.log(
                    f"Выбран LED index: "
                    f"{value}"
                )


        except Exception:

            pass


    # =====================================================
    # KEY COLOR
    # =====================================================

    def choose_key_color(self):

        color = colorchooser.askcolor(
            title=(
                f"Цвет LED {self.selected_key}"
            )
        )


        if not color or not color[0]:

            return


        r, g, b = map(
            int,
            color[0]
        )


        self.selected_color = (
            r,
            g,
            b
        )


        self.key_colors[
            self.selected_key
        ] = (
            r,
            g,
            b
        )


        self.log(
            f"LED {self.selected_key}: "
            f"#{r:02X}{g:02X}{b:02X}"
        )


    # =====================================================
    # CLEAR ONE KEY
    # =====================================================

    def clear_selected_key(self):

        self.key_colors[
            self.selected_key
        ] = (
            0,
            0,
            0
        )


        self.log(
            f"LED {self.selected_key} выключен"
        )


    # =====================================================
    # CLEAR ALL
    # =====================================================

    def clear_all_keys(self):

        for i in range(
            PER_KEY_COUNT
        ):

            self.key_colors[i] = (
                0,
                0,
                0
            )


        self.log(
            "Все LED выключены в памяти."
        )


        self.log(
            "Для отправки нажми "
            "«Отправить Per-Key»."
        )


    # =====================================================
    # PRESET
    # =====================================================

    def set_key_preset(
        self,
        index,
        r,
        g,
        b
    ):

        if not (
            0 <= index < PER_KEY_COUNT
        ):

            return


        self.key_colors[index] = (
            r,
            g,
            b
        )


        self.selected_key = index


        self.key_var.set(
            index
        )


        self.selected_color = (
            r,
            g,
            b
        )


        self.log(
            f"LED {index} установлен: "
            f"#{r:02X}{g:02X}{b:02X}"
        )


    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.running = False


        try:

            if self.device:

                self.device.close()

        except Exception:

            pass


        self.root.destroy()


# =========================================================
# MAIN
# =========================================================

def main():

    root = tk.Tk()


    app = Type84RGB(
        root
    )


    root.protocol(
        "WM_DELETE_WINDOW",
        app.close
    )


    root.mainloop()


if __name__ == "__main__":

    main()
