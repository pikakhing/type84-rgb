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
REPORT_ID = 0x04

CMD_RGB_STATIC = 0x08
ZONE_KEYS = 0x00

CMD_RGB_BRIGHTNESS = 0x0B

CMD_PER_KEY = 0x20
PER_KEY_SUB = 0x04
PER_KEY_MODE_WIRED = 0x03

class Type84RGB:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("700x620")

        self.device = None
        self.device_info = None
        self.running = False

        self.background = (0, 0, 255)
        self.key_color = (255, 0, 0)

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

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

        ttk.Label(
            self.root,
            text="ТЕСТ PER-KEY",
            font=("Segoe UI", 12, "bold")
        ).pack()

        ttk.Label(
            self.root,
            text="Экспериментальный режим протокола 0x20/0x04"
        ).pack(pady=3)

        ttk.Button(
            self.root,
            text="🧪 Попробовать Per-Key",
            command=self.per_key_test
        ).pack(pady=8)

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

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    def log(self, text):
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # ---------------------------------------------------------
    # Device
    # ---------------------------------------------------------

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
                "Ошибка: " + repr(e)
            )

    # ---------------------------------------------------------
    # HID
    # ---------------------------------------------------------

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

        result = self.device.write([0] + packet)

        self.log(
            "TX: "
            + " ".join(
                f"{x:02X}"
                for x in packet
            )
            + " ..."
        )

        self.log(
            "write() = " + str(result)
        )

        return result >= 0

    # ---------------------------------------------------------
    # Static RGB
    # ---------------------------------------------------------

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
        packet[16] = 0x03
        packet[17] = 0x00
        packet[18] = 0x00
        packet[19] = 0x00

        packet[20] = 0xAA
        packet[21] = 0x55

        return packet

    def set_static(self, r, g, b):

        self.background = (r, g, b)

        try:

            ok = self.send(
                self.make_static(r, g, b)
            )

            if ok:
                self.status.set(
                    f"🟢 RGB отправлен: #{r:02X}{g:02X}{b:02X}"
                )

        except Exception as e:

            self.log(
                "RGB ERROR: " + repr(e)
            )

            messagebox.showerror(
                "RGB ошибка",
                repr(e)
            )

    # ---------------------------------------------------------
    # Color picker
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Cycle
    # ---------------------------------------------------------

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
                        self.device.write(packet)

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

    # ---------------------------------------------------------
    # Experimental Per-Key
    # ---------------------------------------------------------

    def make_per_key_header(self):

        packet = [0] * REPORT_SIZE

        packet[0] = REPORT_ID
        packet[1] = CMD_PER_KEY
        packet[2] = PER_KEY_SUB

        packet[9] = PER_KEY_MODE_WIRED

        return packet

    def per_key_test(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        answer = messagebox.askyesno(
            "Экспериментальный тест",
            "Это экспериментальный Per-Key протокол.\n\n"
            "На проводном AK980-подобном протоколе "
            "он описан как монохромный.\n\n"
            "Продолжить?"
        )

        if not answer:
            return

        try:

            # Header: 04 20 04 ... byte 9 = 03
            header = self.make_per_key_header()

            self.send(header)

            self.log(
                "Per-Key header отправлен."
            )

            self.log(
                "⚠️ Пока blob клавиш не отправляется."
            )

            self.log(
                "Это сделано специально: "
                "LED→key mapping для этого протокола "
                "не подтверждён на Type 84."
            )

            messagebox.showinfo(
                "Per-Key",
                "Заголовок Per-Key отправлен.\n\n"
                "Полный RGB-blob пока НЕ отправлялся."
            )

        except Exception as e:

            self.log(
                "Per-Key ERROR: "
                + repr(e)
            )

    # ---------------------------------------------------------

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
