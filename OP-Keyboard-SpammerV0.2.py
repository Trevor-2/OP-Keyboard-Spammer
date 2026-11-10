import sys
import os
import time
import threading
import atexit
import tkinter as tk
from tkinter import messagebox

def resource_path(relative_path):
    """ Get absolute path to resource, ensuring compatibility with PyInstaller and Shortcuts """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- OS & High DPI Optimization ---
IS_WIN = sys.platform == "win32"

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    # Enable Highest DPI Awareness for 4K/Scaling (Per-Monitor V2)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    user32 = ctypes.windll.user32
    winmm = ctypes.windll.winmm  # For High-Precision Timers
    
    # Crash-proof high-precision timer allocation
    winmm.timeBeginPeriod.argtypes = [ctypes.c_uint]
    winmm.timeEndPeriod.argtypes = [ctypes.c_uint]
    winmm.timeBeginPeriod(1)
    atexit.register(lambda: winmm.timeEndPeriod(1))

    # --- Windows API Constants ---
    INPUT_KEYBOARD = 1
    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_KEYUP = 0x0002
    MAPVK_VK_TO_VSC = 0
    GWL_EXSTYLE = -20
    WS_EX_APPWINDOW = 0x00040000
    WS_EX_TOOLWINDOW = 0x00000080
    GA_ROOT = 2
    SW_MINIMIZE = 6

    ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

    if ctypes.sizeof(ctypes.c_void_p) == 8:
        GetWindowLongPtr = user32.GetWindowLongPtrW
        SetWindowLongPtr = user32.SetWindowLongPtrW
        GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
        GetWindowLongPtr.restype = ULONG_PTR
        SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ULONG_PTR]
        SetWindowLongPtr.restype = ULONG_PTR
    else:
        GetWindowLongPtr = user32.GetWindowLongW
        SetWindowLongPtr = user32.SetWindowLongW

    user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
    user32.GetAncestor.restype = wintypes.HWND

    # --- Structs for SendInput ---
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ULONG_PTR)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort), ("wParamH", ctypes.c_ushort)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", ULONG_PTR)]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", INPUT_UNION)]

    def send_scancode(scancode: int, is_keyup: bool = False):
        flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if is_keyup else 0)
        inp = INPUT(type=INPUT_KEYBOARD, ii=INPUT_UNION(ki=KEYBDINPUT(0, scancode, flags, 0, 0)))
        user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

    def is_key_down(vk_code: int) -> bool:
        return bool(user32.GetAsyncKeyState(vk_code) & 0x8000)

else:
    # Safe Fallbacks for macOS / Linux (Zero overhead)
    def is_key_down(vk_code: int) -> bool: return False
    def send_scancode(scancode: int, is_keyup: bool = False): pass


VK_NAME_MAP = {
    0x20: "Space", 0x0D: "Enter", 0x09: "Tab", 0x1B: "Esc", 0x08: "Backspace",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4", 0x74: "F5", 0x75: "F6",
    0x76: "F7", 0x77: "F8", 0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12"
}
MODIFIERS_VK = {"ctrl": 0x11, "alt": 0x12, "shift": 0x10}

def is_combo_down(modifiers, main_vk) -> bool:
    if not IS_WIN or not is_key_down(main_vk): return False
    return all(is_key_down(MODIFIERS_VK[mod]) for mod in modifiers if mod in MODIFIERS_VK)

# --- Theme Configuration ---
THEMES = {
    "dark": {
        "bg": "#1E1E1E", "header_bg": "#2D2D30", "fg": "#FFFFFF", "sub_fg": "#B0B0B0",
        "input_bg": "#252526", "btn_bg": "#252526", "btn_active_bg": "#333334",
        "min_hover": "#3E3E42", "pin_on": "#00E676", "pin_off": "#888888",
        "status_stopped": "#FF4D4D", "status_running": "#00E676",
        "start_btn": "#007ACC", "start_btn_active": "#005A9E",
        "stop_btn": "#E81123", "switch_bg": "#3E3E42", "switch_knob": "#007ACC"
    },
    "light": {
        "bg": "#F3F3F3", "header_bg": "#E1E1E1", "fg": "#000000", "sub_fg": "#555555",
        "input_bg": "#FFFFFF", "btn_bg": "#FFFFFF", "btn_active_bg": "#E5E5E5",
        "min_hover": "#D0D0D0", "pin_on": "#00A843", "pin_off": "#666666",
        "status_stopped": "#D32F2F", "status_running": "#00A843",
        "start_btn": "#007ACC", "start_btn_active": "#005A9E",
        "stop_btn": "#E81123", "switch_bg": "#BFBFBF", "switch_knob": "#FFB900"
    }
}

