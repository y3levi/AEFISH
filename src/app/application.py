import sys
import os
import atexit
import threading
import time
from typing import Optional

from src.config.config_manager import ConfigManager
from src.app.state import AppState, AppStatus
from src.core.fishing_engine import FishingEngine
from src.core.calibration import CalibrationManager
from src.ui.main_window import MainWindow
from src.ui.settings_window import SettingsWindow
from src.ui.calibration_overlay import CalibrationOverlay, WaterCalibrationOverlay
from src.ui.debug_window import DebugWindow
from src.utils.logger import get_logger, setup_logging
from src.utils.constants import APP_NAME, APP_VERSION, HOTKEY_DEBOUNCE_S
from src.utils import localization as _loc

logger = get_logger('application')

class Application:
    def __init__(self) -> None:
        self._config = ConfigManager('config.json')
        
        lang = self._config.get("ui", "language", default="en")
        _loc.load(lang)
        
        save_logs = self._config.get('debug', 'save_logs', default=False)
        setup_logging(save_logs=save_logs)
        
        self._state = AppState()
        self._calibration = CalibrationManager(self._config)
        self._engine = FishingEngine(self._config, self._state)
        self._debug_window = DebugWindow()
        
        region = self._calibration.get_region()
        if region:
            self._state.set_region(region)
            
        self._window = MainWindow(
            app_state=self._state,
            config_manager=self._config,
            on_start=self._start_fishing,
            on_stop=self._stop_fishing,
            on_emergency_stop=self._emergency_stop,
            on_open_settings=self._open_settings,
            on_calibrate_bar=self._start_bar_calibration,
            on_calibrate_water=self._start_water_calibration,
        )
        
        always_on_top = self._config.get("ui", "always_on_top", default=False)
        if always_on_top:
            self._window.after(100, lambda: self._window.wm_attributes("-topmost", True))
            
        self._window.after(200, lambda: self._window.iconbitmap(os.path.join('assets', 'Toki1ICO.ico')))
            
        water_pos = self._calibration.get_water_position()
        if water_pos:
            self._window.after(50, lambda: self._window.update_water_status(water_pos))
        
        self._state.add_callback('status', self._on_state_status)
        self._state.add_callback('confidence', self._on_state_confidence)
        self._state.add_callback('region', self._on_state_region)
        
        self._hotkey_listener = None
        self._last_toggle_time = 0.0
        self._last_emergency_time = 0.0
        self._setup_hotkeys()
        
        self._window.protocol('WM_DELETE_WINDOW', self.shutdown)
        atexit.register(self.shutdown)

    def run(self) -> None:
        """start ctk mainloop."""
        logger.info(f'starting {APP_NAME} v{APP_VERSION}')
        try:
            self._window.mainloop()
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """clean shutdown."""
        logger.info('shutting down')
        self._engine.emergency_stop()
        self._stop_hotkeys()
        self._debug_window.stop()
        logger.info('shutdown complete')
        if hasattr(self, '_window') and self._window.winfo_exists():
            self._window.destroy()

    def _toggle_fishing(self) -> None:
        if self._engine.is_running():
            self._stop_fishing()
        else:
            self._start_fishing()

    def _start_fishing(self) -> None:
        simple_rod = self._config.get('capture', 'simple_rod_mode', default=False)
        if not simple_rod and not self._calibration.is_calibrated():
            self._state.set_status(AppStatus.ERROR, 'calibrate bar first')
            return
        success = self._engine.start()
        if success:
            if self._config.get('debug', 'enabled', default=False):
                self._debug_window.start()
                self._engine.set_debug_callback(self._on_debug_frame)
            else:
                self._engine.set_debug_callback(None)

    def _stop_fishing(self) -> None:
        # run in background
        def _do_stop():
            self._engine.stop()
            self._debug_window.stop()
            self._engine.set_debug_callback(None)
        threading.Thread(target=_do_stop, daemon=True).start()

    def _emergency_stop(self) -> None:
        logger.warning('emergency stop')
        # run in background
        def _do_emergency():
            self._engine.emergency_stop()
            self._debug_window.stop()
            self._engine.set_debug_callback(None)
        threading.Thread(target=_do_emergency, daemon=True).start()

    def _on_debug_frame(self, result) -> None:
        action = self._engine.last_action
        action_str = action.value if action else "WAIT"
        mouse_str = "DOWN" if self._engine.mouse_is_pressed else "UP"
        self._debug_window.update(result, action_str, fps=self._current_fps(), mouse_state=mouse_str)

    def _current_fps(self) -> float:
        return float(self._config.get('capture', 'fps', default=60))

    def _open_settings(self) -> None:
        was_running = self._engine.is_running()
        if was_running:
            self._stop_fishing()
        SettingsWindow(
            parent=self._window,
            config_manager=self._config,
            on_save=self._on_settings_saved,
            on_calibrate_bar=self._start_bar_calibration,
            on_calibrate_water=self._start_water_calibration,
            on_test_mouse=self._test_mouse_input,
        )

    def _on_settings_saved(self) -> None:
        logger.info("settings saved")
        self._stop_hotkeys()
        self._setup_hotkeys()
        
        always_on_top = self._config.get("ui", "always_on_top", default=False)
        self._window.wm_attributes("-topmost", always_on_top)
        
        lang = self._config.get("ui", "language", default="en")
        if _loc.current_lang() != lang:
            _loc.load(lang)
            self._window.after(0, self._window.refresh_i18n)
        
        toggle_key = self._config.get("hotkeys", "toggle", default="f6").upper()
        emergency_key = self._config.get("hotkeys", "emergency_stop", default="f7").upper()
        if hasattr(self._window, "hotkey_toggle_lbl"):
            self._window.hotkey_toggle_lbl.configure(
                text=f"{_loc.t('hotkey.toggle')}  {toggle_key}"
            )
        if hasattr(self._window, "hotkey_emerg_lbl"):
            self._window.hotkey_emerg_lbl.configure(
                text=f"{_loc.t('hotkey.emergency')}  {emergency_key}"
            )

    def _test_mouse_input(self) -> None:
        """diagnostic click test."""
        def _run():
            try:
                from pynput.mouse import Controller as _Mouse, Button
                m = _Mouse()
                m.press(Button.left)
                time.sleep(0.3)
                m.release(Button.left)
            except Exception as e:
                logger.error(f"mouse test failed: {e}")
        threading.Thread(target=_run, daemon=True).start()

    def _start_bar_calibration(self) -> None:
        self._state.set_status(AppStatus.CALIBRATING)
        overlay = CalibrationOverlay(
            parent_root=self._window,
            on_complete=self._on_bar_calibration_complete,
        )
        self._window.after(50, overlay.show)

    def _on_bar_calibration_complete(self, region: Optional[dict]) -> None:
        if region:
            self._calibration.save_region(region)
            self._state.set_region(region)
            logger.info(f"bar calibrated: {region}")
        self._state.set_status(AppStatus.IDLE)

    def _start_water_calibration(self) -> None:
        self._state.set_status(AppStatus.CALIBRATING)
        overlay = WaterCalibrationOverlay(
            parent_root=self._window,
            on_complete=self._on_water_calibration_complete,
        )
        self._window.after(50, overlay.show)

    def _on_water_calibration_complete(self, pos: Optional[dict]) -> None:
        if pos:
            self._calibration.save_water_position(pos)
            logger.info(f"water position: {pos}")
            self._window.after(0, lambda: self._window.update_water_status(pos))
        self._state.set_status(AppStatus.IDLE)

    def _setup_hotkeys(self) -> None:
        from pynput import keyboard
        toggle_key = self._config.get('hotkeys', 'toggle', default='f6').lower()
        emergency_key = self._config.get('hotkeys', 'emergency_stop', default='f7').lower()

        self._last_toggle_time = 0.0
        self._last_emergency_time = 0.0

        hotkeys_map = {
            f'<{toggle_key}>': self._hotkey_toggle,
            f'<{emergency_key}>': self._hotkey_emergency,
        }

        try:
            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys_map)
            self._hotkey_listener.start()
            logger.info(f'hotkeys registered')
        except Exception as e:
            logger.error(f'hotkeys failed: {e}')
            self._hotkey_listener = None

    def _stop_hotkeys(self) -> None:
        if hasattr(self, '_hotkey_listener') and self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None

    def _hotkey_toggle(self) -> None:
        now = time.monotonic()
        if now - self._last_toggle_time < HOTKEY_DEBOUNCE_S:
            return
        self._last_toggle_time = now
        self._window.after(0, self._toggle_fishing)

    def _hotkey_emergency(self) -> None:
        now = time.monotonic()
        if now - self._last_emergency_time < HOTKEY_DEBOUNCE_S:
            return
        self._last_emergency_time = now
        self._emergency_stop()

    def _on_state_status(self, status, text: str) -> None:
        if hasattr(self, '_window') and self._window.winfo_exists():
            self._window.after(0, lambda: self._window.update_status(status, text))
            try:
                is_fishing_status = (status == AppStatus.FISHING)
            except Exception:
                is_fishing_status = False
            _is_fishing = is_fishing_status
            self._window.after(0, lambda f=_is_fishing: self._window.set_fishing_mode(f))

    def _on_state_confidence(self, value: float) -> None:
        if hasattr(self, '_window') and self._window.winfo_exists():
            self._window.after(0, lambda: self._window.update_confidence(value))

    def _on_state_region(self, region) -> None:
        if hasattr(self, '_window') and self._window.winfo_exists():
            self._window.after(0, lambda: self._window.update_calibration_status(region))
