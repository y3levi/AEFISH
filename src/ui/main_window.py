import customtkinter as ctk
from typing import Callable, Optional
from src.app.state import AppState, AppStatus
from src.config.config_manager import ConfigManager
from src.utils import localization
from src.ui import design_system as ds

STATUS_COLORS = {
    AppStatus.IDLE: '#3d5a64',
    AppStatus.WAITING_FOR_GAME: ds.WARNING,
    AppStatus.CALIBRATING: '#7a8fbf',
    AppStatus.CASTING: ds.ACCENT,
    AppStatus.WAITING_FOR_MINIGAME: ds.ACCENT,
    AppStatus.DETECTING: ds.ACCENT_LT,
    AppStatus.FISHING: ds.SUCCESS,
    AppStatus.RECAST: ds.WARNING,
    AppStatus.PAUSED: ds.WARNING,
    AppStatus.ERROR: ds.ERROR,
}

class MainWindow(ctk.CTk):
    def __init__(self, 
                 app_state: AppState,
                 config_manager: ConfigManager,
                 on_start: Callable,
                 on_stop: Callable,
                 on_emergency_stop: Callable,
                 on_open_settings: Callable,
                 on_calibrate_bar: Callable,
                 on_calibrate_water: Callable) -> None:
        super().__init__()
        
        self.title('AE Auto Fishing')
        self.geometry('320x510')
        self.resizable(False, False)
        self.configure(fg_color=ds.BG_MAIN)
        
        self._app_state = app_state
        self._config_manager = config_manager
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_emergency_stop = on_emergency_stop
        self._on_open_settings = on_open_settings
        self._on_calibrate_bar = on_calibrate_bar
        self._on_calibrate_water = on_calibrate_water
        
        self._water_pos: Optional[dict] = None
        
        self._build_ui()
        localization.on_language_change(self.refresh_i18n)
        
        self._app_state.add_callback('status', lambda s, t: self.after(0, lambda: self.update_status(s, t)))
        self._app_state.add_callback('confidence', lambda v: self.after(0, lambda: self.update_confidence(v)))
        self._app_state.add_callback('region', lambda r: self.after(0, lambda: self.update_calibration_status(r)))

    def _build_ui(self) -> None:
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill='x', pady=(20, 0))
        
        brand_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        brand_frame.pack(fill='x', pady=(0, 15), padx=20)
        
        lbl_brand = ctk.CTkLabel(brand_frame, text="A N I M E   E X P E D I T I O N S", 
                                 text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 10))
        lbl_brand.pack()
        
        lbl_title = ctk.CTkLabel(brand_frame, text="auto fishing", 
                                 text_color=ds.FROST, font=(ds.FONT_MAIN, 22, "bold"))
        lbl_title.pack()
        
        lbl_author = ctk.CTkLabel(brand_frame, text="by y3levi", 
                                  text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 10, "italic"))
        lbl_author.pack()

        self.status_frame = ctk.CTkFrame(self.content_frame, fg_color=ds.SURFACE, 
                                         border_color=ds.BORDER, border_width=1, 
                                         corner_radius=18, height=36)
        self.status_frame.pack(fill='x', pady=(0, 15), padx=20)
        self.status_frame.pack_propagate(False)
        
        self.status_canvas = ctk.CTkCanvas(self.status_frame, width=12, height=12, 
                                           bg=ds.SURFACE, highlightthickness=0)
        self.status_canvas.pack(side='left', padx=(12, 8), pady=12)
        self.status_dot = self.status_canvas.create_oval(1, 1, 11, 11, 
                                                         fill=STATUS_COLORS[AppStatus.IDLE], outline='')
        
        self.status_label = ctk.CTkLabel(self.status_frame, text=localization.t("status.idle"), 
                                         text_color=ds.TEXT_PRI, font=(ds.FONT_MAIN, 12))
        self.status_label.pack(side='left', pady=0)
        
        self.main_btn = ctk.CTkButton(self.content_frame, text=localization.t("btn.start"),
                                      fg_color=ds.ACCENT, hover_color=ds.HOVER,
                                      text_color=ds.FROST, font=(ds.FONT_MAIN, 15, "bold"),
                                      height=52, corner_radius=8,
                                      command=self._on_main_btn_click)
        self.main_btn.pack(fill='x', pady=(0, 15), padx=20)
        
        tk_str = f"{localization.t('hotkey.toggle')}  {self._config_manager.get('hotkeys', 'toggle', default='F6').upper()}"
        ek_str = f"{localization.t('hotkey.emergency')}  {self._config_manager.get('hotkeys', 'emergency_stop', default='F7').upper()}"
        self.hotkey_toggle_lbl = ctk.CTkLabel(self.content_frame, text=tk_str, 
                                              text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        self.hotkey_toggle_lbl.pack(padx=20)
        self.hotkey_emerg_lbl = ctk.CTkLabel(self.content_frame, text=ek_str, 
                                             text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        self.hotkey_emerg_lbl.pack(pady=(0, 15), padx=20)
        
        det_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        det_frame.pack(fill='x', pady=(0, 15), padx=20)
        
        self.det_label = ctk.CTkLabel(det_frame, text=localization.t("label.detection"), 
                                      text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        self.det_label.pack(anchor='w')
        
        bar_frame = ctk.CTkFrame(det_frame, fg_color="transparent")
        bar_frame.pack(fill='x')
        
        self.conf_bar = ctk.CTkProgressBar(bar_frame, progress_color=ds.ACCENT, 
                                           fg_color=ds.BG_SUB, height=6)
        self.conf_bar.pack(side='left', fill='x', expand=True, pady=5)
        self.conf_bar.set(0)
        
        self.conf_label = ctk.CTkLabel(bar_frame, text='0%', text_color=ds.TEXT_PRI, 
                                       font=(ds.FONT_MAIN, 11), width=35, anchor='e')
        self.conf_label.pack(side='right')

        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill='x', pady=(0, 15), padx=20)
        
        self.settings_btn = ctk.CTkButton(btn_frame, text=localization.t("btn.settings"), 
                                          fg_color='transparent', hover_color=ds.BG_SUB,
                                          border_width=1, border_color=ds.BORDER,
                                          text_color=ds.TEXT_SEC, corner_radius=8,
                                          command=self._on_open_settings)
        self.settings_btn.pack(side='left', expand=True, padx=(0, 2))
        
        self.calib_bar_btn = ctk.CTkButton(btn_frame, text=localization.t("btn.calibrate_bar"), 
                                           fg_color='transparent', hover_color=ds.BG_SUB,
                                           border_width=1, border_color=ds.BORDER,
                                           text_color=ds.TEXT_SEC, corner_radius=8,
                                           command=self._on_calibrate_bar)
        self.calib_bar_btn.pack(side='left', expand=True, padx=(2, 2))
        
        self.calib_water_btn = ctk.CTkButton(btn_frame, text=localization.t("btn.calibrate_water"), 
                                             fg_color='transparent', hover_color=ds.BG_SUB,
                                             border_width=1, border_color=ds.BORDER,
                                             text_color=ds.TEXT_SEC, corner_radius=8,
                                             command=self._on_calibrate_water)
        self.calib_water_btn.pack(side='left', expand=True, padx=(2, 0))
        
        calib_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        calib_frame.pack(fill='x', padx=20)
        
        self.calib_status_lbl = ctk.CTkLabel(calib_frame, text=localization.t("label.region_none"), 
                                             text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        self.calib_status_lbl.pack()
        
        self.water_status_lbl = ctk.CTkLabel(calib_frame, text=localization.t("label.water_none"), 
                                             text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        self.water_status_lbl.pack()

    def _on_main_btn_click(self) -> None:
        if self._app_state.is_fishing:
            self._on_stop()
        else:
            self._on_start()

    def update_status(self, status: AppStatus, text: str) -> None:
        color = STATUS_COLORS.get(status, STATUS_COLORS[AppStatus.IDLE])
        self.status_canvas.itemconfig(self.status_dot, fill=color)
        locale_key = f"status.{status.value}"
        display = localization.t(locale_key)
        self.status_label.configure(text=display if display != locale_key else text)
        
    def update_confidence(self, value: float) -> None:
        self.conf_bar.set(value)
        self.conf_label.configure(text=f"{int(value*100)}%")
        
    def update_calibration_status(self, region: Optional[dict]) -> None:
        if region:
            text = localization.t("label.region_set", width=region['width'], height=region['height'])
        else:
            text = localization.t("label.region_none")
        self.calib_status_lbl.configure(text=text)
        
    def update_water_status(self, pos: Optional[dict]) -> None:
        self._water_pos = pos
        if pos:
            text = localization.t("label.water_set", x=pos['x'], y=pos['y'])
        else:
            text = localization.t("label.water_none")
        self.water_status_lbl.configure(text=text)

    def set_fishing_mode(self, is_fishing: bool) -> None:
        if is_fishing:
            self.main_btn.configure(text=localization.t("btn.stop"), fg_color=ds.SURFACE2)
        else:
            self.main_btn.configure(text=localization.t("btn.start"), fg_color=ds.ACCENT)

    def show_error(self, message: str) -> None:
        self.update_status(AppStatus.ERROR, message)
        
    def refresh_i18n(self) -> None:
        self.update_status(self._app_state.status, self._app_state.status_text)
        self.update_calibration_status(self._app_state.region)
        self.update_water_status(self._water_pos)
        
        self.hotkey_toggle_lbl.configure(text=f"{localization.t('hotkey.toggle')}  {self._config_manager.get('hotkeys', 'toggle', default='F6').upper()}")
        self.hotkey_emerg_lbl.configure(text=f"{localization.t('hotkey.emergency')}  {self._config_manager.get('hotkeys', 'emergency_stop', default='F7').upper()}")
        
        self.det_label.configure(text=localization.t("label.detection"))
        self.settings_btn.configure(text=localization.t("btn.settings"))
        self.calib_bar_btn.configure(text=localization.t("btn.calibrate_bar"))
        self.calib_water_btn.configure(text=localization.t("btn.calibrate_water"))
        self.set_fishing_mode(self._app_state.is_fishing)
