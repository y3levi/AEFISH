"""fishing engine."""
import threading
import time
from typing import Optional, Callable

from src.core.screen_capture import ScreenCapture
from src.core.detector import Detector, DetectionResult
from src.core.controller import Controller, Action
from src.core.mouse_controller import MouseController
from src.app.state import AppState, AppStatus
from src.utils.logger import get_logger
from src.utils.constants import ENGINE_THREAD_NAME, MIN_LOOP_SLEEP_S

logger = get_logger("fishing_engine")


class FishingEngine:
    """Orchestrates capture → detect → decide → mouse."""

    def __init__(self, config_manager, app_state: AppState) -> None:
        self._cfg = config_manager
        self._state = app_state
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_result: Optional[DetectionResult] = None
        self._last_action: Action = Action.WAIT
        self._debug_callback: Optional[Callable[[DetectionResult], None]] = None
        self._fps_interval: float = 1.0 / 60.0
        self._capture: Optional[ScreenCapture] = None
        self._detector: Optional[Detector] = None
        self._controller: Optional[Controller] = None
        self._mouse: Optional[MouseController] = None
        self._phase = "IDLE"

    def set_debug_callback(self, callback: Optional[Callable[[DetectionResult], None]]) -> None:
        self._debug_callback = callback

    def start(self) -> bool:
        if self.is_running():
            logger.warning("already running")
            return False

        simple_rod = bool(self._cfg.get("capture", "simple_rod_mode", default=False))
        water_pos = self._cfg.get("capture", "water_click_position")

        if simple_rod:
            # autorod: no bar region needed
            if not water_pos:
                logger.warning("autorod: no water pos")
                self._state.set_status(AppStatus.ERROR, "Set water position first")
                return False
            self._mouse = MouseController()
            self._stop_event.clear()
            self._phase = "IDLE"
            self._thread = threading.Thread(
                target=self._loop_autorod,
                name=ENGINE_THREAD_NAME,
                daemon=True,
            )
            self._thread.start()
            logger.info("autorod started")
            return True

        region = self._cfg.get_region()
        if region is None:
            logger.warning("no region calibrated")
            self._state.set_status(AppStatus.ERROR, "No calibrated region")
            return False

        fps = self._cfg.get("capture", "fps", default=60)
        monitor = self._cfg.get("capture", "monitor", default=1)
        self._fps_interval = 1.0 / max(1, fps)

        self._capture = ScreenCapture(monitor)
        self._capture.set_region(region)

        profile = self._cfg.get_profile()
        self._detector = Detector(profile)

        config_dict = self._cfg._config
        profile_ctrl = profile.get("controller", {})
        self._controller = Controller(config_dict)
        self._controller.update_config(config_dict, profile_ctrl)

        self._mouse = MouseController()

        self._stop_event.clear()
        self._phase = "IDLE"
        self._thread = threading.Thread(
            target=self._loop,
            name=ENGINE_THREAD_NAME,
            daemon=True,
        )
        self._thread.start()
        logger.info("engine started")
        return True

    def stop(self) -> None:
        if not self.is_running():
            return
        logger.info("stopping engine")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        self._cleanup()
        self._phase = "IDLE"
        self._state.set_status(AppStatus.IDLE)

    def emergency_stop(self) -> None:
        logger.warning("emergency stop")
        self._stop_event.set()
        if self._mouse:
            self._mouse.emergency_release()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._cleanup()
        self._phase = "IDLE"
        self._state.set_status(AppStatus.IDLE)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def get_last_result(self) -> Optional[DetectionResult]:
        return self._last_result

    @property
    def last_action(self) -> Action:
        return self._last_action

    @property
    def mouse_is_pressed(self) -> bool:
        if self._mouse:
            return self._mouse.is_pressed
        return False

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def prediction_target(self) -> Optional[int]:
        if self._controller:
            return self._controller.prediction_target
        return None

    def _focus_roblox(self) -> bool:
        """focus roblox window."""
        try:
            import ctypes
            hwnd_target = None
            
            def enum_windows_cb(hwnd, lParam):
                nonlocal hwnd_target
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    if "Roblox" in buf.value and ctypes.windll.user32.IsWindowVisible(hwnd):
                        hwnd_target = hwnd
                        return False
                return True

            cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            ctypes.windll.user32.EnumWindows(cb_type(enum_windows_cb), 0)
            
            if hwnd_target:
                fg = ctypes.windll.user32.GetForegroundWindow()
                if hwnd_target != fg:
                    logger.info("focusing roblox window")
                    ctypes.windll.user32.SetForegroundWindow(hwnd_target)
                    time.sleep(0.2)
                    return True
                else:
                    logger.info("roblox already focused")
            else:
                logger.warning("roblox window absent")
        except Exception as e:
            logger.error(f"focus failed: {e}")
        return False

    def _interruptible_sleep(self, seconds: float) -> None:
        """sleep in small chunks so stop_event can interrupt."""
        end = time.monotonic() + seconds
        while not self._stop_event.is_set():
            remaining = end - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(0.05, remaining))

    def _click_water(self, pos: dict) -> None:
        """cast click at pos."""
        try:
            from pynput.mouse import Controller as _Mouse, Button
            m = _Mouse()
            
            logger.info("casting phase started")
            
            # ensure focused
            focused = self._focus_roblox()
            self._interruptible_sleep(0.3)
            if self._stop_event.is_set():
                return
            
            # move cursor
            m.position = (int(pos["x"]), int(pos["y"]))
            self._interruptible_sleep(0.15)
            
            if focused:
                # it was out of focus, do a quick focus click first
                logger.info("focus click")
                m.press(Button.left)
                time.sleep(0.05)
                m.release(Button.left)
                time.sleep(0.2)
            
            # clean tap click
            m.release(Button.left)
            time.sleep(0.04)
            logger.info("mouse click")
            m.press(Button.left)
            time.sleep(0.08)
            m.release(Button.left)
            time.sleep(0.05)
            
            logger.info("cast completion")
        except Exception as e:
            logger.error(f"cast failed: {e}")

    def _loop_autorod(self) -> None:
        """autorod timing loop — no cv needed."""
        water_pos = self._cfg.get("capture", "water_click_position")
        recast_timeout_s = float(self._cfg.get("capture", "recast_timeout_s", default=20.0))
        cooldown_s = float(self._cfg.get("capture", "recast_cooldown_s", default=1.5))

        try:
            while not self._stop_event.is_set():
                # cast
                self._phase = "CASTING"
                self._state.set_status(AppStatus.CASTING)
                self._click_water(water_pos)
                if self._stop_event.is_set():
                    break

                # wait for bite
                self._phase = "WAITING"
                self._state.set_status(AppStatus.WAITING_FOR_MINIGAME)
                logger.info(f"waiting {recast_timeout_s}s for bite")
                self._interruptible_sleep(recast_timeout_s)
                if self._stop_event.is_set():
                    break

                # hook
                logger.info("autorod: hooking fish")
                self._click_water(water_pos)
                if self._stop_event.is_set():
                    break

                # cooldown
                self._phase = "RECAST"
                self._state.set_status(AppStatus.RECAST)
                self._interruptible_sleep(cooldown_s)

        except Exception as e:
            logger.exception(f"autorod error: {e}")
            self._state.set_status(AppStatus.ERROR, str(e))
        finally:
            if self._mouse:
                self._mouse.emergency_release()
            logger.debug("autorod loop exited")

    def _loop(self) -> None:
        """main fishing loop."""
        water_pos = self._cfg.get("capture", "water_click_position")
        recast_timeout_s = float(self._cfg.get("capture", "recast_timeout_s", default=20.0))
        recast_cooldown_s = float(self._cfg.get("capture", "recast_cooldown_s", default=1.5))
        confidence_threshold = float(self._cfg.get("detection", "confidence_threshold", default=0.6))
        fish_lost_timeout_s = float(self._cfg.get("detection", "fish_lost_timeout_ms", default=1500)) / 1000.0
        lost_grace_s = float(self._cfg.get("detection", "lost_target_timeout_ms", default=500)) / 1000.0
        simple_rod = bool(self._cfg.get("capture", "simple_rod_mode", default=False))

        # starting phase
        self._phase = "CASTING" if water_pos else "DETECTING"
        if not water_pos:
            self._state.set_status(AppStatus.DETECTING)

        cast_time: float = 0.0
        fish_lost_since: Optional[float] = None
        consecutive_detects: int = 0

        try:
            while not self._stop_event.is_set():
                loop_start = time.monotonic()

                if self._phase == "CASTING":
                    self._state.set_status(AppStatus.CASTING)
                    self._click_water(water_pos)
                    cast_time = time.monotonic()
                    consecutive_detects = 0
                    self._phase = "WAITING"
                    self._state.set_status(AppStatus.WAITING_FOR_MINIGAME)
                    self._interruptible_sleep(1.0)
                    continue

                frame = self._capture.capture()
                if frame is None:
                    time.sleep(0.1)
                    continue

                result = self._detector.detect(frame)
                self._last_result = result
                self._state.set_confidence(result.confidence)

                detected = result.confidence >= confidence_threshold

                if self._debug_callback:
                    try:
                        self._debug_callback(result)
                    except Exception:
                        pass

                if self._phase == "WAITING":
                    # minimum cast settling delay
                    if time.monotonic() - cast_time < 1.5:
                        time.sleep(0.05)
                        continue

                    if detected:
                        consecutive_detects += 1
                        if consecutive_detects >= 2:
                            if simple_rod:
                                # bite detected
                                logger.info("bite detected")
                                self._click_water(water_pos)
                                
                                # recast sequence
                                self._state.set_status(AppStatus.RECAST)
                                self._interruptible_sleep(2.0)
                                self._phase = "CASTING"
                            else:
                                self._phase = "FISHING"
                                fish_lost_since = None
                                self._state.set_status(AppStatus.FISHING)
                    else:
                        consecutive_detects = 0
                        if time.monotonic() - cast_time > recast_timeout_s:
                            # recast timeout
                            logger.warning("recast timeout")
                            self._mouse.emergency_release() if self._mouse else None
                            self._state.set_status(AppStatus.RECAST)
                            self._interruptible_sleep(recast_cooldown_s)
                            self._phase = "CASTING"

                elif self._phase == "FISHING":
                    if detected:
                        fish_lost_since = None
                        action = self._controller.update(
                            fish_x=result.fish_x,
                            zone_left=result.zone_left,
                            zone_right=result.zone_right,
                            timestamp=time.monotonic(),
                        )
                        self._last_action = action
                        self._mouse.apply(action)
                    else:
                        now = time.monotonic()
                        if fish_lost_since is None:
                            fish_lost_since = now
                        # grace period: keep the last mouse state through short
                        # detection dropouts (e.g. UI flicker over the bar)
                        if now - fish_lost_since > lost_grace_s:
                            self._mouse.apply(Action.RELEASE)
                        if now - fish_lost_since > fish_lost_timeout_s:
                            logger.info("fishing ended")
                            self._mouse.emergency_release()
                            self._controller.reset()
                            fish_lost_since = None
                            self._state.set_status(AppStatus.RECAST)
                            self._interruptible_sleep(recast_cooldown_s)
                            self._phase = "CASTING" if water_pos else "DETECTING"
                            if not water_pos:
                                self._state.set_status(AppStatus.DETECTING)

                elif self._phase == "DETECTING":
                    if detected:
                        consecutive_detects += 1
                        if consecutive_detects >= 2:
                            self._phase = "FISHING"
                            fish_lost_since = None
                            self._state.set_status(AppStatus.FISHING)
                    else:
                        consecutive_detects = 0

                # normal loop sleep
                elapsed = time.monotonic() - loop_start
                sleep_time = self._fps_interval - elapsed
                if sleep_time > MIN_LOOP_SLEEP_S:
                    time.sleep(sleep_time)
                else:
                    time.sleep(MIN_LOOP_SLEEP_S)

        except Exception as e:
            logger.exception(f"loop error: {e}")
            self._state.set_status(AppStatus.ERROR, str(e))
        finally:
            if self._mouse:
                self._mouse.emergency_release()
            if self._controller:
                self._controller.reset()
            logger.debug("loop exited")

    def _cleanup(self) -> None:
        if self._capture:
            self._capture.release()
            self._capture = None
        if self._mouse:
            self._mouse.emergency_release()
            self._mouse = None
        if self._controller:
            self._controller.reset()
            self._controller = None
        self._detector = None
        self._thread = None
