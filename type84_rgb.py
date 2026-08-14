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

# Задержка между HID OUT.
# По твоему тесту 20 мс работает нормально.
PACKET_DELAY = 0.020


# ============================================================
# TYPE 84 RGB
# ============================================================

class Type84RGB:

    def __init__(self, root):

        self.root = root

        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("760x700")

        self.device = None
        self.device_info = None

        self.running = False
        self.per_key_cycle_running = False

        # Цвет всей клавиатуры
        self.background = (255, 0, 0)

        # Состояние всех 128 протокольных LED.
        #
        # None = выключен
        # (R,G,B) = цвет
        #
        # ВАЖНО:
        # индекс здесь именно протокольный индекс 0..127.
        self.key_colors = [None] * 128

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

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

        # ----------------------------------------------------
        # DEVICE
        # ----------------------------------------------------

        device_frame = ttk.LabelFrame(
            self.root,
            text="Устройство"
        )
        device_frame.pack(
            fill="x",
            padx=30,
            pady=5
        )

        ttk.Button(
            device_frame,
            text="1. Найти клавиатуру",
            command=self.scan
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Button(
            device_frame,
            text="2. Подключить MI_02",
            command=self.connect
        ).pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        # ----------------------------------------------------
        # WHOLE KEYBOARD
        # ----------------------------------------------------

        keyboard_frame = ttk.LabelFrame(
            self.root,
            text="Вся клавиатура"
        )
        keyboard_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        ttk.Button(
            keyboard_frame,
            text="🎨 Выбрать цвет всей клавиатуры",
            command=self.choose_background
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Button(
            keyboard_frame,
            text="👤 Переключить в пользовательский режим",
            command=self.set_user_mode
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ttk.Label(
            keyboard_frame,
            text=(
                "Пользовательский режим:\n"
                "AA 23 10 00 00 00 01 00 80 ..."
            )
        ).pack(
            pady=(2, 8)
        )

        # ----------------------------------------------------
        # PER KEY
        # ----------------------------------------------------

        per_key_frame = ttk.LabelFrame(
            self.root,
            text="Per-Key RGB"
        )
        per_key_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        ttk.Label(
            per_key_frame,
            text=(
                "Индекс — протокольный индекс LED от 0 до 127.\n"
                "Без дополнительных смещений."
            )
        ).pack(pady=(8, 5))

        index_frame = ttk.Frame(per_key_frame)
        index_frame.pack(pady=5)

        ttk.Label(
            index_frame,
            text="Индекс:"
        ).pack(
            side="left",
            padx=(0, 5)
        )

        self.index_var = tk.StringVar(
            value="49"
        )

        self.index_entry = ttk.Entry(
            index_frame,
            textvariable=self.index_var,
            width=8
        )
        self.index_entry.pack(
            side="left"
        )

        ttk.Label(
            index_frame,
            text="  (A в твоём официальном захвате = 49)"
        ).pack(
            side="left"
        )

        self.key_color_label = tk.StringVar(
            value="#FF0000"
        )

        ttk.Button(
            per_key_frame,
            text="🎨 Выбрать цвет клавиши",
            command=self.choose_key_color
        ).pack(pady=5)

        ttk.Label(
            per_key_frame,
            textvariable=self.key_color_label
        ).pack()

        buttons = ttk.Frame(per_key_frame)
        buttons.pack(pady=8)

        ttk.Button(
            buttons,
            text="Отправить Per-Key",
            command=self.send_per_key
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Выключить эту клавишу",
            command=self.disable_key
        ).grid(
            row=0,
            column=1,
            padx=5
        )

        ttk.Button(
            buttons,
            text="Выключить все клавиши",
            command=self.disable_all_keys
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        ttk.Button(
            per_key_frame,
            text="🌈 Цикл только выбранной клавиши",
            command=self.toggle_per_key_cycle
        ).pack(pady=(0, 8))

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        ttk.Label(
            self.root,
            text="Лог"
        ).pack()

        self.log_box = tk.Text(
            self.root,
            height=13,
            state="disabled"
        )

        self.log_box.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(5, 20)
        )

    # ========================================================
    # LOGGING
    # ========================================================

    def log(self, text):

        self.log_box.config(
            state="normal"
        )

        self.log_box.insert(
            "end",
            text + "\n"
        )

        self.log_box.see("end")

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
        self.log("=== DEVICE ===")

        self.log(
            "Product: "
            + str(
                info.get("product_string")
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
                "HID RGB готов."
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

    # ========================================================
    # LOW LEVEL HID
    # ========================================================

    def send(self, packet, delay_after=True):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return False

        if len(packet) != REPORT_SIZE:

            raise ValueError(
                "HID report должен быть ровно 64 байта"
            )

        # hidapi:
        # первый 0 = HID Report ID,
        # дальше идут наши 64 байта протокола.
        data = [0] + packet

        result = self.device.write(
            data
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

        if delay_after:

            time.sleep(
                PACKET_DELAY
            )

        return result >= 0

    # ========================================================
    # EXACT TYPE 84 MODE PACKET
    # ========================================================

    def make_mode_packet(self, mode, r, g, b):

        packet = [0] * 64

        # Точный формат из твоего Wireshark:
        #
        # AA 23 10 00 00 00 01 00
        # 01/80
        # RR GG BB FF
        # 00 00 00 00
        # 05
        #
        # ВАЖНО:
        # здесь НЕ:
        # AA 23 10 00 00 01 ...
        #
        # а именно:
        # AA 23 10 00 00 00 01 ...

        packet[0] = 0xAA
        packet[1] = 0x23
        packet[2] = 0x10

        packet[3] = 0x00
        packet[4] = 0x00
        packet[5] = 0x00
        packet[6] = 0x01

        packet[7] = mode

        packet[8] = r
        packet[9] = g
        packet[10] = b
        packet[11] = 0xFF

        # После цвета ЧЕТЫРЕ нулевых байта.
        packet[12] = 0x00
        packet[13] = 0x00
        packet[14] = 0x00
        packet[15] = 0x00

        # После них 05.
        packet[16] = 0x05

        packet[17] = 0x00
        packet[18] = 0x00
        packet[19] = 0x00

        packet[20] = 0x00

        packet[21] = 0xAA
        packet[22] = 0x55

        return packet

    # ========================================================
    # USER MODE
    # ========================================================

    def make_user_mode_packet(self):

        return self.make_mode_packet(
            0x80,
            *self.background
        )

    def set_user_mode(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        try:

            packet = self.make_user_mode_packet()

            self.log(
                "Переключение в пользовательский режим..."
            )

            self.send(
                packet
            )

            self.status.set(
                "👤 Пользовательский режим"
            )

        except Exception as e:

            self.log(
                "USER MODE ERROR: "
                + repr(e)
            )

            messagebox.showerror(
                "Ошибка",
                repr(e)
            )

    # ========================================================
    # STATIC WHOLE KEYBOARD
    # ========================================================

    def make_static_packet(self, r, g, b):

        # mode = 0x01
        return self.make_mode_packet(
            0x01,
            r,
            g,
            b
        )

    def set_static(self, r, g, b):

        self.background = (
            r,
            g,
            b
        )

        try:

            packet = self.make_static_packet(
                r,
                g,
                b
            )

            self.send(
                packet
            )

            self.status.set(
                f"🟢 Статический RGB: "
                f"#{r:02X}{g:02X}{b:02X}"
            )

        except Exception as e:

            self.log(
                "STATIC ERROR: "
                + repr(e)
            )

            messagebox.showerror(
                "RGB ошибка",
                repr(e)
            )

    # ========================================================
    # COLOR PICKER
    # ========================================================

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

    def choose_key_color(self):

        color = colorchooser.askcolor(
            title="Цвет клавиши"
        )

        if not color or not color[0]:

            return

        r, g, b = map(
            int,
            color[0]
        )

        self.selected_key_color = (
            r,
            g,
            b
        )

        self.key_color_label.set(
            f"#{r:02X}{g:02X}{b:02X}"
        )

    # ========================================================
    # PER-KEY PROTOCOL
    # ========================================================

    def build_per_key_packets(self):

        """
        Формирует ТОЧНО 10 HID-пакетов.

        Пакет 1:
            AA 24 38 00 00 00 00 00
            index 0..13

        Пакет 2:
            AA 24 38 38 00 00 00 0E
            index 14..27

        ...

        Пакет 9:
            index 112..125

        Пакет 10:
            index 126..127

        Каждая клавиша:
            INDEX R G B

        Например A из твоего официального захвата:

            31 FF 00 00

        то есть protocol index 49 = красный.
        """

        packets = []

        for start_index in range(
            0,
            128,
            14
        ):

            packet = [0] * 64

            # ------------------------------------------------
            # HEADER
            # ------------------------------------------------

            packet[0] = 0xAA
            packet[1] = 0x24
            packet[2] = 0x38

            # Смещение в байтах:
            #
            # 14 LED * 4 bytes = 0x38
            #
            byte_offset = start_index * 4

            packet[3] = byte_offset & 0xFF
            packet[4] = (
                byte_offset >> 8
            ) & 0xFF
            packet[5] = (
                byte_offset >> 16
            ) & 0xFF
            packet[6] = (
                byte_offset >> 24
            ) & 0xFF

            packet[7] = start_index

            # ------------------------------------------------
            # LED ENTRIES
            # ------------------------------------------------

            packet_pos = 8

            end_index = min(
                start_index + 14,
                128
            )

            for index in range(
                start_index,
                end_index
            ):

                color = self.key_colors[index]

                if color is None:

                    r = 0
                    g = 0
                    b = 0

                else:

                    r, g, b = color

                # EXACT:
                #
                # [index][R][G][B]
                #
                packet[packet_pos] = index
                packet[packet_pos + 1] = r
                packet[packet_pos + 2] = g
                packet[packet_pos + 3] = b

                packet_pos += 4

            packets.append(
                packet
            )

        return packets

    # ========================================================
    # SEND COMPLETE PER-KEY STATE
    # ========================================================

    def send_complete_per_key(self):

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return False

        try:

            packets = (
                self.build_per_key_packets()
            )

            self.log(
                "Отправка полного Per-Key состояния..."
            )

            for number, packet in enumerate(
                packets,
                start=1
            ):

                self.log(
                    f"Per-Key packet "
                    f"{number}/10"
                )

                self.send(
                    packet
                )

            self.log(
                "Per-Key: все 10 пакетов отправлены."
            )

            return True

        except Exception as e:

            self.log(
                "PER-KEY ERROR: "
                + repr(e)
            )

            return False

    # ========================================================
    # READ INDEX
    # ========================================================

    def get_index(self):

        try:

            index = int(
                self.index_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "Ошибка индекса",
                "Индекс должен быть целым числом от 0 до 127."
            )

            return None

        if not 0 <= index <= 127:

            messagebox.showerror(
                "Ошибка индекса",
                "Индекс должен быть от 0 до 127."
            )

            return None

        return index

    # ========================================================
    # SEND ONE KEY
    # ========================================================

    def send_per_key(self):

        index = self.get_index()

        if index is None:

            return

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        # Если цвет ещё не выбран,
        # используем красный.
        color = getattr(
            self,
            "selected_key_color",
            (255, 0, 0)
        )

        self.key_colors[index] = color

        self.log("")
        self.log(
            f"Per-Key index {index}: "
            f"RGB {color}"
        )

        # ВАЖНО:
        # сначала гарантированно включаем
        # пользовательский режим.
        self.set_user_mode()

        # Затем отправляем все 10 пакетов
        # состояния клавиш.
        ok = self.send_complete_per_key()

        if ok:

            self.status.set(
                f"👤 Per-Key index {index} изменён"
            )

    # ========================================================
    # DISABLE ONE KEY
    # ========================================================

    def disable_key(self):

        index = self.get_index()

        if index is None:

            return

        self.key_colors[index] = None

        self.log(
            f"Per-Key index {index}: OFF"
        )

        self.set_user_mode()

        self.send_complete_per_key()

        self.status.set(
            f"⬛ Index {index} выключен"
        )

    # ========================================================
    # DISABLE ALL
    # ========================================================

    def disable_all_keys(self):

        for i in range(128):

            self.key_colors[i] = None

        self.log(
            "Все 128 Per-Key LED установлены в OFF."
        )

        self.set_user_mode()

        self.send_complete_per_key()

        self.status.set(
            "⬛ Все Per-Key клавиши выключены"
        )

    # ========================================================
    # PER-KEY CYCLE
    # ========================================================

    def toggle_per_key_cycle(self):

        index = self.get_index()

        if index is None:

            return

        if self.per_key_cycle_running:

            self.per_key_cycle_running = False

            self.status.set(
                "⏹ Per-Key цикл остановлен"
            )

            return

        if not self.device:

            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключи MI_02."
            )

            return

        self.per_key_cycle_running = True

        self.status.set(
            f"🌈 Цикл index {index}"
        )

        threading.Thread(
            target=self.per_key_cycle_thread,
            args=(index,),
            daemon=True
        ).start()

    def per_key_cycle_thread(
        self,
        index
    ):

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

        # Один раз переключаемся
        # в пользовательский режим.
        try:

            self.set_user_mode()

        except Exception as e:

            self.log(
                "Cycle mode error: "
                + repr(e)
            )

            self.per_key_cycle_running = False

            return

        while self.per_key_cycle_running:

            for r, g, b in colors:

                if not self.per_key_cycle_running:

                    break

                try:

                    # Меняем ТОЛЬКО выбранный
                    # протокольный индекс.
                    self.key_colors[index] = (
                        r,
                        g,
                        b
                    )

                    self.log(
                        f"Cycle index {index}: "
                        f"#{r:02X}{g:02X}{b:02X}"
                    )

                    # Полный Per-Key blob.
                    #
                    # Все остальные индексы остаются
                    # в self.key_colors без изменений.
                    self.send_complete_per_key()

                except Exception as e:

                    self.log(
                        "Per-Key cycle error: "
                        + repr(e)
                    )

                    self.per_key_cycle_running = False

                    break

                # Пауза между цветами.
                time.sleep(
                    0.5
                )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.running = False
        self.per_key_cycle_running = False

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

    root.protocol(
        "WM_DELETE_WINDOW",
        app.close
    )

    root.mainloop()


if __name__ == "__main__":

    main()
