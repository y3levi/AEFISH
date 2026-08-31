import tkinter as tk
from typing import Optional, Callable
from src.utils.logger import get_logger
from src.utils import localization

logger = get_logger('calibration_overlay')

class CalibrationOverlay:
    def __init__(self, parent_root: tk.Tk, on_complete: Callable[[Optional[dict]], None]) -> None:
        self._parent_root = parent_root
        self._on_complete = on_complete
        self._start_x = 0
        self._start_y = 0
        self._rect_id = None
        self._window: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None

    def show(self) -> None:
        self._window = tk.Toplevel(self._parent_root)
        self._window.attributes('-alpha', 0.35)
        self._window.attributes('-topmost', True)
        self._window.attributes('-fullscreen', True)
        self._window.configure(bg='#0a0a0a')
        self._window.config(cursor="cross")
        
        self._canvas = tk.Canvas(self._window, bg='#0a0a0a', highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)
        
        self._canvas.bind('<ButtonPress-1>', self._on_press)
        self._canvas.bind('<B1-Motion>', self._on_drag)
        self._canvas.bind('<ButtonRelease-1>', self._on_release)
        self._window.bind('<Escape>', self._cancel)
        
        big_text = localization.t("calib.bar.instruction")
        small_text = localization.t("calib.bar.detail")
        esc_text = localization.t("calib.bar.esc")
        
        sw = self._window.winfo_screenwidth()
        self._canvas.create_text(sw // 2, 60, text=big_text,
            fill='white', font=('Segoe UI', 18, 'bold'), justify='center')
        self._canvas.create_text(sw // 2, 100, text=small_text,
            fill='#94a3b8', font=('Segoe UI', 13), justify='center')
        self._canvas.create_text(sw // 2, 130, text=esc_text,
            fill='#6b7280', font=('Segoe UI', 11), justify='center')

    def _on_press(self, event) -> None:
        self._start_x = event.x_root
        self._start_y = event.y_root
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        self._rect_id = self._canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline='white', dash=(4, 4), width=2
        )

    def _on_drag(self, event) -> None:
        if self._rect_id:
            self._canvas.coords(self._rect_id, self._start_x, self._start_y, event.x_root, event.y_root)

    def _on_release(self, event) -> None:
        end_x = event.x_root
        end_y = event.y_root
        
        x1 = min(self._start_x, end_x)
        y1 = min(self._start_y, end_y)
        x2 = max(self._start_x, end_x)
        y2 = max(self._start_y, end_y)
        
        width = x2 - x1
        height = y2 - y1
        
        if width > 10 and height > 10:
            region = {'x': x1, 'y': y1, 'width': width, 'height': height}
            # flash confirmation rect
            self._canvas.itemconfig(self._rect_id, outline='#22c55e', dash=())
            self._window.after(300, lambda: self._finish(region))
        else:
            self._cancel()

    def _cancel(self, event=None) -> None:
        logger.info("calibration cancelled")
        if self._window:
            self._window.destroy()
        self._on_complete(None)

    def _finish(self, region: dict) -> None:
        logger.info(f"calibration finished: {region}")
        if self._window:
            self._window.destroy()
        self._on_complete(region)

class WaterCalibrationOverlay:
    def __init__(self, parent_root, on_complete: Callable[[Optional[dict]], None]) -> None:
        self._parent_root = parent_root
        self._on_complete = on_complete
        self._window: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None

    def show(self) -> None:
        self._window = tk.Toplevel(self._parent_root)
        self._window.attributes('-alpha', 0.4)
        self._window.attributes('-topmost', True)
        self._window.attributes('-fullscreen', True)
        self._window.configure(bg='#0a0a0a')
        self._window.config(cursor='crosshair')

        self._canvas = tk.Canvas(self._window, bg='#0a0a0a', highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)

        sw = self._window.winfo_screenwidth()
        self._canvas.create_text(sw // 2, 60, text=localization.t("calib.water.instruction"),
            fill='white', font=('Segoe UI', 18, 'bold'), justify='center')
        self._canvas.create_text(sw // 2, 100, text=localization.t("calib.water.detail"),
            fill='#94a3b8', font=('Segoe UI', 13), justify='center')
        self._canvas.create_text(sw // 2, 130, text=localization.t("calib.water.esc"),
            fill='#6b7280', font=('Segoe UI', 11), justify='center')

        self._canvas.bind('<ButtonPress-1>', self._on_click)
        self._window.bind('<Escape>', self._cancel)

    def _on_click(self, event) -> None:
        pos = {'x': event.x_root, 'y': event.y_root}
        # flash confirmation dot
        dot = self._canvas.create_oval(
            event.x - 12, event.y - 12, event.x + 12, event.y + 12,
            fill='#22c55e', outline='white', width=2
        )
        self._window.after(300, lambda: self._finish(pos))

    def _cancel(self, event=None) -> None:
        if self._window:
            self._window.destroy()
        self._on_complete(None)

    def _finish(self, pos: dict) -> None:
        if self._window:
            self._window.destroy()
        self._on_complete(pos)
