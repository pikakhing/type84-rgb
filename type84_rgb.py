import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import hid
import threading
import time


# =========================================================
# DEVICE
# =========================================================

VID = 0x0C45
PID = 0x8009

INTERFACE = 2
USAGE_PAGE = 0xFF68
USAGE = 0x61

REPORT_SIZE = 64


# =========================================================
# STATIC RGB PROTOCOL
# =========================================================

def make_static_packet(r, g, b):
    """
    Официальный пакет статического RGB,
    восстановленный по Wireshark.

    Для красного:

    AA 23 10 00 00 00 01 00 01
    FF 00 00 FF
    00 00 00 00
    05 00 00 00
    AA 55
    """

    packet = [0] * REPORT_SIZE

    packet[0] = 0xAA
    packet[1] = 0x23
    packet[2] = 0x10

    packet[3] = 0x00
    packet[4] = 0x00
    packet[5] = 0x00
    packet[6] = 0x01
    packet[7] = 0x00
    packet[8] = 0x01

    # RGB
    packet[9] = r
    packet[10] = g
    packet[11] = b

    # Static / enabled
    packet[12] = 0xFF

    packet[13] = 0x00
    packet[14] = 0x00
    packet[15] = 0x00
    packet[16] = 0x00

    # Brightness
    # 0 = off
    # 1..5 = brightness levels
    packet[17] = 0x05

    packet[18] = 0x00
    packet[19] = 0x00
    packet[20] = 0x00

    packet[21] = 0xAA
    packet[22] = 0x55

    return packet


# =========================================================
# APPLICATION
# =========================================================

