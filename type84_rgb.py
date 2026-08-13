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


class Type84RGB:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("760x760")

        self.device = None
        self.device_info = None
        self.running = False

        self.background = (255, 0, 0)

        # 128 Per-Key entries.
        # По умолчанию все выключены.
        self.key_colors = {
            i: (0, 0, 0)
            for i in range(0x80)
        }

        self.selected_key = 0x31

        self.build_ui()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        title = ttk.Label(
            self.root,
            text="Red Square IO Type 84 RGB",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(15, 5))

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
        ).pack(pady=10)

        # -----------------------------------------------------
        # Device
        # -----------------------------------------------------

        device_frame = ttk.Frame(self.root)
        device_frame.pack(fill="x", padx=30)

        ttk.Button(
            device_frame,
            text="1. Найти клавиатуру",
            command=self.scan
        ).pack(fill="x", pady=3)

        ttk.Button(
            device_frame,
            text="2. Подключить MI_02",
            command=self.connect
        ).pack(fill="x", pady=3)

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=12)

        # -----------------------------------------------------
        # Static RGB
        # -----------------------------------------------------

        ttk.Label(
            self.root,
            text="СТАТИЧЕСКИЙ RGB",
            font=("Segoe UI", 12, "bold")
        ).pack()

        colors = ttk.Frame(self.root)
        colors.pack(pady=7)

        ttk.Button(
            colors,
            text="🔴 Красный",
            command=lambda: self.set_static(255, 0, 0)
        ).grid(row=0, column=0, padx=3)

        ttk.Button(
            colors,
            text="🟢 Зелёный",
            command=lambda: self.set_static(0, 255, 0)
        ).grid(row=0, column=1, padx=3)

        ttk.Button(
            colors,
            text="🔵 Синий",
            command=lambda: self.set_static(0, 0, 255)
        ).grid(row=0, column=2, padx=3)

        ttk.Button(
            colors,
            text="⚪ Белый",
            command=lambda: self.set_static(255, 255, 255)
        ).grid(row=0, column=3, padx=3)

        ttk.Button(
            colors,
            text="🎨 Свой цвет",
            command=self.choose_background
        ).grid(row=0, column=4, padx=3)

        ttk.Button(
            self.root,
            text="🌈 Цикл всей клавиатуры",
            command=self.toggle_cycle
        ).pack(pady=7)

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=12)

        # -----------------------------------------------------
        # Per-Key
        # -----------------------------------------------------

        ttk.Label(
            self.root,
            text="PER-KEY RGB",
            font=("Segoe UI", 12, "bold")
        ).pack()

        ttk.Label(
            self.root,
            text="Подтверждённый протокол AA 24 38"
        ).pack(pady=(2, 8))

        per_key = ttk.Frame(self.root)
        per_key.pack(fill="x", padx=30)

        ttk.Label(
            per_key,
            text="Индекс клавиши:"
        ).grid(row=0, column=0, sticky="w")

        self.key_var = tk.StringVar(
            value="31"
        )

        self.key_entry = ttk.Entry(
            per_key,
            textvariable=self.key_var,
            width=10
        )
        self.key_entry.grid(
            row=0,
            column=1,
            padx=8
        )

        ttk.Label(
            per_key,
            text="HEX (00–7F)"
        ).grid(row=0, column=2, sticky="w")

        self.per_key_color = (255, 0, 0)

        ttk.Button(
            per_key,
            text="🎨 Выбрать цвет",
            command=self.choose_key_color
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            pady=7,
            sticky="ew"
        )

        ttk.Button(
            per_key,
            text="🔴 Тест A = красный",
            command=self.test_key_a_red
        ).grid(
            row=2,
            column=0,
            columnspan=3,
            pady=3,
            sticky="ew"
        )

        ttk.Button(
            per_key,
            text="💡 Подсветить выбранную клавишу",
            command=self.set_selected_key
        ).grid(
            row=3,
            column=0,
            columnspan=3,
            pady=3,
            sticky="ew"
        )

        ttk.Button(
            per_key,
            text="⬛ Выключить выбранную клавишу",
            command=self.clear_selected_key
        ).grid(
            row=4,
            column=0,
            columnspan=3,
            pady=3,
            sticky="ew"
        )

        ttk.Button(
            per_key,
            text="🧹 Выключить все Per-Key",
            command=self.clear_all_keys
        ).grid(
            row=5,
            column=0,
            columnspan=3,
            pady=3,
            sticky="ew"
        )

        ttk.Button(
            per_key,
            text="🚀 Отправить текущую Per-Key таблицу",
            command=self.send_per_key_table
        ).grid(
            row=6,
            column=0,
            columnspan=3,
            pady=(8, 3),
            sticky="ew"
        )

        # -----------------------------------------------------
        # Log
        # -----------------------------------------------------

        ttk.Label(
            self.root,
            text="ЛОГ"
        ).pack(pady=(10, 3))

        self.log_box = tk.Text(
            self.root,
            height=13,
            state="disabled"
        )

        self.log_box.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(3, 15)
        )

    # =========================================================
    # Logging
    # =========================================================

    def log(self, text):
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # =========================================================
    # Device
    # =========================================================

    def find_device(self):

        devices = hid.enumerate(VID, PID)

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

    # =========================================================
    # HID
    # =========================================================

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

        # Именно так работал наш подтверждённый
        # AA 23 10 static RGB.
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

    # =========================================================
    # Static RGB — НЕ МЕНЯЕМ РАБОЧИЙ ПРОТОКОЛ
    # =========================================================

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

        self.background = (r, g, b)

        try:

            if self.send(
                self.make_static(r, g, b)
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

    # =========================================================
    # Color picker
    # =========================================================

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

        self.set_static(r, g, b)

    def choose_key_color(self):

        color = colorchooser.askcolor(
            title="Цвет выбранной клавиши"
        )

        if not color or not color[0]:
            return

        self.per_key_color = tuple(
            map(int, color[0])
        )

        r, g, b = self.per_key_color

        self.log(
            "Per-Key цвет: "
            f"#{r:02X}{g:02X}{b:02X}"
        )

    # =========================================================
    # Cycle
    # =========================================================

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
                        r, g, b
                    )

                    if self.device:

                        # Используем тот же способ отправки,
                        # что и для рабочего static RGB.
                        self.device.write(
                            [0] + packet
                        )

                    self.background = (
                        r, g, b
                    )

                except Exception as e:

                    self.log(
                        "Cycle error: "
                        + repr(e)
                    )

                    self.running = False
                    break

                time.sleep(1.0)

    # =========================================================
    # Per-Key protocol
    # =========================================================

    def make_per_key_packet(
        self,
        offset,
        keys
    ):
        """
        Создаёт один AA 24 38 пакет.

        offset:
            смещение блока.

        keys:
            список из максимум 14 записей.

        Формат записи:
            KEY_INDEX R G B

        По подтверждённому захвату:
            AA 24 38 [offset]
            [14 x 4 bytes]
        """

        packet = [0] * 64

        packet[0] = 0xAA
        packet[1] = 0x24
        packet[2] = 0x38

        packet[3] = offset & 0xFF
        packet[4] = (offset >> 8) & 0xFF

        pos = 8

        for key_index in keys:

            r, g, b = self.key_colors[
                key_index
            ]

            packet[pos] = key_index
            packet[pos + 1] = r
            packet[pos + 2] = g
            packet[pos + 3] = b

            pos += 4

        return packet

    def make_per_key_packets(self):

        packets = []

        # Первые 9 пакетов:
        # 00-0D
        # 0E-1B
        # 1C-29
        # ...
        #
        # Каждый содержит 14 клавиш.

        all_keys = list(range(0x80))

        for block in range(9):

            start = block * 14
            chunk = all_keys[
                start:start + 14
            ]

            offset = start * 4

            packets.append(
                self.make_per_key_packet(
                    offset,
                    chunk
                )
            )

        # Последний пакет подтверждённого захвата.
        #
        # В нём:
        #
        # AA 24 08 F8 01 00 01
        # 7E 00 00 00
        # 7F 00 00 00
        #
        # Он не менялся при изменении цвета A,
        # поэтому сохраняем его отдельно.

        last = [0] * 64

        last[0] = 0xAA
        last[1] = 0x24
        last[2] = 0x08
        last[3] = 0xF8
        last[4] = 0x01
        last[5] = 0x00
        last[6] = 0x01
        last[7] = 0x00

        last[8] = 0x7E
        last[9] = 0x00
        last[10] = 0x00
        last[11] = 0x00

        last[12] = 0x7F
        last[13] = 0x00
        last[14] = 0x00
        last[15] = 0x00

        packets.append(last)

        return packets

    def send_per_key_table(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        try:

            packets = (
                self.make_per_key_packets()
            )

            self.log("")
            self.log(
                "=== PER-KEY SEND ==="
            )

            for number, packet in enumerate(
                packets,
                start=1
            ):

                self.log(
                    f"Per-Key OUT #{number}:"
                )

                self.send(packet)

                # Небольшая пауза между HID reports.
                time.sleep(0.003)

            self.status.set(
                "🟢 Per-Key таблица отправлена"
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

    # =========================================================
    # Per-Key controls
    # =========================================================

    def get_selected_key(self):

        value = self.key_var.get().strip()

        try:

            key = int(
                value,
                16
            )

        except ValueError:

            raise ValueError(
                "Индекс должен быть HEX, например 31"
            )

        if not 0 <= key <= 0x7F:

            raise ValueError(
                "Индекс должен быть от 00 до 7F"
            )

        return key

    def set_selected_key(self):

        try:

            key = self.get_selected_key()

            self.key_colors[key] = (
                self.per_key_color
            )

            r, g, b = self.per_key_color

            self.log(
                f"Key {key:02X}: "
                f"RGB {r:02X} {g:02X} {b:02X}"
            )

            self.send_per_key_table()

        except Exception as e:

            messagebox.showerror(
                "Per-Key",
                str(e)
            )

    def clear_selected_key(self):

        try:

            key = self.get_selected_key()

            self.key_colors[key] = (
                0,
                0,
                0
            )

            self.log(
                f"Key {key:02X}: OFF"
            )

            self.send_per_key_table()

        except Exception as e:

            messagebox.showerror(
                "Per-Key",
                str(e)
            )

    def clear_all_keys(self):

        answer = messagebox.askyesno(
            "Очистить Per-Key",
            "Выключить все 128 Per-Key записей?"
        )

        if not answer:
            return

        for key in range(0x80):

            self.key_colors[key] = (
                0,
                0,
                0
            )

        self.send_per_key_table()

    # =========================================================
    # Known test: A = 31
    # =========================================================

    def test_key_a_red(self):

        # По твоему захвату:
        #
        # A = 0x31
        #
        # Красный:
        # 31 FF 00 00

        self.key_var.set("31")

        self.per_key_color = (
            255,
            0,
            0
        )

        self.key_colors[0x31] = (
            255,
            0,
            0
        )

        # Все остальные выключаем,
        # чтобы получить ровно тот же эксперимент,
        # который ты сделал в официальном ПО.

        for key in range(0x80):

            if key != 0x31:

                self.key_colors[key] = (
                    0,
                    0,
                    0
                )

        self.log(
            "=== TEST A RED ==="
        )

        self.log(
            "A = key index 0x31"
        )

        self.log(
            "31 FF 00 00"
        )

        self.send_per_key_table()

    # =========================================================

    def close(self):

        self.running = False

        try:

            if self.device:
                self.device.close()

        except Exception:
            pass

        self.root.destroy()


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
