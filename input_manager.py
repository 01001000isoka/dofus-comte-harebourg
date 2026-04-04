import keyboard
import mouse

class InputEngine:
    def __init__(self, is_active_func):
        self.is_active_func = is_active_func
        self.hotkeys = {}
        mouse.hook(self._mouse_listener)

    def register(self, hotkey_str, callback):
        parts = hotkey_str.lower().replace(' ', '').split('+')
        mouse_buttons = ['left', 'right', 'middle', 'mb4', 'mb5']
        
        is_mouse_bind = any(b in parts for b in mouse_buttons)
        
        if is_mouse_bind:
            self.hotkeys[hotkey_str] = {'parts': parts, 'callback': callback}
        else:
            def secure_callback():
                if self.is_active_func():
                    callback()
                    for p in parts:
                        if p in ['ctrl', 'alt', 'shift']:
                            keyboard.release(p)
            try:
                keyboard.add_hotkey(hotkey_str, secure_callback, suppress=False)
            except:
                pass

    def _mouse_listener(self, event):
        if isinstance(event, mouse.ButtonEvent) and event.event_type == 'down':
            if not self.is_active_func():
                return
            
            btn = str(event.button).lower()
            if btn == 'x': btn = 'mb4'
            if btn == 'x2': btn = 'mb5'
            
            for hk_str, data in self.hotkeys.items():
                parts = data['parts']
                if btn in parts:
                    mods = [p for p in parts if p in ['ctrl', 'alt', 'shift']]
                    if all(keyboard.is_pressed(m) for m in mods):
                        data['callback']()
                        for m in mods:
                            keyboard.release(m)

    def clear(self):
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError: pass
        except Exception: pass
        self.hotkeys.clear()