class Type84RGB:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Red Square IO Type 84 RGB"
        )

        self.root.geometry(
            "700x650"
        )

        self.device = None
        self.device_info = None

        self.running = False

        self.background = (
            255,
            0,
            0
        )

        self.brightness = 5

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


        # -------------------------------------------------
        # DEVICE
        # -------------------------------------------------

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


        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=30,
            pady=15
        )


        # -------------------------------------------------
        # STATIC RGB
        # -------------------------------------------------

        ttk.Label(
            self.root,
            text="ТЕСТ ВСЕЙ КЛАВИАТУРЫ",
            font=("Segoe UI", 12, "bold")
        ).pack()


        colors = ttk.Frame(
            self.root
        )

        colors.pack(
            pady=8
        )


        ttk.Button(
            colors,
            text="🔴 Красный",
            command=lambda:
                self.set_static(
                    255,
                    0,
                    0
                )
        ).grid(
            row=0,
            column=0,
            padx=5
        )


        ttk.Button(
            colors,
            text="🟢 Зелёный",
            command=lambda:
                self.set_static(
                    0,
                    255,
                    0
                )
        ).grid(
            row=0,
            column=1,
            padx=5
        )


        ttk.Button(
            colors,
            text="🔵 Синий",
            command=lambda:
                self.set_static(
                    0,
                    0,
                    255
                )
        ).grid(
            row=0,
            column=2,
            padx=5
        )


        ttk.Button(
            colors,
            text="⚪ Белый",
            command=lambda:
                self.set_static(
                    255,
                    255,
                    255
                )
        ).grid(
            row=0,
            column=3,
            padx=5
        )


        ttk.Button(
            colors,
            text="🎨 Свой цвет",
            command=self.choose_background
        ).grid(
            row=0,
            column=4,
            padx=5
        )


        # -------------------------------------------------
        # BRIGHTNESS
        # -------------------------------------------------

        brightness_frame = ttk.Frame(
            self.root
        )

        brightness_frame.pack(
            pady=8
        )


        ttk.Label(
            brightness_frame,
            text="Яркость:"
        ).pack(
            side="left",
            padx=5
        )


        self.brightness_var = tk.IntVar(
            value=5
        )


        self.brightness_scale = ttk.Scale(
            brightness_frame,
            from_=0,
            to=5,
            orient="horizontal",
            command=self.brightness_changed
        )

        self.brightness_scale.set(
            5
        )

        self.brightness_scale.pack(
            side="left",
            padx=5
        )


        self.brightness_label = ttk.Label(
            brightness_frame,
            text="5"
        )

        self.brightness_label.pack(
            side="left",
            padx=5
        )


        # -------------------------------------------------
        # CYCLE
        # -------------------------------------------------

        ttk.Button(
            self.root,
            text="🌈 Цикл всей клавиатуры",
            command=self.toggle_cycle
        ).pack(
            pady=10
        )


        ttk.Separator(
            self.root,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=30,
            pady=15
        )


        # -------------------------------------------------
        # PER KEY
        # -------------------------------------------------

        ttk.Label(
            self.root,
            text="ТЕСТ PER-KEY",
            font=("Segoe UI", 12, "bold")
        ).pack()


        ttk.Label(
            self.root,
            text="Экспериментальный протокол 0x24/0x38"
        ).pack(
            pady=3
        )


        ttk.Button(
            self.root,
            text="🧪 Попробовать Per-Key",
            command=self.per_key_test
        ).pack(
            pady=8
        )


        # -------------------------------------------------
        # LOG
        # -------------------------------------------------

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


    # =====================================================
    # LOG
    # =====================================================

    def log(self, text):

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


    # =====================================================
    # DEVICE SEARCH
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


    # =====================================================
    # CONNECT
    # =====================================================

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
                self.device_info[
                    "path"
                ]
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


        # hidapi для этого интерфейса
        # требует Report ID перед payload.
        #
        # Именно поэтому фактически передаём:
        #
        # [0] + 64-byte packet
        #
        data = [0] + packet


        result = self.device.write(
            data
        )


        self.log(
            "TX: "
            + " ".join(
                f"{x:02X}"
                for x in packet[:24]
            )
            + " ..."
        )


        self.log(
            "write() = "
            + str(result)
        )


        return result >= 0


    # =====================================================
    # STATIC RGB
    # =====================================================

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

            packet = make_static_packet(
                r,
                g,
                b
            )


            # Используем текущую яркость.
            packet[17] = self.brightness


            ok = self.send(
                packet
            )


            if ok:

                self.status.set(
                    "🟢 RGB отправлен: "
                    f"#{r:02X}{g:02X}{b:02X} "
                    f"яркость {self.brightness}"
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
    # BRIGHTNESS
    # =====================================================

    def brightness_changed(
        self,
        value
    ):

        level = int(
            round(
                float(value)
            )
        )


        self.brightness = level

        self.brightness_var.set(
            level
        )

        self.brightness_label.config(
            text=str(level)
        )


        # Отправляем текущий цвет
        # с новой яркостью.

        try:

            r, g, b = self.background


            packet = make_static_packet(
                r,
                g,
                b
            )


            packet[17] = level


            self.send(
                packet
            )


            self.status.set(
                f"Яркость: {level}"
            )


        except Exception as e:

            self.log(
                "Brightness ERROR: "
                + repr(e)
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

                    self.background = (
                        r,
                        g,
                        b
                    )


                    packet = make_static_packet(
                        r,
                        g,
                        b
                    )


                    packet[17] = (
                        self.brightness
                    )


                    # ВАЖНО:
                    # цикл теперь использует
                    # тот же send(), что и кнопки.

                    self.send(
                        packet
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
    # PER-KEY
    # =====================================================

    def make_per_key_packet(
        self
    ):

        packet = [0] * REPORT_SIZE


        # Это пока только
        # экспериментальный пакет.
        #
        # Полный per-key blob мы
        # строим только после полного
        # разбора официального протокола.

        packet[0] = 0xAA
        packet[1] = 0x24
        packet[2] = 0x38


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
            "По Wireshark обнаружены реальные "
            "пакеты 0xAA 0x24 0x38.\n\n"
            "Полная таблица клавиш пока "
            "не реализована.\n\n"
            "Отправить тестовый пакет?"
        )


        if not answer:

            return


        try:

            packet = (
                self.make_per_key_packet()
            )


            self.send(
                packet
            )


            self.log(
                "Per-Key тестовый пакет отправлен."
            )


            messagebox.showinfo(
                "Per-Key",
                "Тестовый Per-Key пакет отправлен."
            )


        except Exception as e:

            self.log(
                "Per-Key ERROR: "
                + repr(e)
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
```
