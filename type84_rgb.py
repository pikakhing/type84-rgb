
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

# ---------------------------------------------------------
# Рабочий Static RGB
# ---------------------------------------------------------

STATIC_DELAY = 0.002  # 2 ms

# ---------------------------------------------------------
# Per-Key AA 24
# ---------------------------------------------------------

PER_KEY_DELAY = 0.002  # 2 ms между OUT report'ами

PER_KEY_HEADER = 0xAA
PER_KEY_COMMAND = 0x24
PER_KEY_SUBCOMMAND = 0x38

PER_KEY_COUNT = 128

# Последний пакет имеет другой заголовок:
# AA 24 08 F8 01 00 01 00 ...
PER_KEY_LAST_COMMAND = 0x08
PER_KEY_LAST_OFFSET = 0x01


class Type84RGB:

    def __init__(self, root):

        self.root = root

        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("820x760")

        self.device = None
        self.device_info = None

        self.running = False

        self.background = (255, 0, 0)

        # 128 LED/key entries.
        # Значение каждой клавиши = (R, G, B)
        self.key_colors = [
            (0, 0, 0)
            for _ in range(PER_KEY_COUNT)
        ]

        self.selected_key = 0
        self.selected_color = (255, 0, 0)

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
        title.pack(pady=(18, 5))

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
        ).pack(pady=12)

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=30)

        ttk.Button(
            top,
            text="1. Найти клавиатуру",
            command=self.scan
        ).pack(fill="x", pady=4)

        ttk.Button(
            top,
            text="2. Подключить MI_02",
            command=self.connect
        ).pack(fill="x", pady=4)

        # -------------------------------------------------
        # Static RGB
        # -------------------------------------------------

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=15)

        ttk.Label(
            self.root,
            text="ТЕСТ ВСЕЙ КЛАВИАТУРЫ",
            font=("Segoe UI", 12, "bold")
        ).pack()

        colors = ttk.Frame(self.root)
        colors.pack(pady=8)

        ttk.Button(
            colors,
            text="🔴 Красный",
            command=lambda: self.set_static(255, 0, 0)
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            colors,
            text="🟢 Зелёный",
            command=lambda: self.set_static(0, 255, 0)
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            colors,
            text="🔵 Синий",
            command=lambda: self.set_static(0, 0, 255)
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            colors,
            text="⚪ Белый",
            command=lambda: self.set_static(255, 255, 255)
        ).grid(row=0, column=3, padx=5)

        ttk.Button(
            colors,
            text="🎨 Свой цвет",
            command=self.choose_background
        ).grid(row=0, column=4, padx=5)

        ttk.Button(
            self.root,
            text="🌈 Цикл всей клавиатуры",
            command=self.toggle_cycle
        ).pack(pady=10)

        # -------------------------------------------------
        # Per-Key
        # -------------------------------------------------

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=15)

        ttk.Label(
            self.root,
            text="PER-KEY RGB",
            font=("Segoe UI", 12, "bold")
        ).pack()

        ttk.Label(
            self.root,
            text="Протокол AA 24 • 128 LED entries"
        ).pack(pady=3)

        perkey = ttk.Frame(self.root)
        perkey.pack(pady=8)

        ttk.Label(
            perkey,
            text="Индекс клавиши / LED:"
        ).grid(row=0, column=0, padx=5)

        self.key_var = tk.IntVar(value=0)

        self.key_spin = tk.Spinbox(
            perkey,
            from_=0,
            to=127,
            width=8,
            textvariable=self.key_var,
            command=self.update_selected_key
        )
        self.key_spin.grid(row=0, column=1, padx=5)

        ttk.Button(
            perkey,
            text="Выбрать цвет",
            command=self.choose_key_color
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            perkey,
            text="Выключить клавишу",
            command=self.clear_selected_key
        ).grid(row=0, column=3, padx=5)

        ttk.Button(
            perkey,
            text="🧪 Отправить Per-Key",
            command=self.send_per_key
        ).grid(row=0, column=4, padx=5)

        # -------------------------------------------------
        # Presets
        # -------------------------------------------------

        presets = ttk.Frame(self.root)
        presets.pack(pady=5)

        ttk.Button(
            presets,
            text="A = красный",
            command=lambda: self.set_key_preset(0x31, 255, 0, 0)
        ).pack(side="left", padx=5)

        ttk.Button(
            presets,
            text="A = синий",
            command=lambda: self.set_key_preset(0x31, 0, 0, 255)
        ).pack(side="left", padx=5)

        ttk.Button(
            presets,
            text="Все выключить",
            command=self.clear_all_keys
        ).pack(side="left", padx=5)

        # -------------------------------------------------
        # Delay
        # -------------------------------------------------

        delay_frame = ttk.Frame(self.root)
        delay_frame.pack(pady=5)

        ttk.Label(
            delay_frame,
            text="Задержка между OUT:"
        ).pack(side="left", padx=5)

        self.delay_var = tk.StringVar(
            value="2.0"
        )

        ttk.Entry(
            delay_frame,
            textvariable=self.delay_var,
            width=8
        ).pack(side="left")

        ttk.Label(
            delay_frame,
            text="мс"
        ).pack(side="left", padx=5)

        # -------------------------------------------------
        # Log
        # -------------------------------------------------

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
    # Logging
    # =====================================================

    def log(self, text):

        def write_log():

            self.log_box.config(state="normal")

            self.log_box.insert(
                "end",
                text + "\n"
            )

            self.log_box.see("end")

            self.log_box.config(
                state="disabled"
            )

        try:
            self.root.after(0, write_log)
        except Exception:
            pass

    # =====================================================
    # Device
    # =====================================================

    def find_device(self):

        devices = hid.enumerate(
            VID,
            PID
        )

        for d in devices:

            if (
                d.get("interface_number") == INTERFACE
                and d.get("usage_page") == USAGE_PAGE
                and d.get("usage") == USAGE
            ):
                return d

        return None

    def scan(self):

        self.log("Поиск Type 84...")

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
        self.log("=== DEVICE ===")

        self.log(
            "Product: "
            + str(info.get("product_string"))
        )

        self.log("VID: 0x0C45")
        self.log("PID: 0x8009")
        self.log("Interface: 2")
        self.log("Usage Page: 0xFF68")
        self.log("Usage: 0x61")

        self.log(
            "Path: "
            + str(info.get("path"))
        )

    def connect(self):

        if not self.device_info:
            self.device_info = self.find_device()

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
            self.log("=== CONNECTED ===")

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
    # Static RGB
    # =====================================================

    def make_static(self, r, g, b):

        packet = [0] * 64

        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10
        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00
        packet[8] = 0x01

        packet[9] = r
        packet[10] = g
        packet[11] = b

        packet[12] = 0xFF

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
    # Color picker
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
    # Cycle
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

                time.sleep(1.0)

    # =====================================================
    # Per-Key helpers
    # =====================================================

    def update_selected_key(self):

        try:
            key = int(
                self.key_var.get()
            )

            if 0 <= key < PER_KEY_COUNT:
                self.selected_key = key

        except Exception:
            pass

    def choose_key_color(self):

        self.update_selected_key()

        color = colorchooser.askcolor(
            title=f"Цвет LED {self.selected_key}"
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
            f"RGB({r}, {g}, {b})"
        )

    def set_key_preset(
        self,
        key,
        r,
        g,
        b
    ):

        if not (
            0 <= key < PER_KEY_COUNT
        ):
            return

        self.key_colors[key] = (
            r,
            g,
            b
        )

        self.key_var.set(key)

        self.log(
            f"LED {key}: "
            f"RGB({r}, {g}, {b})"
        )

        self.send_per_key()

    def clear_selected_key(self):

        self.update_selected_key()

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

    def clear_all_keys(self):

        self.key_colors = [
            (0, 0, 0)
            for _ in range(PER_KEY_COUNT)
        ]

        self.log(
            "Все 128 LED выключены."
        )

    # =====================================================
    # Per-Key packet construction
    # =====================================================

    def make_per_key_packets(self):

        """
        Строим ровно 10 report'ов по структуре
        официального test1.txt.

        Первые 9:

            AA 24 38 OFFSET ...
        
        Последний:

            AA 24 08 F8 01 ...

        Каждая LED entry:

            INDEX R G B

        Всего 128 entries.
        """

        packets = []

        # ---------------------------------------------
        # Первые 9 packets содержат по 14 entries
        # ---------------------------------------------

        for chunk in range(9):

            start = chunk * 14

            packet = [0] * 64

            packet[0] = 0xAA
            packet[1] = 0x24
            packet[2] = 0x38

            # Значение из официальных пакетов:
            #
            # packet 0 -> 00 00
            # packet 1 -> 38 00
            # packet 2 -> 70 00
            # packet 3 -> A8 00
            # packet 4 -> E0 00
            # packet 5 -> 18 01
            # packet 6 -> 50 01
            # packet 7 -> 88 01
            # packet 8 -> C0 01
            #
            # Это фактически byte-offset
            # 56 * chunk.

            offset = start * 4

            packet[3] = offset & 0xFF
            packet[4] = (
                offset >> 8
            ) & 0xFF

            pos = 8

            for i in range(14):

                key = start + i

                r, g, b = self.key_colors[key]

                packet[pos] = key
                packet[pos + 1] = r
                packet[pos + 2] = g
                packet[pos + 3] = b

                pos += 4

            packets.append(packet)

        # ---------------------------------------------
        # Последние 2 entries: 126 и 127
        # ---------------------------------------------

        packet = [0] * 64

        packet[0] = 0xAA
        packet[1] = 0x24
        packet[2] = 0x08
        packet[3] = 0xF8
        packet[4] = 0x01
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00

        pos = 8

        for key in range(
            126,
            128
        ):

            r, g, b = self.key_colors[key]

            packet[pos] = key
            packet[pos + 1] = r
            packet[pos + 2] = g
            packet[pos + 3] = b

            pos += 4

        packets.append(packet)

        return packets

    # =====================================================
    # Per-Key SEND
    # =====================================================

    def get_per_key_delay(self):

        try:

            ms = float(
                self.delay_var.get()
            )

            if ms < 0:
                ms = 0

            return ms / 1000.0

        except Exception:

            return PER_KEY_DELAY

    def send_per_key(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        self.update_selected_key()

        try:

            packets = self.make_per_key_packets()

            delay = self.get_per_key_delay()

            self.log("")
            self.log(
                "=== PER-KEY SEND ==="
            )

            self.log(
                f"Packets: {len(packets)}"
            )

            self.log(
                f"Delay: {delay * 1000:.2f} ms"
            )

            for number, packet in enumerate(
                packets,
                start=1
            ):

                result = self.device.write(
                    [0] + packet
                )

                self.log(
                    f"OUT {number}/10: "
                    + " ".join(
                        f"{x:02X}"
                        for x in packet
                    )
                )

                self.log(
                    f"write() = {result}"
                )

                if result < 0:

                    raise RuntimeError(
                        f"write() failed "
                        f"on packet {number}"
                    )

                # ВАЖНО:
                # Никаких read() здесь нет.
                #
                # В Wireshark между реальными report'ами
                # видны URB completion packets.
                # Это не отдельные данные, которые
                # нужно создавать из Python.

                if number < len(packets):

                    time.sleep(
                        delay
                    )

            self.status.set(
                "🟢 Per-Key отправлен"
            )

            self.log(
                "Per-Key transmission complete."
            )

        except Exception as e:

            self.log(
                "Per-Key ERROR: "
                + repr(e)
            )

            messagebox.showerror(
                "Per-Key ошибка",
                repr(e)
            )

    # =====================================================
    # Close
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

    app = Type84RGB(root)

    root.protocol(
        "WM_DELETE_WINDOW",
        app.close
    )

    root.mainloop()


if __name__ == "__main__":
    main()

