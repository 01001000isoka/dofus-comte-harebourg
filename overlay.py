import tkinter as tk
import json
import os
import sys
import win32gui
import win32con
import win32api
import win32process
import math_dofus
from input_manager import InputEngine

TRANSPARENT_COLOR = "pink" 
BASE_WIDTH = 1920.0
BASE_HEIGHT = 1080.0

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_dofus_hwnd():
    hwnds = []
    def callback(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title, class_name = win32gui.GetWindowText(hwnd), win32gui.GetClassName(hwnd)
            if "unity" in class_name.lower() or "dofus" in title.lower():
                rect = win32gui.GetWindowRect(hwnd)
                if rect[2] - rect[0] > 300: hwnds.append(hwnd)
        return True
    win32gui.EnumWindows(callback, None)
    return hwnds[0] if hwnds else None

class ComteOverlay:
    def __init__(self, root, control_panel, config):
        self.root = root
        self.control_panel = control_panel
        self.config = config
        self.window_title = "Comte_Map_Overlay"
        self.root.title(self.window_title)
        
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.root.attributes("-alpha", 0.55) 
        self.root.config(bg=TRANSPARENT_COLOR)
        self.root.update_idletasks()
        
        hwnd = win32gui.FindWindow(None, self.window_title)
        if hwnd:
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.shield = tk.Toplevel(self.root)
        self.shield.title("Comte_Shield")
        self.shield.overrideredirect(True)
        self.shield.attributes("-topmost", True)
        self.shield.attributes("-alpha", 0.01) 
        self.shield.config(bg="black")
        
        self.shield.update_idletasks()
        hwnd_shield = win32gui.FindWindow(None, "Comte_Shield")
        if hwnd_shield:
            ex_style = win32gui.GetWindowLong(hwnd_shield, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd_shield, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_NOACTIVATE)
            
        self.shield.withdraw()
        self.is_shield_active = False

        self.grille_db = []
        self.rendered_cells = {} 
        self.last_w, self.last_h = 0, 0
        self.id_to_coord, self.coord_to_id = math_dofus.build_dofus_grid()

        self.player_cell, self.target_cell, self.resolution_cell = None, None, None
        self.base_angle = 360 
        self.melee_hits = 0
        self.show_grid = False

        self.input_engine = InputEngine(self.is_dofus_active)
        self.load_database()
        self.hook_inputs()
        self.track_dofus_window()

    def load_database(self):
        db_path = resource_path("grille_shakra_db.json")
        if not os.path.exists(db_path): return
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                grille_raw = json.load(f)
            sorted_keys = sorted(grille_raw.keys(), key=lambda k: (grille_raw[k]['y'], grille_raw[k]['x']))
            self.grille_db = []
            for key in sorted_keys:
                self.grille_db.append((grille_raw[key]['x'], grille_raw[key]['y']))
        except Exception: pass

    def is_dofus_active(self):
        dofus_hwnd = get_dofus_hwnd()
        if not dofus_hwnd: return False
        return win32gui.GetForegroundWindow() == dofus_hwnd

    def hook_inputs(self):
        # 1. Nettoyage
        self.input_engine.clear()
        
        # 2. Raccourcis Classiques de Combat uniquement (gérés par ton InputEngine)
        self.input_engine.register(self.config.get('ping_player', ''), lambda: self.ping_cell('player'))
        self.input_engine.register(self.config.get('ping_target', ''), lambda: self.ping_cell('target'))
        self.input_engine.register(self.config.get('hotkey_90', ''), lambda: self.control_panel.trigger_button_by_angle(90))
        self.input_engine.register(self.config.get('hotkey_180', ''), lambda: self.control_panel.trigger_button_by_angle(180))
        self.input_engine.register(self.config.get('hotkey_270', ''), lambda: self.control_panel.trigger_button_by_angle(270))
        self.input_engine.register(self.config.get('hotkey_360', ''), lambda: self.control_panel.trigger_button_by_angle(360))
        self.input_engine.register(self.config.get('hotkey_reset', ''), lambda: self.control_panel.reset_turn_action())

        # NB: Les raccourcis de calibrage (Ctrl+Flèches) ont été déplacés dans track_dofus_window 
        # pour éviter les bugs de la librairie Keyboard !

    def set_show_grid(self, val):
        self.show_grid = val
        self.render_scaled_grid(self.last_w, self.last_h)

    def adjust_calibration(self, param, delta):
        if param == 'scale': self.config['scale'] += delta
        elif param == 'x': self.config['offset_x'] += delta
        elif param == 'y': self.config['offset_y'] += delta
        
        self.control_panel.update_calib_ui(self.config['scale'], self.config['offset_x'], self.config['offset_y'])
        self.render_scaled_grid(self.last_w, self.last_h)
        
        # Sauvegarde 500ms après avoir relâché les touches pour ne pas spammer le fichier JSON
        if hasattr(self, 'save_timer'):
            self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(500, lambda: self.control_panel.save_callback(self.config))

    def reset_turn(self):
        self.player_cell = None
        self.target_cell = None
        self.resolution_cell = None
        self.base_angle = 360
        self.melee_hits = 0
        self.render_scaled_grid(self.last_w, self.last_h)

    def set_confusion(self, angle):
        if self.base_angle == angle:
            return
        self.base_angle = angle
        self.calculate_resolution()
        
    def set_melee_hits(self, hits):
        self.melee_hits = hits
        self.calculate_resolution()

    def ping_cell(self, role):
        if not self.rendered_cells: return
        mouse_x, mouse_y = win32gui.GetCursorPos()
        dofus_hwnd = get_dofus_hwnd()
        if not dofus_hwnd: return

        try:
            client_pt = win32gui.ScreenToClient(dofus_hwnd, (mouse_x, mouse_y))
            rel_x, rel_y = client_pt[0], client_pt[1]
        except: return

        closest_cell, min_dist = None, float('inf')
        for cid, (cx, cy) in self.rendered_cells.items():
            dist = ((cx - rel_x) / 2.0)**2 + (cy - rel_y)**2
            if dist < min_dist:
                min_dist, closest_cell = dist, cid

        if closest_cell is not None:
            if role == 'player': self.player_cell = closest_cell
            elif role == 'target': self.target_cell = closest_cell
            self.calculate_resolution() 

    def calculate_resolution(self):
        if self.player_cell is not None and self.target_cell is not None:
            eff_angle = (self.base_angle - (self.melee_hits * 90)) % 360
            if eff_angle == 0: 
                eff_angle = 360
                
            if eff_angle == 360:
                self.resolution_cell = self.target_cell
            else:
                px, py = self.id_to_coord[self.player_cell]
                tx, ty = self.id_to_coord[self.target_cell]
                dx, dy = tx - px, ty - py

                if eff_angle == 90: aim_x, aim_y = px - dy, py + dx
                elif eff_angle == 180: aim_x, aim_y = px - dx, py - dy
                elif eff_angle == 270: aim_x, aim_y = px + dy, py - dx

                self.resolution_cell = self.coord_to_id.get((aim_x, aim_y), None)
        else:
            self.resolution_cell = None

        self.render_scaled_grid(self.last_w, self.last_h)

    def draw_flashy_tile(self, cx, cy, hw, hh, color_edge, color_mid, color_center):
        clip = 0.20  
        def get_rounded_pts(scale):
            shw = hw * scale
            shh = hh * scale
            sdx = shw * clip
            sdy = shh * clip
            return [
                cx - sdx, cy - shh + sdy, cx + sdx, cy - shh + sdy,
                cx + shw - sdx, cy - sdy, cx + shw - sdx, cy + sdy,
                cx + sdx, cy + shh - sdy, cx - sdx, cy + shh - sdy,
                cx - shw + sdx, cy + sdy, cx - shw + sdx, cy - sdy
            ]

        self.canvas.create_polygon(get_rounded_pts(1.0), fill=color_edge, outline=color_edge, width=2, smooth=True, tags="grid")
        self.canvas.create_polygon(get_rounded_pts(0.70), fill=color_mid, outline="", smooth=True, tags="grid")
        self.canvas.create_polygon(get_rounded_pts(0.35), fill=color_center, outline="", smooth=True, tags="grid")

    def render_scaled_grid(self, current_w, current_h):
        if not self.grille_db or current_w == 0: return
        self.canvas.delete("all")
        self.rendered_cells.clear() 
        
        final_scale = (current_h / BASE_HEIGHT) * self.config['scale']
        final_offset_x = (current_w - (BASE_WIDTH * final_scale)) / 2.0 + self.config['offset_x']
        final_offset_y = (current_h - (BASE_HEIGHT * final_scale)) / 2.0 + self.config['offset_y']
        
        hw, hh = (43 * final_scale) - 1, (21.5 * final_scale) - 1

        for idx, (orig_x, orig_y) in enumerate(self.grille_db):
            x = int((orig_x * final_scale) + final_offset_x)
            y = int((orig_y * final_scale) + final_offset_y)
            self.rendered_cells[idx] = (x, y)
            
            # --- LA GRILLE DE CALIBRAGE THÉORIQUE ---
            if self.show_grid:
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill="#00FFFF", outline="", tags="grid")
            
            if idx == self.target_cell:
                self.draw_flashy_tile(x, y, hw, hh, "#8b0000", "#e74c3c", "#ffb8b8")
            elif idx == self.resolution_cell:
                self.draw_flashy_tile(x, y, hw, hh, "#4a235a", "#8e44ad", "#e8daef")
            elif idx == self.player_cell:
                self.draw_flashy_tile(x, y, hw, hh, "#145a32", "#2ecc71", "#d5f5e3")

    def _is_mod_pressed(self, mod):
        if mod == 'ctrl': return win32api.GetAsyncKeyState(win32con.VK_CONTROL) < 0
        if mod == 'alt': return win32api.GetAsyncKeyState(win32con.VK_MENU) < 0
        if mod == 'shift': return win32api.GetAsyncKeyState(win32con.VK_SHIFT) < 0
        return False

    def track_dofus_window(self):
        dofus_hwnd = get_dofus_hwnd()
        active_hwnd = win32gui.GetForegroundWindow() 
        
        _, active_pid = win32process.GetWindowThreadProcessId(active_hwnd)
        current_pid = os.getpid()
        
        if dofus_hwnd:
            try:
                rect = win32gui.GetClientRect(dofus_hwnd)
                width, height = rect[2] - rect[0], rect[3] - rect[1]
                pt = win32gui.ClientToScreen(dofus_hwnd, (0, 0))
                win_x, win_y = pt[0], pt[1]
                
                if width != self.last_w or height != self.last_h:
                    if width > 0 and height > 0:
                        self.last_w, self.last_h = width, height
                        self.render_scaled_grid(width, height)
                
                if active_hwnd == dofus_hwnd or active_pid == current_pid:
                    if width > 0 and height > 0:
                        self.root.geometry(f"{width}x{height}+{win_x}+{win_y}")
                        
                        # ==================================================
                        # NOUVEAU CALIBRAGE DIRECT & SANS BUG (MODE GLISSADE)
                        # ==================================================
                        # S'active QUE si la grille est visible sur l'interface
                        if self.show_grid and self._is_mod_pressed('ctrl'):
                            # Déplacements
                            if win32api.GetAsyncKeyState(win32con.VK_UP) < 0: self.adjust_calibration('y', -1)
                            elif win32api.GetAsyncKeyState(win32con.VK_DOWN) < 0: self.adjust_calibration('y', 1)
                            
                            if win32api.GetAsyncKeyState(win32con.VK_LEFT) < 0: self.adjust_calibration('x', -1)
                            elif win32api.GetAsyncKeyState(win32con.VK_RIGHT) < 0: self.adjust_calibration('x', 1)
                            
                            # Zoom / Dezoom
                            if (win32api.GetAsyncKeyState(0x6B) < 0 or win32api.GetAsyncKeyState(0xBB) < 0 or win32api.GetAsyncKeyState(0x21) < 0):
                                self.adjust_calibration('scale', 0.001) # Numpad+, Touche +, ou PageUp
                            elif (win32api.GetAsyncKeyState(0x6D) < 0 or win32api.GetAsyncKeyState(0x36) < 0 or win32api.GetAsyncKeyState(0x22) < 0):
                                self.adjust_calibration('scale', -0.001) # Numpad-, Touche 6, ou PageDown

                        # ==================================================

                        block_clicks = False
                        if active_hwnd == dofus_hwnd:
                            mouse_binds = [self.config.get('ping_target', ''), self.config.get('ping_player', '')]
                            for bind in mouse_binds:
                                parts = bind.lower().replace(' ', '').split('+')
                                if any(c in parts for c in ['left', 'right', 'middle', 'mb4', 'mb5']):
                                    mods = [p for p in parts if p in ['ctrl', 'alt', 'shift']]
                                    if mods and all(self._is_mod_pressed(m) for m in mods):
                                        block_clicks = True
                                        break
                        
                        if block_clicks:
                            if not self.is_shield_active:
                                self.shield.geometry(f"{width}x{height}+{win_x}+{win_y}")
                                self.shield.deiconify()
                                self.control_panel.root.lift() 
                                self.is_shield_active = True
                        else:
                            if self.is_shield_active:
                                self.shield.withdraw()
                                self.is_shield_active = False
                else:
                    self.root.geometry(f"1x1+-9999+-9999")
                    if self.is_shield_active:
                        self.shield.withdraw()
                        self.is_shield_active = False
            except: pass 
        else:
            self.root.geometry(f"1x1+-9999+-9999")
            if self.is_shield_active:
                self.shield.withdraw()
                self.is_shield_active = False
            
        self.root.after(30, self.track_dofus_window)