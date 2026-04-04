import tkinter as tk
import ctypes
import keyboard
import threading
import time
import win32api
import win32con
import os

AZERTY_TO_SCAN = {
    'a': 16, 'z': 17, 'e': 18, 'r': 19, 't': 20, 'y': 21, 'u': 22, 'i': 23, 'o': 24, 'p': 25,
    'q': 30, 's': 31, 'd': 32, 'f': 33, 'g': 34, 'h': 35, 'j': 36, 'k': 37, 'l': 38, 'm': 39,
    'w': 44, 'x': 45, 'c': 46, 'v': 47, 'b': 48, 'n': 49,
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, '0': 11,
    'f1': 59, 'f2': 60, 'f3': 61, 'f4': 62, 'f5': 63, 'f6': 64, 'f7': 65, 'f8': 66, 'f9': 67, 'f10': 68, 'f11': 87, 'f12': 88,
    'tab': 15, 'enter': 28, 'space': 57, 'esc': 1, 'backspace': 14,
    '²': 41, '&': 2, 'é': 3, '"': 4, "'": 5, '(': 6, '-': 7, 'è': 8, '_': 9, 'ç': 10, 'à': 11, ')': 12, '=': 13,
    'num 1': 79, 'num 2': 80, 'num 3': 81, 'num 4': 75, 'num 5': 76, 'num 6': 77, 'num 7': 71, 'num 8': 72, 'num 9': 73, 'num 0': 82,
}
SCAN_TO_AZERTY = {v: k for k, v in AZERTY_TO_SCAN.items()}