# --- GUI Application ---
class KeyAutoClickerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # Hide window immediately to prevent flickering during initial draw
        self.withdraw()

        self.title("OP Keyboard Spammer")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(resource_path("keyboard.ico"))
        except Exception:
            pass

        self.current_theme = "dark"
        self.always_on_top = True
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.target_combo = ((), 0x58, "X")
        self.hotkey_combo = ((), 0x77, "F8")

        self.is_capturing = False
        self.is_running = False

        self._create_custom_titlebar()
        self._build_widgets()
        self._apply_theme()

        # Responsive DPI calculation with robust Min-Width Protection
        self.update_idletasks()
        req_w = max(self.winfo_reqwidth(), 400)
        req_h = self.winfo_reqheight()
        self.geometry(f"{req_w + 12}x{req_h + 12}")
        self.minsize(req_w, req_h)

        if IS_WIN:
            self.hotkey_listener_running = True
            threading.Thread(target=self._hotkey_listener, daemon=True).start()
        else:
            self.hotkey_listener_running = False

    def _create_custom_titlebar(self):
        self.header_frame = tk.Frame(self, height=34)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.header_frame.pack_propagate(False)

        self.title_label = tk.Label(self.header_frame, text="⌨ OP Keyboard Spammer", font=("Segoe UI", 9, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=10)

        self.close_btn = tk.Label(self.header_frame, text="✕", font=("Segoe UI", 9, "bold"), width=3)
        self.close_btn.pack(side=tk.RIGHT, fill=tk.Y)
        self.close_btn.bind("<Button-1>", lambda e: self.on_close())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(bg="#E81123", fg="#FFFFFF"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(
            bg=THEMES[self.current_theme]["header_bg"], fg=THEMES[self.current_theme]["fg"]
        ))

        self.min_btn = tk.Label(self.header_frame, text="—", font=("Segoe UI", 9, "bold"), width=3)
        self.min_btn.pack(side=tk.RIGHT, fill=tk.Y)
        self.min_btn.bind("<Button-1>", lambda e: self.minimize_window())
        self.min_btn.bind("<Enter>", lambda e: self.min_btn.config(bg=THEMES[self.current_theme]["min_hover"]))
        self.min_btn.bind("<Leave>", lambda e: self.min_btn.config(bg=THEMES[self.current_theme]["header_bg"]))

        self.pin_btn = tk.Label(self.header_frame, text="⬛ Pin", font=("Segoe UI", 9, "bold"), cursor="hand2", padx=4)
        self.pin_btn.pack(side=tk.RIGHT, fill=tk.Y)
        self.pin_btn.bind("<Button-1>", lambda e: self._toggle_on_top())

        self.switch_canvas = tk.Canvas(self.header_frame, width=44, height=22, bd=0, highlightthickness=0, cursor="hand2")
        self.switch_canvas.pack(side=tk.RIGHT, padx=8, pady=6)
        self.switch_canvas.bind("<Button-1>", lambda e: self._toggle_theme())

        # Cross-platform safe drag bindings
        for widget in (self.header_frame, self.title_label):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

    def _draw_theme_switch(self):
        t = THEMES[self.current_theme]
        self.switch_canvas.config(bg=t["header_bg"])
        self.switch_canvas.delete("all")
        
        self.switch_canvas.create_oval(2, 2, 20, 20, fill=t["switch_bg"], outline="")
        self.switch_canvas.create_oval(24, 2, 42, 20, fill=t["switch_bg"], outline="")
        self.switch_canvas.create_rectangle(11, 2, 33, 20, fill=t["switch_bg"], outline="")

        if self.current_theme == "dark":
            self.switch_canvas.create_oval(4, 4, 18, 18, fill=t["switch_knob"], outline="")
        else:
            self.switch_canvas.create_oval(26, 4, 40, 18, fill=t["switch_knob"], outline="")

    def _build_widgets(self):
        self.main_frame = tk.Frame(self, padx=15, pady=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_target = tk.Label(self.main_frame, text="Target Key:", font=("Segoe UI", 9, "bold"))
        self.lbl_target.grid(row=0, column=0, sticky="w", pady=6)
        
        self.target_btn = tk.Button(
            self.main_frame, text=self.target_combo[2], relief="solid", bd=1,
            font=("Segoe UI", 9, "bold"), command=lambda: self._start_capture("target")
        )
        self.target_btn.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0), ipady=2)

        self.lbl_interval = tk.Label(self.main_frame, text="Interval (sec):", font=("Segoe UI", 9, "bold"))
        self.lbl_interval.grid(row=1, column=0, sticky="w", pady=6)
        
        self.delay_entry = tk.Entry(self.main_frame, insertbackground="white", relief="solid", bd=1, font=("Segoe UI", 9))
        self.delay_entry.insert(0, "0.05")
        self.delay_entry.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0), ipady=2)

        self.lbl_hotkey = tk.Label(self.main_frame, text="Toggle Hotkey:", font=("Segoe UI", 9, "bold"))
        self.lbl_hotkey.grid(row=2, column=0, sticky="w", pady=6)
        
        self.hotkey_btn = tk.Button(
            self.main_frame, text=self.hotkey_combo[2], relief="solid", bd=1,
            font=("Segoe UI", 9, "bold"), command=lambda: self._start_capture("hotkey")
        )
        self.hotkey_btn.grid(row=2, column=1, sticky="ew", pady=6, padx=(10, 0), ipady=2)

        self.status_label = tk.Label(self.main_frame, text="Status: STOPPED", font=("Segoe UI", 10, "bold"))
        self.status_label.grid(row=3, column=0, columnspan=2, pady=12)

        self.toggle_btn = tk.Button(
            self.main_frame, text=f"START ({self.hotkey_combo[2]})",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", command=self.toggle_spammer
        )
        self.toggle_btn.grid(row=4, column=0, columnspan=2, sticky="ew", ipady=8, pady=5)

        self.note = tk.Label(
            self.main_frame, 
            text="Click key buttons to bind single key or combo.\nPress global hotkey anytime to start/pause.",
            font=("Segoe UI", 8), justify="center"
        )
        self.note.grid(row=5, column=0, columnspan=2, pady=(12, 0), sticky="ew")
        
        self.main_frame.bind("<Configure>", lambda e: self.note.config(wraplength=e.width - 10))
        self.main_frame.columnconfigure(1, weight=1)

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self.current_theme]
        self.configure(bg=t["bg"])
        self.header_frame.config(bg=t["header_bg"])
        self.title_label.config(bg=t["header_bg"], fg=t["fg"])
        self.close_btn.config(bg=t["header_bg"], fg=t["fg"])
        self.min_btn.config(bg=t["header_bg"], fg=t["fg"])
        self.pin_btn.config(bg=t["header_bg"], fg=t["pin_on"] if self.always_on_top else t["pin_off"])

        self._draw_theme_switch()

        self.main_frame.config(bg=t["bg"])
        self.lbl_target.config(bg=t["bg"], fg=t["fg"])
        self.lbl_interval.config(bg=t["bg"], fg=t["fg"])
        self.lbl_hotkey.config(bg=t["bg"], fg=t["fg"])
        self.note.config(bg=t["bg"], fg=t["sub_fg"])

        self.target_btn.config(bg=t["btn_bg"], fg=t["fg"], activebackground=t["btn_active_bg"], activeforeground=t["fg"])
        self.hotkey_btn.config(bg=t["btn_bg"], fg=t["fg"], activebackground=t["btn_active_bg"], activeforeground=t["fg"])
        self.delay_entry.config(bg=t["input_bg"], fg=t["fg"], insertbackground=t["fg"])

        if self.is_running:
            self.status_label.config(bg=t["bg"], fg=t["status_running"])
            self.toggle_btn.config(bg=t["stop_btn"], fg="#FFFFFF", activebackground=t["stop_btn"], activeforeground="#FFFFFF")
        else:
            self.status_label.config(bg=t["bg"], fg=t["status_stopped"])
            self.toggle_btn.config(bg=t["start_btn"], fg="#FFFFFF", activebackground=t["start_btn_active"], activeforeground="#FFFFFF")

    def _toggle_on_top(self, set_state=None):
        self.always_on_top = not self.always_on_top if set_state is None else set_state
        self.attributes("-topmost", self.always_on_top)
        t = THEMES[self.current_theme]
        self.pin_btn.config(text="⬛ Pin" if self.always_on_top else "⬜ Pin", fg=t["pin_on"] if self.always_on_top else t["pin_off"])

    def minimize_window(self):
        if self.always_on_top:
            self._toggle_on_top(set_state=False)

        if IS_WIN:
            raw_hwnd = self.winfo_id()
            root_hwnd = user32.GetAncestor(raw_hwnd, GA_ROOT)
            if root_hwnd:
                user32.ShowWindow(root_hwnd, SW_MINIMIZE)
            else:
                self.iconify()
        else:
            self.iconify()

    def _start_drag(self, event):
        self._x = event.x_root - self.winfo_rootx()
        self._y = event.y_root - self.winfo_rooty()

    def _on_drag(self, event):
        x = event.x_root - self._x
        y = event.y_root - self._y
        self.geometry(f"+{x}+{y}")

    def _start_capture(self, mode: str):
        if not IS_WIN:
            messagebox.showinfo("OS Limitation", "Hardware-level key capturing requires Windows DirectInput.\nPlease configure manually or use on Windows.")
            return

        if self.is_running or self.is_capturing: return
        self.is_capturing = True
        btn = self.target_btn if mode == "target" else self.hotkey_btn
        btn.config(text="[ Press Key / Combo... ]", fg="#FFD700", bg="#333334")
        threading.Thread(target=self._capture_thread, args=(mode,), daemon=True).start()

    def _capture_thread(self, mode: str):
        time.sleep(0.2)
        main_vk = None
        mods = []
        
        while self.is_capturing:
            for vk in range(0x08, 0xFF):
                if vk in (0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5): continue
                if is_key_down(vk):
                    main_vk = vk
                    break
            if main_vk: break
            # Keep CPU overhead at absolutely 0% during scanning (25Hz)
            time.sleep(0.04) 

        if is_key_down(0x11): mods.append("ctrl")
        if is_key_down(0x10): mods.append("shift")
        if is_key_down(0x12): mods.append("alt")

        if main_vk in VK_NAME_MAP:
            name = VK_NAME_MAP[main_vk]
        else:
            sc = user32.MapVirtualKeyW(main_vk, MAPVK_VK_TO_VSC)
            buf = ctypes.create_unicode_buffer(32)
            user32.GetKeyNameTextW(sc << 16, buf, 32)
            name = buf.value.upper() if buf.value else f"VK_{hex(main_vk)}"

        combo_name = "+".join([m.capitalize() for m in mods] + [name])
        combo_data = (tuple(mods), main_vk, combo_name)

        def update_gui():
            t = THEMES[self.current_theme]
            if mode == "target":
                self.target_combo = combo_data
                self.target_btn.config(text=combo_name, fg=t["fg"], bg=t["btn_bg"])
            else:
                self.hotkey_combo = combo_data
                self.hotkey_btn.config(text=combo_name, fg=t["fg"], bg=t["btn_bg"])
                if not self.is_running:
                    self.toggle_btn.config(text=f"START ({combo_name})")
            self.is_capturing = False

        while is_key_down(main_vk):
            time.sleep(0.04)
        self.after(0, update_gui)

    def toggle_spammer(self):
        if not IS_WIN:
            messagebox.showerror("OS Error", "Hardware injection is strictly Windows only.")
            return
        
        if self.is_running: self.stop_spammer()
        else: self.start_spammer()

    def start_spammer(self):
        mods, main_vk, name = self.target_combo
        if not main_vk: return messagebox.showerror("Error", "Please select a target key.")

        main_scancode = user32.MapVirtualKeyW(main_vk, MAPVK_VK_TO_VSC)
        if not main_scancode: return messagebox.showerror("Error", f"Invalid scancode for '{name}'")

        mod_scancodes = [sc for m in mods if (sc := user32.MapVirtualKeyW(MODIFIERS_VK[m], MAPVK_VK_TO_VSC))]

        try:
            interval = max(0.001, float(self.delay_entry.get().strip()))
        except ValueError:
            return messagebox.showerror("Error", "Invalid interval time format.")

        self.is_running = True
        t = THEMES[self.current_theme]
        self.status_label.config(text="Status: RUNNING", fg=t["status_running"])
        self.toggle_btn.config(text=f"STOP ({self.hotkey_combo[2]})", bg=t["stop_btn"])

        threading.Thread(target=self._spam_loop, args=(mod_scancodes, main_scancode, interval), daemon=True).start()

    def stop_spammer(self):
        self.is_running = False
        t = THEMES[self.current_theme]
        self.status_label.config(text="Status: STOPPED", fg=t["status_stopped"])
        self.toggle_btn.config(text=f"START ({self.hotkey_combo[2]})", bg=t["start_btn"])

    def _spam_loop(self, mod_scancodes: list, main_scancode: int, interval: float):
        # Micro-optimization: Cache global functions locally to skip namespace lookups during tight loops
        send = send_scancode
        slp = time.sleep
        
        while self.is_running:
            for m_sc in mod_scancodes: send(m_sc, False)
            send(main_scancode, False)
            slp(0.002)
            send(main_scancode, True)
            for m_sc in reversed(mod_scancodes): send(m_sc, True)
            slp(interval)

    def _hotkey_listener(self):
        last_state = False
        last_toggle_time = 0.0
        
        while self.hotkey_listener_running:
            if not self.is_capturing:
                mods, main_vk, _ = self.hotkey_combo
                target_main_vk = self.target_combo[1]
                
                if main_vk and not (self.is_running and main_vk == target_main_vk):
                    pressed = is_combo_down(mods, main_vk)
                    
                    # Edge-trigger detection (only triggers on the exact moment the key goes down)
                    if pressed and not last_state:
                        # Non-blocking timestamp debounce (250ms)
                        current_time = time.perf_counter()
                        if current_time - last_toggle_time > 0.25:
                            self.after(0, self.toggle_spammer)
                            last_toggle_time = current_time
                            
                    last_state = pressed
                    
            # 100Hz polling rate (0.01s). Captures human input flawlessly while keeping CPU load at ~0.00%
            time.sleep(0.01)

    def _apply_taskbar_fix(self):
        if not IS_WIN: 
            self.deiconify()
            return
        
        # Transparent transition to prevent screen flicker during DWM style handover
        self.attributes("-alpha", 0.0)
        self.overrideredirect(True)
        self.update()

        raw_hwnd = self.winfo_id()
        root_hwnd = user32.GetAncestor(raw_hwnd, GA_ROOT)

        if root_hwnd:
            style = GetWindowLongPtr(root_hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            SetWindowLongPtr(root_hwnd, GWL_EXSTYLE, style)

        # Restore visibility safely
        self.deiconify()
        self.attributes("-alpha", 1.0)

    def on_close(self):
        self.is_running = False
        self.hotkey_listener_running = False
        self.destroy()

if __name__ == "__main__":
    app = KeyAutoClickerGUI()
    # Execute Taskbar injection after Tkinter initializes HWND
    app.after(50, app._apply_taskbar_fix)
    app.mainloop()