import sys, json, os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, 
    QLabel, QHBoxLayout, QComboBox, QLineEdit
)
from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QIcon

class MetronomeApp(QWidget):
    TONES = {
        "Default": "sfx/Default.wav",
        "Clock": "sfx/Clock.wav",
        "Classic": "sfx/Classic.wav",
        "Digital": "sfx/Digital.wav",
        "Electric": "sfx/Electric.wav",
        "Sonar": "sfx/Sonar.wav"
    }

    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("icon.png"))
        self.set_dark_title_bar()
        
        self.is_playing = False
        self.slots_data = self.load_slots()
        self.current_slot = str(self.slots_data.get("active_slot", "1"))
        
        if self.current_slot not in self.slots_data["slots"]:
            self.current_slot = list(self.slots_data["slots"].keys())[0]
            
        slot_info = self.slots_data["slots"][self.current_slot]
        self.bpm = slot_info["bpm"]
        self.configured_seconds = slot_info["seconds"]
        self.total_seconds = self.configured_seconds
        
        self.beat_timer = QTimer(self)
        self.beat_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.beat_timer.timeout.connect(self.play_tick)
        
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.tick_second)
        
        self.tick_sound = QSoundEffect()

        self.timer_finished = QSoundEffect()
        self.timer_finished.setSource(QUrl.fromLocalFile("sfx/finished.wav"))
        
        self.init_ui()
        self.populate_slots_combo()
        self.apply_slot_data(self.current_slot)

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        self.slot_title_input = QLineEdit()
        self.slot_title_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slot_title_input.setObjectName("slotTitleInput")
        self.slot_title_input.textEdited.connect(self.on_name_edited)
        self.slot_title_input.returnPressed.connect(self.slot_title_input.clearFocus)
        main_layout.addWidget(self.slot_title_input)

        bpm_layout = QHBoxLayout()
        self.btn_dec_bpm_5 = QPushButton("◀◀")
        self.btn_dec_bpm_1 = QPushButton("◀")
        self.bpm_label = QLabel(f"{self.bpm} bpm", alignment=Qt.AlignmentFlag.AlignCenter)
        self.btn_inc_bpm_1 = QPushButton("▶")
        self.btn_inc_bpm_5 = QPushButton("▶▶")
        
        for btn in [self.btn_dec_bpm_5, self.btn_dec_bpm_1, self.btn_inc_bpm_1, self.btn_inc_bpm_5]:
            btn.setFixedSize(50, 50)
            btn.setObjectName("arrowBtn")

        self.bpm_label.setObjectName("bpmLabel")
        
        self.btn_dec_bpm_5.clicked.connect(lambda: self.change_bpm(-5))
        self.btn_dec_bpm_1.clicked.connect(lambda: self.change_bpm(-1))
        self.btn_inc_bpm_1.clicked.connect(lambda: self.change_bpm(1))
        self.btn_inc_bpm_5.clicked.connect(lambda: self.change_bpm(5))
        
        bpm_layout.addWidget(self.btn_dec_bpm_5)
        bpm_layout.addWidget(self.btn_dec_bpm_1)
        bpm_layout.addWidget(self.bpm_label, stretch=1)
        bpm_layout.addWidget(self.btn_inc_bpm_1)
        bpm_layout.addWidget(self.btn_inc_bpm_5)
        main_layout.addLayout(bpm_layout)

        timer_layout = QHBoxLayout()
        self.btn_dec_tim_30 = QPushButton("◀◀")
        self.btn_dec_tim_1 = QPushButton("◀")
        self.timer_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.btn_inc_tim_1 = QPushButton("▶")
        self.btn_inc_tim_30 = QPushButton("▶▶")

        for btn in [self.btn_dec_tim_30, self.btn_dec_tim_1, self.btn_inc_tim_1, self.btn_inc_tim_30]:
            btn.setFixedSize(50, 50)
            btn.setObjectName("arrowBtn")

        self.timer_label.setObjectName("timerLabel")

        self.btn_dec_tim_30.clicked.connect(lambda: self.change_timer(-30))
        self.btn_dec_tim_1.clicked.connect(lambda: self.change_timer(-1))
        self.btn_inc_tim_1.clicked.connect(lambda: self.change_timer(1))
        self.btn_inc_tim_30.clicked.connect(lambda: self.change_timer(30))

        timer_layout.addWidget(self.btn_dec_tim_30)
        timer_layout.addWidget(self.btn_dec_tim_1)
        timer_layout.addWidget(self.timer_label, stretch=1)
        timer_layout.addWidget(self.btn_inc_tim_1)
        timer_layout.addWidget(self.btn_inc_tim_30)
        main_layout.addLayout(timer_layout)

        main_layout.addStretch()

        bottom_layout = QHBoxLayout()

        profile_box = QVBoxLayout()
        profile_box.setSpacing(5)
        
        profile_label = QLabel("Profiles:")
        profile_label.setObjectName("sectionLabel")
        profile_box.addWidget(profile_label)

        profile_controls = QHBoxLayout()
        self.combo_slots = QComboBox()
        self.combo_slots.setMinimumWidth(140)
        self.combo_slots.setFixedHeight(45)
        self.combo_slots.setObjectName("comboSlots")
        self.combo_slots.currentIndexChanged.connect(self.on_combo_changed)
        profile_controls.addWidget(self.combo_slots)

        self.add_slot_btn = QPushButton("+")
        self.add_slot_btn.setFixedSize(45, 45)
        self.add_slot_btn.setObjectName("addBtn")
        self.add_slot_btn.clicked.connect(self.add_new_slot)
        profile_controls.addWidget(self.add_slot_btn)

        self.delete_slot_btn = QPushButton("-")
        self.delete_slot_btn.setFixedSize(45, 45)
        self.delete_slot_btn.setObjectName("deleteBtn")
        self.delete_slot_btn.clicked.connect(self.delete_current_slot)
        profile_controls.addWidget(self.delete_slot_btn)

        profile_box.addLayout(profile_controls)
        bottom_layout.addLayout(profile_box)

        bottom_layout.addSpacing(15)

        sound_box = QVBoxLayout()
        sound_box.setSpacing(5)

        sound_label = QLabel("Sounds:")
        sound_label.setObjectName("sectionLabel")
        sound_box.addWidget(sound_label)

        self.combo_tones = QComboBox()
        self.combo_tones.setMinimumWidth(130)
        self.combo_tones.setFixedHeight(45)
        self.combo_tones.setObjectName("comboTones")
        for tone_name in self.TONES.keys():
            self.combo_tones.addItem(tone_name)
        self.combo_tones.currentTextChanged.connect(self.on_tone_changed)
        sound_box.addWidget(self.combo_tones)

        bottom_layout.addLayout(sound_box)

        bottom_layout.addStretch()

        action_box = QVBoxLayout()
        action_box.setSpacing(5)

        spacer_label = QLabel("")
        action_box.addWidget(spacer_label)

        action_controls = QHBoxLayout()
        self.start_btn = QPushButton("START")
        self.start_btn.setFixedSize(110, 45)
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.toggle_metronome)
        action_controls.addWidget(self.start_btn)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedSize(85, 45)
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_metronome)
        action_controls.addWidget(self.stop_btn)

        action_box.addLayout(action_controls)
        bottom_layout.addLayout(action_box)

        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
        self.setWindowTitle("Minimal Metronome")

        self.setStyleSheet("""
            QWidget {
            background-color: #0f111a;
            color: #e0e6ed;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QLineEdit#slotTitleInput {
            font-size: 20px;
            font-weight: 600;
            color: #ffffff;
            background-color: transparent;
            border: none;
            border-bottom: 2px solid #2a2e45;
            padding: 5px;
        }
        QLineEdit#slotTitleInput:focus {
            border-bottom: 2px solid #00d2ff;
        }

        QLabel#bpmLabel {
            font-size: 42px;
            font-weight: bold;
            color: #ffffff;
        }
        QLabel#timerLabel {
            font-size: 26px;
            font-weight: 500;
            color: #00d2ff;
        }
        QLabel#sectionLabel {
            font-size: 13px;
            font-weight: bold;
            color: #8a99ad;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        QPushButton#arrowBtn {
            background-color: #1a1d2e;
            color: #00d2ff;
            border: 2px solid #2a304d;
            border-radius: 12px;
            font-size: 16px;
        }
        QPushButton#arrowBtn:hover {
            background-color: #252a42;
            border-color: #00d2ff;
        }
        QPushButton#arrowBtn:pressed {
            background-color: #00d2ff;
            color: #0f111a;
        }

        QComboBox#comboSlots, QComboBox#comboTones {
            background-color: #1a1d2e;
            color: #ffffff;
            border: 2px solid #2a304d;
            border-radius: 8px;
            padding: 5px 10px;
            font-size: 15px;
            font-weight: bold;
        }
        QComboBox#comboSlots:hover, QComboBox#comboTones:hover {
            border-color: #00d2ff;
        }
        QComboBox#comboSlots::drop-down, QComboBox#comboTones::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #1a1d2e;
            color: #ffffff;
            selection-background-color: #252a42;
            selection-color: #00d2ff;
            border: 1px solid #2a304d;
        }

        QPushButton#addBtn {
            background-color: #1a1d2e;
            color: #00d2ff;
            border: 2px solid #2a304d;
            border-radius: 8px;
            font-size: 22px;
            font-weight: bold;
        }
        QPushButton#addBtn:hover {
            background-color: #252a42;
            border-color: #00d2ff;
        }

        QPushButton#deleteBtn {
            background-color: #1a1d2e;
            color: #ff3d00;
            border: 2px solid #2a304d;
            border-radius: 8px;
            font-size: 22px;
            font-weight: bold;
        }
        QPushButton#deleteBtn:hover {
            background-color: #252a42;
            border-color: #ff3d00;
        }

        QPushButton#startBtn {
            background-color: #00c853;
            color: #ffffff;
            border: 2px solid #a6a6a6;
            border-radius: 10px;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton#startBtn:hover {
            background-color: #00e676;
            border-color: #ffffff;
        }

        QPushButton#stopBtn {
            background-color: #ff3d00;
            color: #ffffff;
            border: 2px solid #a6a6a6;
            border-radius: 10px;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton#stopBtn:hover {
            background-color: #ff6e40;
            border-color: #ffffff;
        }

        QPushButton#arrowBtn:disabled,
        QPushButton#addBtn:disabled,
        QPushButton#deleteBtn:disabled {
            background-color: #121420;
            color: #2a304d;
            border-color: #181b29;
        }

        QComboBox#comboSlots:disabled,
        QComboBox#comboTones:disabled {
            background-color: #121420;
            color: #3b4259;
            border-color: #181b29;
        }

        QLineEdit#slotTitleInput:disabled {
            color: #3b4259;
            border-bottom-color: #181b29;
        }
        """)

        self.update_timer_display()

    def tick_second(self):
        if self.total_seconds > 0:
            self.total_seconds -= 1
            self.update_timer_display()
            if self.total_seconds == 0:
                self.pause_metronome()
                self.timer_finished.play()

    def update_timer_display(self):
        minutes, seconds = divmod(self.total_seconds, 60)
        self.timer_label.setText(f"{minutes} min {seconds} sec")

    def toggle_metronome(self):
        if self.is_playing:
            self.pause_metronome()
        else:
            self.start_metronome()

    def start_metronome(self):
        if self.total_seconds <= 0:
            return

        interval_ms = int(60000 / self.bpm)
        self.beat_timer.start(interval_ms)
        self.countdown_timer.start()
        self.is_playing = True
        self.set_controls_enabled(False)

        self.start_btn.setText("PAUSE")
        self.start_btn.setStyleSheet("""
            QPushButton#startBtn {
                background-color: #ffb300;
                color: #ffffff;
                border: 2px solid #a6a6a6;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#startBtn:hover { background-color: #ffca28; }
        """)

    def pause_metronome(self):
        self.beat_timer.stop()
        self.countdown_timer.stop()
        self.is_playing = False
        self.set_controls_enabled(True)

        self.start_btn.setText("START")
        self.start_btn.setStyleSheet("""
            QPushButton#startBtn {
                background-color: #00c853;
                color: #ffffff;
                border: 2px solid #a6a6a6;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#startBtn:hover { background-color: #00e676; }
        """)

    def stop_metronome(self):
        self.pause_metronome()
        self.total_seconds = self.configured_seconds
        self.update_timer_display()

    def play_tick(self):
        self.tick_sound.play()

    def on_tone_changed(self, tone_name):
        if tone_name in self.TONES:
            sound_file = self.TONES[tone_name]
            self.tick_sound.setSource(QUrl.fromLocalFile(sound_file))
            self.update_current_slot_data()

    def change_bpm(self, amount):
        if self.is_playing:
            return
        self.bpm += amount
        if self.bpm < 40: 
            self.bpm = 40
        elif self.bpm > 240:
            self.bpm = 240
            
        self.bpm_label.setText(f"{self.bpm} bpm")
        self.update_current_slot_data()

    def change_timer(self, amount):
        if self.is_playing:
            return
        self.configured_seconds += amount
        if self.configured_seconds < 0:
            self.configured_seconds = 0
            
        self.total_seconds = self.configured_seconds
        self.update_timer_display()
        self.update_current_slot_data()

    def load_slots(self):
        default_data = {
            "active_slot": "1",
            "slots": {
                "1": {"name": "slot 1", "bpm": 120, "seconds": 300, "tone": "Standard"}
            }
        }
        
        if os.path.exists("slots.json"):
            try:
                with open("slots.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "slots" in data and data["slots"]:
                        return data
            except Exception:
                return default_data
        return default_data

    def save_slots(self):
        with open("slots.json", "w", encoding="utf-8") as f:
            json.dump(self.slots_data, f, indent=4, ensure_ascii=False)

    def populate_slots_combo(self):
        self.combo_slots.blockSignals(True)
        self.combo_slots.clear()
        for slot_id, data in self.slots_data["slots"].items():
            self.combo_slots.addItem(data["name"], slot_id)
        self.combo_slots.blockSignals(False)

    def apply_slot_data(self, slot_id):
        self.current_slot = str(slot_id)
        slot_info = self.slots_data["slots"][self.current_slot]
        
        self.bpm = slot_info["bpm"]
        self.configured_seconds = slot_info["seconds"]
        self.total_seconds = self.configured_seconds
        
        self.slot_title_input.blockSignals(True)
        self.slot_title_input.setText(slot_info["name"])
        self.slot_title_input.blockSignals(False)
        
        self.bpm_label.setText(f"{self.bpm} bpm")
        self.update_timer_display()
        
        tone_name = slot_info.get("tone", "Standard")
        index_tone = self.combo_tones.findText(tone_name)
        if index_tone != -1:
            self.combo_tones.blockSignals(True)
            self.combo_tones.setCurrentIndex(index_tone)
            self.combo_tones.blockSignals(False)
            self.on_tone_changed(tone_name)

        index_slot = self.combo_slots.findData(self.current_slot)
        if index_slot != -1 and self.combo_slots.currentIndex() != index_slot:
            self.combo_slots.blockSignals(True)
            self.combo_slots.setCurrentIndex(index_slot)
            self.combo_slots.blockSignals(False)

    def on_combo_changed(self, index):
        if index < 0 or self.is_playing:
            return
        selected_id = self.combo_slots.itemData(index)
        if selected_id and selected_id != self.current_slot:
            self.update_current_slot_data()
            self.apply_slot_data(selected_id)

    def on_name_edited(self, new_name):
        slot_key = str(self.current_slot)
        self.slots_data["slots"][slot_key]["name"] = new_name
        
        index = self.combo_slots.findData(self.current_slot)
        if index != -1:
            self.combo_slots.blockSignals(True)
            self.combo_slots.setItemText(index, new_name)
            self.combo_slots.blockSignals(False)
            
        self.save_slots()

    def add_new_slot(self):
        if self.is_playing:
            return
        
        existing_keys = set(int(k) for k in self.slots_data["slots"].keys() if k.isdigit())
        
        new_id_num = 1
        while new_id_num in existing_keys:
            new_id_num += 1
            
        new_id = str(new_id_num)
        new_name = f"slot {new_id}"
        
        self.slots_data["slots"][new_id] = {
            "name": new_name,
            "bpm": 120,
            "seconds": 300,
            "tone": "Standard"
        }
        
        self.update_current_slot_data()
        self.populate_slots_combo()
        self.apply_slot_data(new_id)

    def delete_current_slot(self):
        if self.is_playing or len(self.slots_data["slots"]) <= 1:
            return

        slot_to_delete = str(self.current_slot)
        if slot_to_delete in self.slots_data["slots"]:
            del self.slots_data["slots"][slot_to_delete]

        remaining_keys = list(self.slots_data["slots"].keys())
        new_active_id = remaining_keys[0]

        self.populate_slots_combo()
        self.apply_slot_data(new_active_id)
        self.update_current_slot_data()

    def update_current_slot_data(self):
        slot_key = str(self.current_slot)
        self.slots_data["active_slot"] = self.current_slot
        if slot_key in self.slots_data["slots"]:
            self.slots_data["slots"][slot_key]["bpm"] = self.bpm
            self.slots_data["slots"][slot_key]["seconds"] = self.configured_seconds
            self.slots_data["slots"][slot_key]["name"] = self.slot_title_input.text()
            self.slots_data["slots"][slot_key]["tone"] = self.combo_tones.currentText()
        self.save_slots()

    def set_controls_enabled(self, enabled: bool):
        controls = [
            self.slot_title_input,
            self.btn_dec_bpm_5, self.btn_dec_bpm_1, self.btn_inc_bpm_1, self.btn_inc_bpm_5,
            self.btn_dec_tim_30, self.btn_dec_tim_1, self.btn_inc_tim_1, self.btn_inc_tim_30,
            self.combo_slots, self.add_slot_btn, self.delete_slot_btn,
            self.combo_tones
        ]
        for widget in controls:
            widget.setEnabled(enabled)

    def set_dark_title_bar(self):
        try:
            import ctypes
            hwnd = int(self.winId())
            
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(value), 
                ctypes.sizeof(value)
            )
        except Exception:
            pass

    def closeEvent(self, event):
        self.update_current_slot_data()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetronomeApp()
    window.setFixedSize(700, 350)
    window.show()
    sys.exit(app.exec())