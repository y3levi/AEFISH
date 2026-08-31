import customtkinter as ctk
from typing import Callable, Optional
from src.config.config_manager import ConfigManager
from src.utils.logger import get_logger
from src.utils import localization
from src.ui import design_system as ds

logger = get_logger('settings_window')

class SettingsWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        on_save: Callable = None,
        on_calibrate_bar: Callable = None,
        on_calibrate_water: Callable = None,
        on_test_mouse: Callable = None,
    ) -> None:
        super().__init__(parent)
        self.title(localization.t("settings.title"))
        self.geometry('480x620')
        self.resizable(False, False)
        
        self.configure(fg_color=ds.BG_MAIN)
        self._config_manager = config_manager
        self._on_save = on_save
        self._on_calibrate_bar = on_calibrate_bar
        self._on_calibrate_water = on_calibrate_water
        self._on_test_mouse = on_test_mouse
        
        self.after(200, lambda: self.iconbitmap(ds.ICON_SETTINGS))
        
        self._labels = []
        self._lang_map = {"English": "en", "Português": "pt_BR"}
        self._inv_lang_map = {"en": "English", "pt_BR": "Português"}
        
        self.grab_set()
        
        self._build_ui()
        self._load_values()
        localization.on_language_change(self._refresh_text)

    def _build_ui(self) -> None:
        self.tabview = ctk.CTkTabview(self, fg_color=ds.SURFACE, segmented_button_selected_color=ds.ACCENT, 
                                      segmented_button_selected_hover_color=ds.HOVER,
                                      segmented_button_unselected_color=ds.BG_SUB,
                                      segmented_button_unselected_hover_color=ds.SURFACE2,
                                      segmented_button_fg_color=ds.BG_MAIN,
                                      text_color=ds.TEXT_PRI)
        self.tabview.pack(fill='both', expand=True, padx=20, pady=(20, 10))
        
        self.tab_basic = self.tabview.add("Basic")
        self.tab_adv = self.tabview.add("Advanced")
        
        self._build_basic_tab()
        self._build_adv_tab()
        
        self.btn_frame = ctk.CTkFrame(self, fg_color=ds.BG_MAIN)
        self.btn_frame.pack(fill='x', padx=20, pady=(10, 20))
        
        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel", 
                                        fg_color='transparent', border_width=1, 
                                        border_color=ds.BORDER, text_color=ds.TEXT_SEC, 
                                        hover_color=ds.BG_SUB,
                                        command=self.destroy)
        self.cancel_btn.pack(side='left', expand=True, padx=5)
        
        self.save_btn = ctk.CTkButton(self.btn_frame, text="Save", 
                                      fg_color=ds.ACCENT, text_color=ds.FROST, 
                                      hover_color=ds.HOVER,
                                      command=self._save_values)
        self.save_btn.pack(side='right', expand=True, padx=5)

    def _build_basic_tab(self) -> None:
        scroll = ctk.CTkScrollableFrame(self.tab_basic, fg_color="transparent")
        scroll.pack(fill='both', expand=True)
        
        self._add_header(scroll, "settings.section.general")
        self.lang_combo = self._add_combo(scroll, "settings.general.language", ["English", "Português"])
        self.ontop_switch = self._add_switch(scroll, "settings.general.always_on_top")
        
        self._add_header(scroll, "settings.section.fishing")
        self.calib_bar_btn = ctk.CTkButton(scroll, text="", fg_color="transparent", 
                                           border_width=1, border_color=ds.BORDER, 
                                           text_color=ds.TEXT_SEC, hover_color=ds.BG_SUB,
                                           command=self._do_calib_bar)
        self.calib_bar_btn.pack(fill='x', pady=5)
        
        self.calib_water_btn = ctk.CTkButton(scroll, text="", fg_color="transparent", 
                                             border_width=1, border_color=ds.BORDER, 
                                             text_color=ds.TEXT_SEC, hover_color=ds.BG_SUB,
                                             command=self._do_calib_water)
        self.calib_water_btn.pack(fill='x', pady=5)
        
        self.recast_entry, _ = self._add_entry_desc(scroll, "settings.fishing.recast_timeout", "settings.fishing.recast_timeout_desc")
        self.simple_rod_switch, _ = self._add_switch_desc(scroll, "settings.fishing.simple_rod", "settings.fishing.simple_rod_desc")
        
        self._add_header(scroll, "settings.section.hotkeys")
        self.start_hotkey = self._add_entry(scroll, "settings.hotkeys.toggle")
        self.emerg_hotkey = self._add_entry(scroll, "settings.hotkeys.emergency")
        
        self._add_header(scroll, "settings.section.debug")
        self.debug_switch = self._add_switch(scroll, "settings.debug.enable")
        
        self.disclaimer_lbl = ctk.CTkLabel(scroll, text="", text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 10, "italic"))
        self.disclaimer_lbl.pack(pady=(20, 5))
        self._labels.append((self.disclaimer_lbl, "settings.basic.disclaimer"))

    def _build_adv_tab(self) -> None:
        scroll = ctk.CTkScrollableFrame(self.tab_adv, fg_color="transparent")
        scroll.pack(fill='both', expand=True)
        
        self.adv_warn_lbl = ctk.CTkLabel(scroll, text="", text_color=ds.WARNING, font=(ds.FONT_MAIN, 12, 'bold'))
        self.adv_warn_lbl.pack(pady=5)
        self._labels.append((self.adv_warn_lbl, "settings.advanced_warning"))
        
        self._add_header(scroll, "settings.section.detection")
        self.fps_entry, _ = self._add_entry_desc(scroll, "settings.detection.fps", "settings.detection.fps_desc")
        self.conf_slider, _ = self._add_slider_desc(scroll, "settings.detection.confidence", "settings.detection.confidence_desc", 0.1, 1.0, 18, 0.6)
        self.lost_targ_entry, _ = self._add_entry_desc(scroll, "settings.detection.lost_timeout", "settings.detection.lost_timeout_desc")
        self.fish_lost_entry, _ = self._add_entry_desc(scroll, "settings.detection.fish_lost_timeout", "settings.detection.fish_lost_timeout_desc")
        
        self._add_header(scroll, "settings.section.controller")
        self.deadzone_entry, _ = self._add_entry_desc(scroll, "settings.controller.deadzone", "settings.controller.deadzone_desc")
        self.pred_switch, _ = self._add_switch_desc(scroll, "settings.controller.prediction", "settings.controller.prediction_desc")
        self.smooth_slider, _ = self._add_slider_desc(scroll, "settings.controller.smoothing", "settings.controller.smoothing_desc", 0.0, 1.0, 20, 0.9)
        
        self._add_header(scroll, "settings.section.adv_debug")
        self.masks_switch, _ = self._add_switch_desc(scroll, "settings.adv_debug.show_masks", "settings.adv_debug.show_masks_desc")
        
        self._add_header(scroll, "settings.section.diagnostics")
        self.diag_desc = ctk.CTkLabel(scroll, text="", text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        self.diag_desc.pack(anchor='w')
        self._labels.append((self.diag_desc, "settings.diagnostics.test_mouse_desc"))
        
        self.diag_btn = ctk.CTkButton(scroll, text="", fg_color="transparent", 
                                      border_width=1, border_color=ds.BORDER, 
                                      text_color=ds.TEXT_SEC, hover_color=ds.BG_SUB,
                                      command=self._do_test_mouse)
        self.diag_btn.pack(anchor='w', pady=5)
        self.diag_result = ctk.CTkLabel(scroll, text="", text_color=ds.SUCCESS)
        self.diag_result.pack(anchor='w')

    def _add_header(self, parent, loc_key) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=(15, 5))
        
        lbl = ctk.CTkLabel(frame, text="", text_color=ds.ACCENT_LT, font=(ds.FONT_MAIN, 12, 'bold'))
        lbl.pack(anchor='w')
        
        # uppercase dynamic text
        def update_lbl_text(text):
            lbl.configure(text=text.upper())
            
        self._labels.append((lbl, loc_key, update_lbl_text))
        
        line = ctk.CTkFrame(frame, fg_color=ds.BORDER, height=1)
        line.pack(fill='x', pady=(2, 0))

    def _add_combo(self, parent, loc_key, values) -> ctk.CTkComboBox:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=2)
        lbl = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_PRI)
        lbl.pack(side='left')
        self._labels.append((lbl, loc_key))
        combo = ctk.CTkComboBox(frame, values=values, width=120, 
                                fg_color=ds.SURFACE2, border_color=ds.BORDER, 
                                button_color=ds.SURFACE2, button_hover_color=ds.BG_SUB)
        combo.pack(side='right')
        return combo

    def _add_switch(self, parent, loc_key) -> ctk.CTkSwitch:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=2)
        lbl = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_PRI)
        lbl.pack(side='left')
        self._labels.append((lbl, loc_key))
        sw = ctk.CTkSwitch(frame, text="", progress_color=ds.ACCENT)
        sw.pack(side='right')
        return sw

    def _add_switch_desc(self, parent, loc_key, desc_key) -> tuple[ctk.CTkSwitch, ctk.CTkLabel]:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=4)
        
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill='x')
        lbl = ctk.CTkLabel(top, text="", text_color=ds.TEXT_PRI)
        lbl.pack(side='left')
        self._labels.append((lbl, loc_key))
        
        sw = ctk.CTkSwitch(top, text="", progress_color=ds.ACCENT)
        sw.pack(side='right')
        
        desc = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        desc.pack(anchor='w')
        self._labels.append((desc, desc_key))
        return sw, desc

    def _add_entry(self, parent, loc_key) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=2)
        lbl = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_PRI)
        lbl.pack(side='left')
        self._labels.append((lbl, loc_key))
        ent = ctk.CTkEntry(frame, width=120, fg_color=ds.SURFACE2, border_color=ds.BORDER)
        ent.pack(side='right')
        return ent

    def _add_entry_desc(self, parent, loc_key, desc_key) -> tuple[ctk.CTkEntry, ctk.CTkLabel]:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=4)
        
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill='x')
        lbl = ctk.CTkLabel(top, text="", text_color=ds.TEXT_PRI)
        lbl.pack(side='left')
        self._labels.append((lbl, loc_key))
        
        ent = ctk.CTkEntry(top, width=120, fg_color=ds.SURFACE2, border_color=ds.BORDER)
        ent.pack(side='right')
        
        desc = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        desc.pack(anchor='w')
        self._labels.append((desc, desc_key))
        return ent, desc

    def _add_slider_desc(self, parent, loc_key, desc_key, from_, to, steps, default) -> tuple[ctk.CTkSlider, ctk.CTkLabel]:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill='x', pady=4)
        
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill='x')
        
        lbl = ctk.CTkLabel(top, text="", text_color=ds.TEXT_PRI)
        lbl.pack(side='left')
        self._labels.append((lbl, loc_key))
        
        val_lbl = ctk.CTkLabel(top, text=str(default), text_color=ds.TEXT_SEC, width=40)
        val_lbl.pack(side='right')
        
        sl = ctk.CTkSlider(top, from_=from_, to=to, number_of_steps=steps, width=120, progress_color=ds.ACCENT, button_color=ds.ACCENT_LT, button_hover_color=ds.FROST)
        sl.pack(side='right', padx=10)
        sl.set(default)
        
        def update_val(v):
            val_lbl.configure(text=f"{v:.2f}")
        sl.configure(command=update_val)
        
        desc = ctk.CTkLabel(frame, text="", text_color=ds.TEXT_SEC, font=(ds.FONT_MAIN, 11))
        desc.pack(anchor='w')
        self._labels.append((desc, desc_key))
        return sl, desc

    def _refresh_text(self) -> None:
        for item in self._labels:
            if len(item) == 2:
                widget, key = item
                widget.configure(text=localization.t(key))
            else:
                widget, key, func = item
                func(localization.t(key))
            
        self.title(localization.t("settings.title"))
        self.calib_bar_btn.configure(text=localization.t("settings.fishing.calibrate_bar"))
        self.calib_water_btn.configure(text=localization.t("settings.fishing.calibrate_water"))
        self.diag_btn.configure(text=localization.t("settings.diagnostics.test_mouse"))
        self.cancel_btn.configure(text=localization.t("btn.cancel"))
        self.save_btn.configure(text=localization.t("btn.save"))
        
        self.tabview._segmented_button._buttons_dict["Basic"].configure(text=localization.t("settings.tab.basic") if localization.t("settings.tab.basic") != "settings.tab.basic" else "Basic")
        self.tabview._segmented_button._buttons_dict["Advanced"].configure(text=localization.t("settings.tab.advanced") if localization.t("settings.tab.advanced") != "settings.tab.advanced" else "Advanced")

    def _do_calib_bar(self) -> None:
        self._save_config_only()
        self.destroy()
        if self._on_calibrate_bar:
            self._on_calibrate_bar()

    def _do_calib_water(self) -> None:
        self._save_config_only()
        self.destroy()
        if self._on_calibrate_water:
            self._on_calibrate_water()

    def _do_test_mouse(self) -> None:
        if self._on_test_mouse:
            self._on_test_mouse()
            self.diag_result.configure(text="OK")

    def _load_values(self) -> None:
        lang = self._config_manager.get('ui', 'language', default='en')
        self.lang_combo.set(self._inv_lang_map.get(lang, "English"))
        
        if self._config_manager.get('ui', 'always_on_top', default=False):
            self.ontop_switch.select()
        else:
            self.ontop_switch.deselect()
            
        self.recast_entry.insert(0, str(self._config_manager.get('capture', 'recast_timeout_s', default=20.0)))
        if self._config_manager.get('capture', 'simple_rod_mode', default=False): self.simple_rod_switch.select()
        else: self.simple_rod_switch.deselect()
        self.start_hotkey.insert(0, self._config_manager.get('hotkeys', 'toggle', default='f6'))
        self.emerg_hotkey.insert(0, self._config_manager.get('hotkeys', 'emergency_stop', default='f7'))
        
        if self._config_manager.get('debug', 'enabled', default=False): self.debug_switch.select()
        else: self.debug_switch.deselect()
        
        self.fps_entry.insert(0, str(self._config_manager.get('capture', 'fps', default=60)))
        self.conf_slider.set(self._config_manager.get('detection', 'confidence_threshold', default=0.6))
        self.conf_slider._command(self.conf_slider.get())
        self.lost_targ_entry.insert(0, str(self._config_manager.get('detection', 'lost_target_timeout_ms', default=500)))
        self.fish_lost_entry.insert(0, str(self._config_manager.get('detection', 'fish_lost_timeout_ms', default=1200)))
        
        self.deadzone_entry.insert(0, str(self._config_manager.get('detection', 'deadzone', default=10)))
        if self._config_manager.get('controller', 'prediction', default=True): self.pred_switch.select()
        else: self.pred_switch.deselect()
        
        self.smooth_slider.set(self._config_manager.get('controller', 'smoothing', default=0.9))
        self.smooth_slider._command(self.smooth_slider.get())
        
        if self._config_manager.get('debug', 'show_masks', default=False): self.masks_switch.select()
        else: self.masks_switch.deselect()
        
        self._refresh_text()

    def _save_config_only(self) -> None:
        self._config_manager.set('ui', 'language', value=self._lang_map.get(self.lang_combo.get(), 'en'))
        self._config_manager.set('ui', 'always_on_top', value=bool(self.ontop_switch.get()))
        
        try: self._config_manager.set('capture', 'recast_timeout_s', value=float(self.recast_entry.get()))
        except ValueError: pass
        
        self._config_manager.set('capture', 'simple_rod_mode', value=bool(self.simple_rod_switch.get()))
        self._config_manager.set('hotkeys', 'toggle', value=self.start_hotkey.get())
        self._config_manager.set('hotkeys', 'emergency_stop', value=self.emerg_hotkey.get())
        self._config_manager.set('debug', 'enabled', value=bool(self.debug_switch.get()))
        
        try: self._config_manager.set('capture', 'fps', value=int(self.fps_entry.get()))
        except ValueError: pass
        
        self._config_manager.set('detection', 'confidence_threshold', value=float(self.conf_slider.get()))
        
        try: self._config_manager.set('detection', 'lost_target_timeout_ms', value=int(self.lost_targ_entry.get()))
        except ValueError: pass
        
        try: self._config_manager.set('detection', 'fish_lost_timeout_ms', value=int(self.fish_lost_entry.get()))
        except ValueError: pass
        
        try: self._config_manager.set('detection', 'deadzone', value=int(self.deadzone_entry.get()))
        except ValueError: pass
        
        self._config_manager.set('controller', 'prediction', value=bool(self.pred_switch.get()))
        self._config_manager.set('controller', 'smoothing', value=float(self.smooth_slider.get()))
        self._config_manager.set('debug', 'show_masks', value=bool(self.masks_switch.get()))
        
        self._config_manager.save()

    def _save_values(self) -> None:
        self._save_config_only()
        if self._on_save:
            self._on_save()
        self.destroy()
