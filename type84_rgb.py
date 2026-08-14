
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


class Type84RGB:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("700x650")

        self.device = None
        self.device_info = None

        self.running = False

        self.background = (255, 0, 0)
        self.key_color = (255, 0, 0)
        # Текущее состояние всех 128 LED.
        # Каждый элемент: (R, G, B)
        self.per_key_colors = [
            (0, 0, 0)
            for _ in range(128)
        ]

        self.build_ui()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        ttk.Label(
            self.root,
            text="Red Square IO Type 84 RGB",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(18, 5))

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

        # -----------------------------------------------------
        # Режим всей клавиатуры
        # -----------------------------------------------------

        ttk.Label(
            self.root,
            text="РЕЖИМ ВСЕЙ КЛАВИАТУРЫ",
            font=("Segoe UI", 12, "bold")
        ).pack()

        ttk.Button(
            self.root,
            text="🎨 Выбрать цвет всей клавиатуры",
            command=self.choose_background
        ).pack(pady=8)

        ttk.Button(
            self.root,
            text="👤 Переключить в пользовательский режим",
            command=self.set_custom_mode
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="🌈 Цикл всей клавиатуры",
            command=self.toggle_cycle
        ).pack(pady=8)

        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(fill="x", padx=30, pady=15)

        # -----------------------------------------------------
        # Per-Key
        # -----------------------------------------------------

        ttk.Label(
            self.root,
            text="PER-KEY",
            font=("Segoe UI", 12, "bold")
        ).pack()

        ttk.Label(
            self.root,
            text="Изменение отдельного LED-индекса"
        ).pack(pady=3)

        key_frame = ttk.Frame(self.root)
        key_frame.pack(pady=8)

        ttk.Label(
            key_frame,
            text="Индекс:"
        ).grid(row=0, column=0, padx=5)

        self.key_index_var = tk.IntVar(value=31)

        ttk.Spinbox(
            key_frame,
            from_=0,
            to=127,
            textvariable=self.key_index_var,
            width=8
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            key_frame,
            text="Выбрать цвет",
            command=self.choose_key_color
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            self.root,
            text="🔴 Отправить Per-Key",
            command=self.send_per_key
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="⬛ Выключить выбранный LED",
            command=self.disable_selected_key
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="⬛ Выключить все LED",
            command=self.disable_all_keys
        ).pack(pady=5)

        # -----------------------------------------------------
        # Log
        # -----------------------------------------------------

        self.log_box = tk.Text(
            self.root,
            height=12,
            state="disabled"
        )

        self.log_box.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(10, 20)
        )

    # =========================================================
    # LOG
    # =========================================================

    def log(self, text):
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # =========================================================
    # DEVICE
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

            self.status.set("❌ Type 84 не найдена")
            self.log("MI_02 не найден.")

            return

        self.device_info = info

        self.status.set("✅ Type 84 найдена")

        self.log("")
        self.log("=== DEVICE ===")
        self.log("Product: " + str(
            info.get("product_string")
        ))
        self.log("VID: 0x0C45")
        self.log("PID: 0x8009")
        self.log("Interface: 2")
        self.log("Usage Page: 0xFF68")
        self.log("Usage: 0x61")
        self.log("Path: " + str(info.get("path")))

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
                "Ошибка: " + repr(e)
            )

    # =========================================================
    # HID SEND
    # =========================================================

    def send(self, packet, delay=True):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return False

        if len(packet) != REPORT_SIZE:
            raise ValueError(
                f"HID report должен быть 64 байта, получено {len(packet)}"
            )

        # hidapi write() для данного интерфейса ожидает
        # report ID перед 64-байтным payload.
        result = self.device.write([0] + packet)

        self.log(
            "TX: "
            + " ".join(
                f"{x:02X}"
                for x in packet
            )
        )

        self.log(
            "write() = " + str(result)
        )

        if delay:
            time.sleep(PACKET_DELAY)

        return result >= 0

    # =========================================================
    # RGB STATIC
    # =========================================================

    def make_static(self, r, g, b):

        packet = [0] * 64

        # ВАЖНО:
        #
        # Реальный пакет:
        #
        # AA 23 10 00 00 00 01 00 01
        # R  G  B  FF
        # 00 00 00 00 05
        #
        # Поэтому здесь НЕ:
        #
        # AA 23 10 00 00 01 00 01
        #
        # а именно:
        #
        # AA 23 10 00 00 00 01 00 01

        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10

        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00

        # 0x01 = статический режим
        packet[8] = 0x01

        packet[9] = r
        packet[10] = g
        packet[11] = b
        packet[12] = 0xFF

        # После цвета:
        #
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

    # =========================================================
    # CUSTOM / USER MODE
    # =========================================================

    def make_custom_mode(self, r=0xB6, g=0x4C, b=0xFD):

        packet = [0] * 64

        # Реальный пакет с сайта:
        #
        # AA 23 10 00 00 00 01 00 80
        # B6 4C FD FF
        # 00 00 00 00 05
        # 00 00 00 AA 55

        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10

        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x00
        packet[6] = 0x01
        packet[7] = 0x00

        # 0x80 = пользовательский режим
        packet[8] = 0x80

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
                    "Custom mode: 0x80"
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

    # =========================================================
    # SET STATIC
    # =========================================================

    def set_static(self, r, g, b):

        self.background = (r, g, b)

        try:

            packet = self.make_static(r, g, b)

            if self.send(packet):

                self.status.set(
                    f"🟢 RGB: #{r:02X}{g:02X}{b:02X}"
                )

        except Exception as e:

            self.log(
                "RGB ERROR: " + repr(e)
            )

            messagebox.showerror(
                "RGB ошибка",
                repr(e)
            )

    # =========================================================
    # COLOR PICKER
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
            title="Цвет клавиши"
        )

        if not color or not color[0]:
            return

        self.key_color = tuple(
            map(int, color[0])
        )

        r, g, b = self.key_color

        self.log(
            f"Выбран цвет клавиши: "
            f"#{r:02X}{g:02X}{b:02X}"
        )

    # =========================================================
    # CYCLE
    # =========================================================

    def toggle_cycle(self):

        if self.running:

            self.running = False
            self.status.set("⏹ Цикл остановлен")

            return

        self.running = True
        self.status.set("🌈 Цикл запущен")

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
                        self.send(
                            packet,
                            delay=True
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
    # PER-KEY PACKET
    # =========================================================

    def make_per_key_packets(self):
        """
        Создаёт полный официальный Per-Key blob из 10 HID reports.

        self.per_key_colors содержит состояние всех 128 LED.
        Поэтому изменение одной клавиши НЕ выключает остальные.
        """

        packets = []

        for packet_number in range(10):

            packet = [0] * REPORT_SIZE

            start_index = packet_number * 14
            offset = start_index * 4

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

            packet[0] = 0xAA
            packet[1] = 0x24

            # Первые 9:
            # AA 24 38 ...
            #
            # Последний:
            # AA 24 08 ...
            packet[2] = (
                0x08
                if packet_number == 9
                else 0x38
            )

            packet[3] = offset & 0xFF
            packet[4] = (offset >> 8) & 0xFF

            packet[5] = 0x00

            # Последний пакет = 01
            packet[6] = (
                0x01
                if packet_number == 9
                else 0x00
            )

            packet[7] = 0x00

        # -------------------------------------------------
        # LED records
        # -------------------------------------------------

            for slot in range(14):

                index = start_index + slot

                if index >= 128:
                    break

                pos = 8 + slot * 4

                r, g, b = self.per_key_colors[index]

                packet[pos] = index
                packet[pos + 1] = r
                packet[pos + 2] = g
                packet[pos + 3] = b

            packets.append(packet)

        return packets

    # =========================================================
    # SEND PER-KEY
    # =========================================================
    ф
    def send_per_key(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        try:

            index = int(
                self.key_index_var.get()
            )

        except Exception:

            messagebox.showerror(
                "Ошибка",
                "Индекс должен быть числом."
            )

            return

        if not 0 <= index <= 127:

            messagebox.showerror(
                "Ошибка",
                "Индекс LED должен быть от 0 до 127."
            )

            return

        r, g, b = self.key_color

        # -----------------------------------------------------
        # ВАЖНО:
        # Сначала сохраняем новый цвет в состоянии.
        # -----------------------------------------------------

        self.per_key_colors[index] = (
            r,
            g,
            b
        )

        self.log("")
        self.log("=== PER-KEY ===")
        self.log(
            f"LED index = {index}"
        )
        self.log(
            f"Color = #{r:02X}{g:02X}{b:02X}"
        )

        try:

            packets = self.make_per_key_packets()

            # Всегда отправляем полный официальный blob.
            for number, packet in enumerate(
                packets,
                start=1
            ):

                self.log(
                    f"Per-Key packet "
                    f"{number}/10"
                )

                ok = self.send(
                    packet,
                    delay=True
                )

                if not ok:

                    self.status.set(
                        "❌ Ошибка Per-Key"
                    )

                    return

            self.status.set(
                f"🟢 LED {index}: "
                f"#{r:02X}{g:02X}{b:02X}"
            )

            self.log(
                "✅ Все 10 Per-Key пакетов отправлены."
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


    # =========================================================
    # DISABLE SELECTED
    # =========================================================

    def disable_selected_key(self):

        if not self.device:
            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )
            return

        try:
            index = int(
                self.key_index_var.get()
            )
        except Exception:
            messagebox.showerror(
                "Ошибка",
                "Индекс должен быть числом."
            )
            return

        if not 0 <= index <= 127:
            messagebox.showerror(
                "Ошибка",
                "Индекс LED должен быть от 0 до 127."
            )
            return

        # Запоминаем, что этот LED выключен.
        self.per_key_colors[index] = (
            0,
            0,
            0
        )

        self.log(
            f"LED {index} выключен."
        )

        try:

            packets = self.make_per_key_packets()

            for number, packet in enumerate(
                packets,
                start=1
            ):

                ok = self.send(
                    packet,
                    delay=True
                )

                if not ok:
                    self.status.set(
                        "❌ Ошибка выключения LED"
                    )
                    return

            self.status.set(
                f"⬛ LED {index} выключен"
            )

        except Exception as e:

            self.log(
                "DISABLE ERROR: "
                + repr(e)
            )


    # =========================================================
    # DISABLE ALL
    # =========================================================

    def disable_all_keys(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        try:

            packets = self.make_per_key_packets(
                255,
                0,
                0,
                0
            )

        except ValueError:
            # Нам нужен специальный вариант:
            # все 128 LED = 00 00 00.
            packets = []

            for packet_number in range(10):

                packet = [0] * REPORT_SIZE

                start_index = packet_number * 14
                offset = start_index * 4

                packet[0] = 0xAA
                packet[1] = 0x24
                packet[2] = (
                    0x08
                    if packet_number == 9
                    else 0x38
                )

                packet[3] = offset & 0xFF
                packet[4] = (offset >> 8) & 0xFF
                packet[5] = 0x00
                packet[6] = (
                    0x01
                    if packet_number == 9
                    else 0x00
                )
                packet[7] = 0x00

                for slot in range(14):

                    index = start_index + slot

                    if index >= 128:
                        break

                    pos = 8 + slot * 4

                    packet[pos] = index
                    packet[pos + 1] = 0x00
                    packet[pos + 2] = 0x00
                    packet[pos + 3] = 0x00

                packets.append(packet)

        try:

            self.log("")
            self.log(
                "=== DISABLE ALL LED ==="
            )

            for number, packet in enumerate(
                packets,
                start=1
            ):

                self.log(
                    f"Disable packet "
                    f"{number}/10"
                )

                ok = self.send(
                    packet,
                    delay=True
                )

                if not ok:

                    self.status.set(
                        "❌ Ошибка выключения LED"
                    )

                    return

            self.status.set(
                "⬛ Все LED выключены"
            )

            self.log(
                "✅ Все 10 Per-Key пакетов отправлены."
            )

        except Exception as e:

            self.log(
                "DISABLE ALL ERROR: "
                + repr(e)
            )

            messagebox.showerror(
                "Ошибка",
                repr(e)
            )

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        self.running = False

        try:

            if self.device:
                self.device.close()

        except Exception:
            pass

        self.root.destroy()


# =============================================================
# MAIN
# =============================================================

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
