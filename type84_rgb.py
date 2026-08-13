import tkinter as tk
from tkinter import ttk, messagebox
import hid

VID = 0x0C45
PID = 0x8009
TARGET_INTERFACE = 2
TARGET_USAGE_PAGE = 0xFF68
TARGET_USAGE = 0x61

class Type84App:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Square IO Type 84 RGB")
        self.root.geometry("620x430")
        self.device = None

        title = ttk.Label(
            root,
            text="Red Square IO Type 84 RGB",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(20, 5))

        ttk.Label(
            root,
            text="USB: 0C45:8009 • RGB interface: MI_02"
        ).pack(pady=(0, 20))

        frame = ttk.Frame(root)
        frame.pack(fill="x", padx=30)

        self.status = tk.StringVar(value="Устройство ещё не проверено")
        ttk.Label(
            frame,
            textvariable=self.status,
            font=("Segoe UI", 11)
        ).pack(pady=10)

        ttk.Button(
            frame,
            text="Найти клавиатуру",
            command=self.scan
        ).pack(fill="x", pady=5)

        ttk.Button(
            frame,
            text="Проверить MI_02",
            command=self.connect
        ).pack(fill="x", pady=5)

        self.info = tk.Text(
            root,
            height=12,
            width=70,
            state="disabled"
        )
        self.info.pack(padx=30, pady=20, fill="both", expand=True)

    def log(self, text):
        self.info.config(state="normal")
        self.info.insert("end", text + "\n")
        self.info.see("end")
        self.info.config(state="disabled")

    def find_device(self):
        devices = hid.enumerate(VID, PID)

        for d in devices:
            if (
                d.get("interface_number") == TARGET_INTERFACE
                and d.get("usage_page") == TARGET_USAGE_PAGE
                and d.get("usage") == TARGET_USAGE
            ):
                return d

        return None

    def scan(self):
        self.log("Поиск IO Type 84...")
        device = self.find_device()

        if not device:
            self.status.set("❌ Type 84 не найдена")
            self.log("MI_02 не найден.")
            messagebox.showerror(
                "Не найдено",
                "Не найден интерфейс MI_02 клавиатуры."
            )
            return

        self.status.set("✅ Type 84 найдена")
        self.log("Устройство найдено!")
        self.log("VID: 0x0C45")
        self.log("PID: 0x8009")
        self.log("Interface: MI_02")
        self.log("Usage Page: 0xFF68")
        self.log("Usage: 0x61")
        self.log("Product: " + str(device.get("product_string")))
        self.log("Path: " + str(device.get("path")))

    def connect(self):
        device_info = self.find_device()

        if not device_info:
            self.status.set("❌ Устройство не найдено")
            self.log("Сначала подключите клавиатуру по USB.")
            return

        try:
            if self.device:
                self.device.close()

            self.device = hid.device()
            self.device.open_path(device_info["path"])

            self.status.set("🟢 MI_02 подключён")
            self.log("")
            self.log("=== MI_02 успешно открыт ===")
            self.log("Manufacturer: " +
                     str(self.device.get_manufacturer_string()))
            self.log("Product: " +
                     str(self.device.get_product_string()))
            self.log("")
            self.log("RGB-команды пока НЕ отправляются.")
            self.log("Соединение готово.")

        except Exception as e:
            self.status.set("❌ Ошибка подключения")
            self.log("Ошибка: " + repr(e))
            messagebox.showerror("Ошибка", repr(e))

def main():
    root = tk.Tk()
    app = Type84App(root)

    def close():
        try:
            if app.device:
                app.device.close()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()

if __name__ == "__main__":
    main()