class ComteControlPanel:
    def __init__(self, root, config, save_callback, rehook_callback, set_confusion_callback, set_melee_hits_callback, reset_turn_callback=None, set_grid_visibility_callback=None):
        self.root = root
        self.config = config
        self.save_callback = save_callback
        self.rehook_callback = rehook_callback
        self.set_confusion_callback = set_confusion_callback
        self.set_melee_hits_callback = set_melee_hits_callback
        self.reset_turn_callback = reset_turn_callback
        self.set_grid_visibility_callback = set_grid_visibility_callback
        
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="#1E1E1E")
        
        self.w, self.h = 250, 560 # Agrandissement pour la zone Calibrage
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{self.w}x{self.h}+{screen_w - 270}+50")

        self.root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, self.w, self.h, 20, 20)
        ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)

        self.header = tk.Frame(self.root, bg="#111111", height=25, cursor="fleur")
        self.header.pack(fill=tk.X)
        self.make_draggable(self.header)
        
        lbl_title = tk.Label(self.header, text="Outils Pi", bg="#111111", fg="#00FFFF", font=("Segoe UI", 9, "bold"), cursor="fleur")
        lbl_title.pack(side=tk.LEFT, padx=10, pady=2)
        self.make_draggable(lbl_title)

        btn_close_app = tk.Label(self.header, text="✖", bg="#111111", fg="#e74c3c", font=("Segoe UI", 10, "bold"), cursor="hand2")
        btn_close_app.pack(side=tk.RIGHT, padx=8)
        btn_close_app.bind("<Button-1>", lambda e: self.close_application())

        self.tab_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.tab_frame.pack(fill=tk.X, pady=5)
        
        self.btn_tab_combat = tk.Label(self.tab_frame, text="COMBAT", bg="#00FFFF", fg="black", font=("Segoe UI", 8, "bold"), cursor="hand2", width=14)
        self.btn_tab_combat.pack(side=tk.LEFT, padx=10)
        self.btn_tab_combat.bind("<Button-1>", lambda e: self.show_combat())

        self.btn_tab_config = tk.Label(self.tab_frame, text="CONFIG", bg="#2D2D2D", fg="white", font=("Segoe UI", 8, "bold"), cursor="hand2", width=14)
        self.btn_tab_config.pack(side=tk.RIGHT, padx=10)
        self.btn_tab_config.bind("<Button-1>", lambda e: self.show_config())

        self.page_combat = tk.Frame(self.root, bg="#1E1E1E")
        self.page_config = tk.Frame(self.root, bg="#1E1E1E")
        
        self.melee_hits = 0 
        self.is_listening = False 
        self.hotkey_btns = {}
        self.show_grid_var = tk.BooleanVar(value=False)
        self.calib_entries = {}
        
        self.build_combat_page()
        self.build_config_page()
        self.page_combat.pack(fill=tk.BOTH, expand=True)

    def close_application(self):
        keyboard.unhook_all_hotkeys()
        os._exit(0)

    def make_draggable(self, widget):
        widget.bind("<ButtonPress-1>", self.start_move)
        widget.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.win_x = self.root.winfo_x()
        self.win_y = self.root.winfo_y()

    def do_move(self, event):
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y
        self.root.geometry(f"+{self.win_x + dx}+{self.win_y + dy}")

    def show_combat(self):
        self.btn_tab_combat.config(bg="#00FFFF", fg="black")
        self.btn_tab_config.config(bg="#2D2D2D", fg="white")
        self.page_config.pack_forget()
        self.page_combat.pack(fill=tk.BOTH, expand=True)

    def show_config(self):
        self.btn_tab_config.config(bg="#00FFFF", fg="black")
        self.btn_tab_combat.config(bg="#2D2D2D", fg="white")
        self.page_combat.pack_forget()
        self.page_config.pack(fill=tk.BOTH, expand=True)

    def build_combat_page(self):
        self.buttons_data = [
            {"id": 1, "text": "100% à 90%", "angle": 270, "color": "#2ecc71"},
            {"id": 2, "text": "89% à 75%", "angle": 90, "color": "#f1c40f"},
            {"id": 3, "text": "74% à 45% (Miroir)", "angle": 180, "color": "#e67e22"},
            {"id": 4, "text": "44% à 30%", "angle": 90, "color": "#e74c3c"},
            {"id": 5, "text": "29% à 0%", "angle": 270, "color": "#c0392b"}
        ]
        self.btn_widgets = []
        for data in self.buttons_data:
            btn = tk.Label(self.page_combat, text=data["text"], font=("Segoe UI", 9, "bold"), 
                           bg="#2D2D2D", fg=data["color"], pady=5, cursor="hand2")
            btn.pack(fill=tk.X, padx=15, pady=3)
            btn.bind("<Button-1>", lambda e, d=data: self.on_button_click(d["id"], d["angle"]))
            self.btn_widgets.append({"widget": btn, "id": data["id"], "default_color": data["color"]})
        self.active_btn_id = None

        frame_cac = tk.Frame(self.page_combat, bg="#151515", bd=1, relief="sunken")
        frame_cac.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(frame_cac, text="Dégâts CàC (Lignes):", bg="#151515", fg="#AAAAAA", font=("Segoe UI", 8)).pack(pady=2)
        
        controls = tk.Frame(frame_cac, bg="#151515")
        controls.pack(pady=2)
        
        btn_minus = tk.Label(controls, text="-", bg="#2D2D2D", fg="white", font=("Segoe UI", 12, "bold"), width=3, cursor="hand2")
        btn_minus.pack(side=tk.LEFT, padx=5)
        btn_minus.bind("<Button-1>", lambda e: self.update_cac(-1))
        
        self.lbl_cac = tk.Label(controls, text="0", bg="#151515", fg="#00FFFF", font=("Segoe UI", 12, "bold"), width=3)
        self.lbl_cac.pack(side=tk.LEFT, padx=5)
        
        btn_plus = tk.Label(controls, text="+", bg="#2D2D2D", fg="white", font=("Segoe UI", 12, "bold"), width=3, cursor="hand2")
        btn_plus.pack(side=tk.LEFT, padx=5)
        btn_plus.bind("<Button-1>", lambda e: self.update_cac(1))
        
        btn_reset = tk.Label(frame_cac, text="Réinitialiser CàC", bg="#151515", fg="#e74c3c", font=("Segoe UI", 8, "underline"), cursor="hand2")
        btn_reset.pack(pady=4)
        btn_reset.bind("<Button-1>", lambda e: self.update_cac(0, reset=True))

        btn_reset_tour = tk.Label(self.page_combat, text="NOUVEAU TOUR", bg="#8e44ad", fg="white", font=("Segoe UI", 9, "bold"), pady=8, cursor="hand2")
        btn_reset_tour.pack(fill=tk.X, padx=15, pady=(5, 10))
        btn_reset_tour.bind("<Button-1>", lambda e: self.reset_turn_action())

    def update_cac(self, delta, reset=False):
        if reset: self.melee_hits = 0
        else: self.melee_hits = max(0, min(10, self.melee_hits + delta))
        self.lbl_cac.config(text=str(self.melee_hits))
        if self.melee_hits > 0: self.lbl_cac.config(fg="#ff6666") 
        else: self.lbl_cac.config(fg="#00FFFF")
        self.set_melee_hits_callback(self.melee_hits)

    def reset_turn_action(self):
        self.update_cac(0, reset=True)
        self.active_btn_id = None
        for btn_dict in self.btn_widgets:
            btn_dict["widget"].config(bg="#2D2D2D", fg=btn_dict["default_color"])
            
        if self.reset_turn_callback:
            self.reset_turn_callback()

    def build_config_page(self):
        # SECTION 1: RACCOURCIS
        tk.Label(self.page_config, text="Raccourcis (Clic pour modifier)", bg="#1E1E1E", fg="#00FFFF", font=("Segoe UI", 8, "bold")).pack(pady=(2, 5))
        
        settings = [
            ("Ping Cible", "ping_target"), ("Ping Joueur", "ping_player"),
            ("Buff 2/4 (90°)", "hotkey_90"), ("Miroir (180°)", "hotkey_180"), 
            ("Buff 1/5 (270°)", "hotkey_270"), ("Nouveau Tour", "hotkey_reset") 
        ]
        
        for label_text, config_key in settings:
            frame = tk.Frame(self.page_config, bg="#1E1E1E")
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            tk.Label(frame, text=label_text, bg="#1E1E1E", fg="#CCCCCC", font=("Segoe UI", 7)).pack(side=tk.LEFT)
            btn_clear = tk.Label(frame, text="✖", bg="#c0392b", fg="white", font=("Segoe UI", 7, "bold"), width=2, cursor="hand2")
            btn_clear.pack(side=tk.RIGHT)
            
            current_val = self.config.get(config_key, "Aucun")
            btn_assign = tk.Label(frame, text=current_val if current_val else "Aucun", bg="#2980b9", fg="white", font=("Segoe UI", 7, "bold"), width=10, cursor="hand2")
            btn_assign.pack(side=tk.RIGHT, padx=4)
            
            btn_assign.bind("<Button-1>", lambda e, k=config_key, b=btn_assign: self.catch_key(k, b))
            btn_clear.bind("<Button-1>", lambda e, k=config_key, b=btn_assign: self.apply_key(k, "", b))
            self.hotkey_btns[config_key] = btn_assign

        # SECTION 2: CALIBRAGE
        tk.Frame(self.page_config, bg="#333333", height=1).pack(fill=tk.X, padx=10, pady=10)
        tk.Label(self.page_config, text="Calibrage Grille", bg="#1E1E1E", fg="#00FFFF", font=("Segoe UI", 8, "bold")).pack()
        tk.Label(self.page_config, text="(Ctrl + Flèches/PgUp/PgDn)", bg="#1E1E1E", fg="#AAAAAA", font=("Segoe UI", 7, "italic")).pack(pady=(0, 5))

        cb_grid = tk.Checkbutton(self.page_config, text="Afficher repères théoriques", variable=self.show_grid_var,
                                 bg="#1E1E1E", fg="white", selectcolor="#2D2D2D", activebackground="#1E1E1E",
                                 font=("Segoe UI", 8), command=self.on_toggle_grid)
        cb_grid.pack()

        calib_settings = [("Échelle", "scale"), ("Offset X", "offset_x"), ("Offset Y", "offset_y")]
        for label_text, key in calib_settings:
            f = tk.Frame(self.page_config, bg="#1E1E1E")
            f.pack(fill=tk.X, padx=15, pady=2)
            tk.Label(f, text=label_text, bg="#1E1E1E", fg="#CCCCCC", font=("Segoe UI", 8)).pack(side=tk.LEFT)
            
            ent = tk.Entry(f, width=10, bg="#2D2D2D", fg="white", borderwidth=0, justify="center", font=("Segoe UI", 8))
            ent.pack(side=tk.RIGHT)
            ent.insert(0, str(self.config.get(key, 0)))
            self.calib_entries[key] = ent

        btn_save_calib = tk.Label(self.page_config, text="APPLIQUER CALIBRAGE", bg="#27ae60", fg="white", font=("Segoe UI", 8, "bold"), pady=6, cursor="hand2")
        btn_save_calib.pack(fill=tk.X, padx=15, pady=10)
        btn_save_calib.bind("<Button-1>", lambda e: self.save_calibration())

    def on_toggle_grid(self):
        if self.set_grid_visibility_callback:
            self.set_grid_visibility_callback(self.show_grid_var.get())

    def update_calib_ui(self, scale, x, y):
        self.calib_entries['scale'].delete(0, tk.END)
        self.calib_entries['scale'].insert(0, f"{scale:.4f}")
        self.calib_entries['offset_x'].delete(0, tk.END)
        self.calib_entries['offset_x'].insert(0, str(int(x)))
        self.calib_entries['offset_y'].delete(0, tk.END)
        self.calib_entries['offset_y'].insert(0, str(int(y)))

    def save_calibration(self):
        try:
            self.config['scale'] = float(self.calib_entries['scale'].get())
            self.config['offset_x'] = int(float(self.calib_entries['offset_x'].get()))
            self.config['offset_y'] = int(float(self.calib_entries['offset_y'].get()))
            self.save_callback(self.config)
            self.rehook_callback() 
            self.show_combat()
        except: pass

    def catch_key(self, config_key, btn):
        if self.is_listening: return
        self.is_listening = True
        btn.configure(text="...", bg="#f39c12", fg="black") 
        threading.Thread(target=self._listen_thread, args=(config_key, btn), daemon=True).start()

    def _listen_thread(self, config_key, btn):
        captured_key = None
        captured_mods = []
        while win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0 or win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0 or win32api.GetAsyncKeyState(win32con.VK_MBUTTON) < 0:
            time.sleep(0.01)
        time.sleep(0.1)
        
        def get_current_mods():
            mods = []
            if win32api.GetAsyncKeyState(win32con.VK_CONTROL) < 0: mods.append("ctrl")
            if win32api.GetAsyncKeyState(win32con.VK_MENU) < 0: mods.append("alt")
            if win32api.GetAsyncKeyState(win32con.VK_SHIFT) < 0: mods.append("shift")
            return mods

        def on_key(e):
            nonlocal captured_key, captured_mods
            if e.event_type == keyboard.KEY_DOWN:
                if e.name not in ['alt', 'ctrl', 'shift', 'maj', 'right alt', 'right ctrl', 'left alt', 'left ctrl', 'menu']:
                    captured_mods = get_current_mods()
                    if e.scan_code in SCAN_TO_AZERTY: captured_key = SCAN_TO_AZERTY[e.scan_code]
                    else: captured_key = e.name

        hook = keyboard.hook(on_key, suppress=True)
        
        while not captured_key:
            if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0: captured_key = "left"
            elif win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0: captured_key = "right"
            elif win32api.GetAsyncKeyState(win32con.VK_MBUTTON) < 0: captured_key = "middle"
            elif win32api.GetAsyncKeyState(0x05) < 0: captured_key = "mb4" 
            elif win32api.GetAsyncKeyState(0x06) < 0: captured_key = "mb5" 
            
            if captured_key:
                captured_mods = get_current_mods()
                break
            time.sleep(0.01)
            
        keyboard.unhook(hook)
        
        if captured_key == "esc": final_key = self.config.get(config_key, "") 
        else: final_key = "+".join(captured_mods) + "+" + captured_key if captured_mods else captured_key

        time.sleep(0.3)
        self.root.after(0, self.apply_key, config_key, final_key, btn)

    def release_modifiers(self):
        try:
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        except: pass

    def apply_key(self, config_key, new_value, btn):
        self.release_modifiers()
        if new_value: 
            for k in list(self.config.keys()):
                if k != config_key and self.config.get(k) == new_value:
                    self.config[k] = ""
                    if k in self.hotkey_btns:
                        self.hotkey_btns[k].configure(text="Aucun", bg="#2980b9")

        self.config[config_key] = new_value
        self.save_callback(self.config)
        self.rehook_callback() 
        
        btn.configure(text=new_value if new_value else "Aucun", bg="#2980b9", fg="white")
        self.is_listening = False

        self.btn_tab_config.config(text="OK!", bg="#2ecc71", fg="black")
        self.root.after(800, lambda: self.btn_tab_config.config(text="CONFIG", bg="#00FFFF"))

    def trigger_button_by_angle(self, target_angle):
        for data in self.buttons_data:
            if data["angle"] == target_angle:
                self.root.after(0, lambda d=data: self.on_button_click(d["id"], d["angle"]))
                break

    def on_button_click(self, btn_id, angle):
        self.active_btn_id = btn_id
        self.set_confusion_callback(angle)
        for btn_dict in self.btn_widgets:
            w, b_id = btn_dict["widget"], btn_dict["id"]
            if b_id == self.active_btn_id:
                w.config(bg="#00FFFF", fg="black")
            else:
                w.config(bg="#2D2D2D", fg=btn_dict["default_color"])