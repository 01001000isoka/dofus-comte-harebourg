import tkinter as tk
import config_manager
import sys
import os
from gui import ComteControlPanel
from overlay import ComteOverlay

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    config = config_manager.load_config()
    root = tk.Tk()
    control_root = tk.Toplevel(root)
    
    icon_path = resource_path("logo.ico")
    if os.path.exists(icon_path):
        try: control_root.iconbitmap(icon_path)
        except: pass

    global app
    app = None

    panel = ComteControlPanel(
        control_root, 
        config, 
        save_callback=config_manager.save_config,
        rehook_callback=lambda: app.hook_inputs() if app else None,
        set_confusion_callback=lambda angle: app.set_confusion(angle) if app else None,
        set_melee_hits_callback=lambda hits: app.set_melee_hits(hits) if app else None,
        reset_turn_callback=lambda: app.reset_turn() if app else None,
        set_grid_visibility_callback=lambda val: app.set_show_grid(val) if app else None
    )

    app = ComteOverlay(root, panel, config)
    root.mainloop()

if __name__ == "__main__":
    main()