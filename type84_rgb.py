
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
# Type 84 RGB application
# ---------------------------------------------------------

class Type84RGB:

    def __init__(self, root):

        self.root = root
        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("760x700")

        self.device = None
        self.device_info = None

        self.running = False

        self.background = (255, 0, 0)
        self.key_colors = {}

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

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=15)

        # -------------------------------------------------
        # Static RGB
        # -------------------------------------------------

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

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=15)

        # -------------------------------------------------
        # Per-Key
        # -------------------------------------------------

        ttk.Label(
            self.root,
            text="PER-KEY RGB",
            font=("Segoe UI", 12, "bold")
        ).pack()

        ttk.Label(
            self.root,
            text=(
                "Протокол AA 24 38 — 128 LED/key-индексов"
            )
        ).pack(pady=3)

        perkey = ttk.Frame(self.root)
        perkey.pack(pady=8)

        ttk.Button(
            perkey,
            text="🧪 A → красный",
            command=lambda: self.set_key_color(
                0x31, 255, 0, 0
            )
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            perkey,
            text="🧪 A → синий",
            command=lambda: self.set_key_color(
                0x31, 0, 0, 255
            )
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            perkey,
            text="🎨 Выбрать цвет A",
            command=self.choose_key_color
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            self.root,
            text="🧪 Отправить текущий Per-Key",
            command=self.send_per_key
        ).pack(pady=8)

        self.log_box = tk.Text(
            self.root,
            height=15,
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

        self.log_box.config(state="normal")

        self.log_box.insert(
            "end",
            text + "\n"
        )

        self.log_box.see("end")

        self.log_box.config(state="disabled")

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
            + str(
                info.get("product_string")
            )
        )

        self.log("VID: 0x0C45")
        self.log("PID: 0x8009")
        self.log("Interface: 2")
        self.log("Usage Page: 0xFF68")
        self.log("Usage: 0x61")

        self.log(
            "Path: "
            + str(
                info.get("path")
            )
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

            try:

                self.log(
                    "Manufacturer: "
                    + str(
                        self.device.get_manufacturer_string()
                    )
                )

            except Exception:
                pass

            try:

                self.log(
                    "Product: "
                    + str(
                        self.device.get_product_string()
                    )
                )

            except Exception:
                pass

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
    # HID send
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

        # В hidapi для данного интерфейса
        # первый байт — Report ID = 0.
        data = [0] + packet

        result = self.device.write(data)

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
    #
    # Подтверждённый пакет:
    #
    # AA 23 10 00 00 00 01 00 01
    # RR GG BB FF
    # 00 00 00 00
    # 05
    # 00 00 00
    # AA 55
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

            if self.send(
                self.make_static(
                    r,
                    g,
                    b
                )
            ):

                self.status.set(
                    "🟢 RGB отправлен: "
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
    # Color picker — whole keyboard
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
            (255, 0, 255)
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
    # PER-KEY PROTOCOL
    #
    # Official capture:
    #
    # AA 24 38 XX ...
    #
    # Every LED entry:
    #
    #    INDEX
    #    R
    #    G
    #    B
    #
    # The first packet starts at LED 0.
    #
    # 14 entries per packet.
    #
    # Packets:
    #
    # 1:  0x00 ... 0x0D
    # 2:  0x0E ... 0x1B
    # 3:  0x1C ... 0x29
    # 4:  0x2A ... 0x37
    # 5:  0x38 ... 0x45
    # 6:  0x46 ... 0x53
    # 7:  0x54 ... 0x61
    # 8:  0x62 ... 0x6F
    # 9:  0x70 ... 0x7D
    #
    # Last packet:
    #
    # AA 24 08 F8 ...
    # 7E
    # 7F
    #
    # The capture shows the final packet separately.
    # =====================================================

    def make_per_key_packet(
        self,
        start_index,
        entries
    ):

        packet = [0] * 64

        # Header
        packet[0] = 0xAA
        packet[1] = 0x24

        # Normal data packets use 0x38.
        packet[2] = 0x38

        # Address/offset.
        #
        # Official capture:
        #
        # packet 1:
        # AA 24 38 00 00 00 00 00 ...
        #
        # packet 2:
        # AA 24 38 38 00 00 00 0E ...
        #
        # packet 3:
        # AA 24 38 70 00 00 00 1C ...
        #
        # packet 4:
        # AA 24 38 A8 00 00 00 2A ...
        #
        # offset = start_index * 4
        #
        offset = start_index * 4

        packet[3] = offset & 0xFF
        packet[4] = (offset >> 8) & 0xFF

        # Bytes 5-7 are zero in the capture.
        packet[5] = 0x00
        packet[6] = 0x00
        packet[7] = 0x00

        pos = 8

        for index, r, g, b in entries:

            if pos + 4 > 64:

                break

            packet[pos] = index
            packet[pos + 1] = r
            packet[pos + 2] = g
            packet[pos + 3] = b

            pos += 4

        return packet

    def make_per_key_final_packet(
        self,
        colors
    ):

        packet = [0] * 64

        packet[0] = 0xAA
        packet[1] = 0x24
        packet[2] = 0x08
        packet[3] = 0xF8

        packet[4] = 0x01
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00

        # Last two LED indices in the official capture.
        #
        # 7E = last-but-one
        # 7F = last
        #
        # Put them into the same 4-byte structure.

        pos = 8

        for index in (0x7E, 0x7F):

            r, g, b = colors.get(
                index,
                (0, 0, 0)
            )

            packet[pos] = index
            packet[pos + 1] = r
            packet[pos + 2] = g
            packet[pos + 3] = b

            pos += 4

        return packet

    def build_per_key_packets(self):

        # 128 LED/key entries.
        colors = {}

        for i in range(128):

            colors[i] = (
                0,
                0,
                0
            )

        # Apply user-defined colours.
        for index, color in self.key_colors.items():

            if 0 <= index < 128:

                colors[index] = color

        packets = []

        # Official capture uses 14 entries
        # in each normal AA 24 38 packet.

        start = 0

        while start < 126:

            entries = []

            for i in range(
                start,
                min(start + 14, 126)
            ):

                r, g, b = colors[i]

                entries.append(
                    (
                        i,
                        r,
                        g,
                        b
                    )
                )

            packets.append(
                self.make_per_key_packet(
                    start,
                    entries
                )
            )

            start += 14

        # Final AA 24 08 packet.
        packets.append(
            self.make_per_key_final_packet(
                colors
            )
        )

        return packets

    # =====================================================
    # Send Per-Key
    # =====================================================

    def send_per_key(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        try:

            packets = self.build_per_key_packets()

            self.log("")
            self.log(
                "=== PER-KEY SEND ==="
            )

            self.log(
                f"Пакетов: {len(packets)}"
            )

            for number, packet in enumerate(
                packets,
                start=1
            ):

                self.send(packet)

                # Небольшая задержка.
                #
                # Она нужна не для изменения протокола,
                # а чтобы USB HID не получил все reports
                # одним слишком быстрым burst.
                time.sleep(0.003)

                self.log(
                    f"Per-Key packet {number}/"
                    f"{len(packets)} отправлен."
                )

            self.status.set(
                "🟢 Per-Key отправлен"
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
    # Set one key
    # =====================================================

    def set_key_color(
        self,
        index,
        r,
        g,
        b
    ):

        self.key_colors[index] = (
            r,
            g,
            b
        )

        self.log(
            f"LED index 0x{index:02X}: "
            f"RGB {r},{g},{b}"
        )

        self.send_per_key()

    # =====================================================
    # Key color picker
    # =====================================================

    def choose_key_color(self):

        color = colorchooser.askcolor(
            title="Цвет клавиши A"
        )

        if not color or not color[0]:

            return

        r, g, b = map(
            int,
            color[0]
        )

        # В твоём захвате:
        #
        # A = 0x31
        #
        # Поэтому здесь намеренно используем 0x31.

        self.set_key_color(
            0x31,
            r,
            g,
            b
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

