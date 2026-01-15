import customtkinter as ctk
import threading
import json
import os
import time
import random
import speech_recognition as sr
import asyncio
import edge_tts
import pygame
from google import genai
from google.genai import types
from datetime import datetime
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from PIL import Image
import re
from tkinter import filedialog, messagebox
import platform

# ReportLab Imports
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- Configuration & Constants ---
CONFIG_FILE = "config_italian.json"
DEFAULT_CONFIG = {
    "api_key": "",
    "model_name": "gemini-2.0-flash-exp",
    "target_language": "Italian",
    "persona": "Friendly Tutor (Maestro Simpatico)",
    "level": "A2",
    "scenario": "Random",
    "teacher_avatar": "teacher_default.png",
    "user_avatar": "user_default.png",
    "voice": "Elsa (Female)",
    "show_translation": False
}

SCENARIOS = {
    "Italian": {
        "Random": "Randomly select a daily life situation in Italy.",
        "Travel (Viaggio)": "Ordering espresso, buying tickets for the Colosseum, asking for directions to the station.",
        "Shopping (Fare Spesa)": "Buying leather goods in Florence, asking for size, bargaining at a market.",
        "Restaurant (Ristorante)": "Ordering Pizza/Pasta, asking for the wine list, paying the bill (Il conto).",
        "Making Friends (Fare Amicizia)": "Self-introduction, talking about hobbies (soccer, art), asking about plans.",
        "Business (Affari)": "Formal greetings, exchanging contacts, scheduling a meeting."
    },
    "English": {
        "Random": "Randomly select a daily life situation.",
        "Travel": "Ordering coffee, buying tickets, asking for directions.",
        "Shopping": "Buying clothes, asking for size, returning an item.",
        "Restaurant": "Ordering food, paying the bill, asking for recommendations.",
        "Making Friends": "Self-introduction, talking about hobbies, small talk.",
        "Business": "Formal greetings, scheduling a meeting, professional introduction."
    }
}

VOICES = {
    "Italian": {
        "Elsa (Female)": "it-IT-ElsaNeural",
        "Isabella (Female)": "it-IT-IsabellaNeural",
        "Diego (Male)": "it-IT-DiegoNeural"
    },
    "English": {
        "Aria (US Female)": "en-US-AriaNeural",
        "Ana (US Female)": "en-US-AnaNeural",
        "Guy (US Male)": "en-US-GuyNeural",
        "Christopher (US Male)": "en-US-ChristopherNeural"
    }
}

PERSONAS = {
    "Italian": {
        "Friendly Tutor (Maestro Simpatico)": "You are a friendly and patient Italian tutor.",
        "Strict Teacher (Maestro Severo)": "You are a strict Italian teacher who corrects every grammar mistake.",
        "Shop Clerk (Commesso)": "You are a polite shop clerk in an Italian boutique.",
        "Hotel Staff (Receptionist)": "You are a professional hotel receptionist in Rome.",
        "Stranger (Sconosciuto)": "You are a casual local Italian speaking on the street.",
        "Friend (Amico)": "You are a close friend speaking casually (Informal/Tu)."
    },
    "English": {
        "Friendly Tutor": "You are a friendly and patient English tutor.",
        "Strict Teacher": "You are a strict English teacher who corrects every grammar mistake.",
        "Shop Clerk": "You are a polite shop clerk.",
        "Hotel Staff": "You are a professional hotel receptionist.",
        "Stranger": "You are a casual local speaking on the street.",
        "Friend": "You are a close friend speaking casually."
    }
}

def get_all_voices_map():
    all_v = {}
    for lang in VOICES:
        all_v.update(VOICES[lang])
    return all_v

ALL_VOICES_MAP = get_all_voices_map()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ConfigManager:
    @staticmethod
    def load_config():
        if not os.path.exists(CONFIG_FILE):
            ConfigManager.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, val in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = val
                return config
        except Exception:
            return DEFAULT_CONFIG

    @staticmethod
    def save_config(config_data):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

class AudioHandler:
    def __init__(self, voice_key="Elsa (Female)"):
        pygame.mixer.init()
        self.fs = 44100
        self.channels = 1 
        self.voice = ALL_VOICES_MAP.get(voice_key, "it-IT-ElsaNeural")
        self.threshold = 500  # Increased threshold to reduce sensitivity
        self.last_speech_time = 0

    def set_voice(self, voice_key):
        self.voice = ALL_VOICES_MAP.get(voice_key, "it-IT-ElsaNeural")

    def listen(self, gemini_client):
        # Dynamic Listening with VAD (Voice Activity Detection)
        print("Listening (Smart VAD)...")
        
        # Recording constants
        SILENCE_LIMIT = 2.0  # Increased silence limit for natural pauses
        PRE_RECORD = 0.5    # Seconds of buffer
        MIN_RECORD_SECONDS = 0.5 # Minimum duration to consider as speech
        
        audio_data = []
        silence_start = None
        speaking_started = False
        start_record_time = 0
        
        try:
            # Re-initialize stream for each listen intent to avoid buffer overflow issues on some systems
            with sd.InputStream(samplerate=self.fs, channels=1, dtype='int16') as stream:
                start_listening = time.time()
                while True:
                    chunk, overflow = stream.read(int(self.fs * 0.1)) # 100ms
                    if overflow: print("Audio Overflow")
                    
                    # Calculate energy (RMS)
                    rms = np.sqrt(np.mean(chunk.astype(np.int32)**2))
                    
                    if not speaking_started:
                        if rms > self.threshold:
                            print(f"Voice detected! (RMS: {rms:.0f})")
                            speaking_started = True
                            start_record_time = time.time()
                            audio_data.append(chunk)
                            silence_start = None
                        else:
                            # Ring buffer effect (keep last few chunks)
                            if len(audio_data) > int(PRE_RECORD * 10): 
                                audio_data.pop(0)
                            audio_data.append(chunk)
                    else:
                        audio_data.append(chunk)
                        if rms < self.threshold:
                            if silence_start is None:
                                silence_start = time.time()
                            elif time.time() - silence_start > SILENCE_LIMIT:
                                print("Silence detected, stopping...")
                                break
                        else:
                            silence_start = None
                    
                    # Hard Timeout safety (e.g. 20s)
                    if len(audio_data) > 20 * 10: 
                        print("Max duration reached.")
                        break
                    
                    if not gemini_client:
                        break
            
            # Filter out very short noises
            duration = (len(audio_data) * 0.1) - PRE_RECORD
            if not speaking_started or duration < MIN_RECORD_SECONDS:
                 return None

            # Concatenate and save
            full_audio = np.concatenate(audio_data, axis=0)
            temp_wav = f"temp_input_{int(time.time())}.wav"
            wav.write(temp_wav, self.fs, full_audio)
            
            # Send to Gemini for Transcription
            print("Transcribing with Gemini...")
            text = gemini_client.transcribe_audio(temp_wav)
            print(f"Transcribed: {text}")
            
            try:
                os.remove(temp_wav)
            except:
                pass
            
            # Add a cooldown to prevent rapid firing
            time.sleep(1.0)
                
            return text

        except Exception as e:
            print(f"VAD Error: {e}")
            return None

    async def speak(self, text):
        if not text:
            return
        
        # Don't speak if it looks like an API error
        if "RESOURCE_EXHAUSTED" in text or "429" in text:
            print("API Limit Reached. Skipping TTS.")
            return

        # Use unique filename to avoid permission errors
        output_file = f"temp_voice_{int(time.time())}.mp3"
        
        # Split Translation if present
        italian_part = text.split("---")[0]
        
        clean_text = italian_part.strip()
        
        if not clean_text:
            return

        print(f"TTS saying ({self.voice}): {clean_text}") 
        
        try:
            communicate = edge_tts.Communicate(clean_text, self.voice)
            await communicate.save(output_file)
            
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            pygame.mixer.music.unload()
            # Small delay to ensure handle release
            time.sleep(0.2)
            try:
                os.remove(output_file)
            except Exception as e:
                print(f"Warning: Could not remove temp file: {e}")
        except Exception as e:
            print(f"TTS Error: {e}")

class GeminiClient:
    def __init__(self, api_key, model_name, persona, level, scenario, show_translation, target_language="Italian"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.show_translation = show_translation
        self.scenario_name = scenario
        self.persona_name = persona
        self.level = level
        self.target_language = target_language
        
        # Safe get for scenario description
        scenario_desc = SCENARIOS.get(target_language, {}).get(scenario, scenario)
        if scenario == "Random":
            scenario_prompt = f"Randomly pick a common {target_language} scenario and roleplay it."
        else:
            scenario_prompt = f"Roleplay this scenario: {scenario_desc}"
        
        # Safe get for persona prompt
        persona_prompt = PERSONAS.get(target_language, {}).get(persona, persona)

        trans_instruction = ""
        if show_translation:
            trans_instruction = "After the response, add a separator `---` followed by a Traditional Chinese (繁體中文) translation."

        self.system_instruction = (
            f"{persona_prompt} The user's {target_language} level is {level} (CEFR standards). {scenario_prompt} "
            f"Act as a native {target_language} speaker. "
            f"{trans_instruction} "
            "Keep replies concise, helping the conversation flow naturally. "
        )
        
        self.chat = self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7
            )
        )
        self.history = []

    def send_message(self, text):
        try:
            response = self.chat.send_message(text)
            self.history.append({"role": "user", "parts": [text]})
            self.history.append({"role": "model", "parts": [response.text]})
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def transcribe_audio(self, file_path):
        try:
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            
            prompt = f"Listen to this audio and purely transcribe what is said in {self.target_language}. Do NOT translate. If it is silence or noise, return nothing."
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    prompt
                ]
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini STT Error: {e}")
            return ""

    def translate_user_text(self, text):
        prompt = f"Translate the following {self.target_language} text to Traditional Chinese (only output the translation): {text}"
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except:
            return ""

    def generate_report(self):
        prompt = (
            f"對話結束了。請你擔任一位專業的 {self.target_language} 語言教練。"
            f"根據對話紀錄，分析 **使用者(學生)** 的 {self.target_language} 表現。"
            "請「嚴格」針對使用者的 文法(Grammar)、詞彙(Vocabulary) 與 自然度(Naturalness) 進行分析。"
            "**不要** 分析 AI 老師的表現。"
            "請使用 **繁體中文 (Traditional Chinese)** 撰寫這份詳細的分析報告。"
            "請使用 Markdown 項目符號格式，包含以下章節：\n"
            "- **總體評估 (Overall Assessment)**: 簡述使用者的當前程度 (以 CEFR 標準為參考) 與流暢度。\n"
            "- **文法糾正 (Grammar Corrections)**: 引用使用者說錯的句子，並提供修正後的正確說法與解說。\n"
            "- **詞彙建議 (Vocabulary Enhancements)**: 建議在該語境下更自然或更高級的用詞。\n"
            "- **改進建議 (Actionable Advice)**: 針對未來的具體練習建議。"
        )
        try:
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"Report Generation Error: {str(e)}"

class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, text, sender, avatar_path, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.sender = sender
        try:
            if os.path.exists(avatar_path):
                img = ctk.CTkImage(Image.open(avatar_path), size=(40, 40))
            else:
                 img = None
        except:
            img = None 
        self.avatar_label = ctk.CTkLabel(self, text="", image=img)
        bubble_color = "#2B2B2B" if sender == "AI" else "#1F6AA5"
        text_color = "white"
        self.bubble_frame = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=15)
        self.text_label = ctk.CTkLabel(
            self.bubble_frame, 
            text=text, 
            wraplength=400, 
            text_color=text_color, 
            justify="left",
            font=("Meiryo", 14) 
        )
        self.text_label.pack(padx=10, pady=5)
        if sender == "AI":
            self.avatar_label.pack(side="left", anchor="n", padx=(0, 10))
            self.bubble_frame.pack(side="left", anchor="w")
        else:
            self.avatar_label.pack(side="right", anchor="n", padx=(10, 0))
            self.bubble_frame.pack(side="right", anchor="e")
    
    def update_text(self, new_text):
        self.text_label.configure(text=new_text)

class ItalianApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Speaking Practice (Italian/English)")
        self.geometry("1000x800")
        
        self.config = ConfigManager.load_config()
        self.audio_handler = AudioHandler(self.config.get("voice"))
        self.gemini_client = None
        self.is_running = False
        self.timer_seconds = 300 
        
        self.avatars_dir = "assets/avatars"
        if not os.path.exists(self.avatars_dir):
            os.makedirs(self.avatars_dir, exist_ok=True)
            
        self.available_icons = [f for f in os.listdir(self.avatars_dir) if f.endswith(".png")]
        self.available_icons.sort()
        if not self.available_icons:
            self.available_icons = ["default"]
        self.saved_label = None # To track the saved label
        self.setup_ui()

    def setup_ui(self):
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_settings = self.tab_view.add("Settings (Impostazioni)")
        self.tab_practice = self.tab_view.add("Practice (Pratica)")
        self.tab_report = self.tab_view.add("Report (Rapporto)")
        
        self.setup_settings_tab()
        self.setup_practice_tab()
        self.setup_report_tab()

    def setup_settings_tab(self):
        frame = ctk.CTkScrollableFrame(self.tab_settings)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Gemini API Key:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_api_key = ctk.CTkEntry(frame, width=400, show="*")
        self.entry_api_key.pack(anchor="w", padx=10, pady=(0, 10))
        self.entry_api_key.insert(0, self.config.get("api_key", ""))

        ctk.CTkLabel(frame, text="Model Name:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_model = ctk.CTkEntry(frame, width=400)
        self.entry_model.pack(anchor="w", padx=10, pady=(0, 10))
        self.entry_model.insert(0, self.config.get("model_name", "gemini-2.0-flash-exp"))

        # Language Selection
        ctk.CTkLabel(frame, text="Target Language (Lingua):", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.combo_language = ctk.CTkComboBox(frame, width=400, values=["Italian", "English"], command=self.update_settings_options)
        self.combo_language.pack(anchor="w", padx=10, pady=(0, 10))
        self.combo_language.set(self.config.get("target_language", "Italian"))

        ctk.CTkLabel(frame, text="Persona (Ruolo):", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.combo_persona = ctk.CTkComboBox(frame, width=400, values=[])
        self.combo_persona.pack(anchor="w", padx=10, pady=(0, 10))
        # Initial set (will be updated by update_settings_options call below)
        
        ctk.CTkLabel(frame, text="Level (Level/Livello):", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_level = ctk.CTkEntry(frame, width=400)
        self.entry_level.pack(anchor="w", padx=10, pady=(0, 10))
        self.entry_level.insert(0, self.config.get("level", "A2"))
        
        ctk.CTkLabel(frame, text="Scenario (Situazione):", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.option_scenario = ctk.CTkOptionMenu(frame, values=[])
        self.option_scenario.pack(anchor="w", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(frame, text="Voice (Voce):", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.option_voice = ctk.CTkOptionMenu(frame, values=[])
        self.option_voice.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Trigger update to populate values based on current language
        self.update_settings_options(self.combo_language.get())

        ctk.CTkLabel(frame, text="Teacher Avatar:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.option_teacher_avatar = ctk.CTkOptionMenu(frame, values=self.available_icons)
        self.option_teacher_avatar.pack(anchor="w", padx=10, pady=(0, 10))
        self.option_teacher_avatar.set(self.config.get("teacher_avatar", "teacher_default.png"))
        
        ctk.CTkLabel(frame, text="User Avatar:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.option_user_avatar = ctk.CTkOptionMenu(frame, values=self.available_icons)
        self.option_user_avatar.pack(anchor="w", padx=10, pady=(0, 10))
        self.option_user_avatar.set(self.config.get("user_avatar", "user_default.png"))
        
        ctk.CTkLabel(frame, text="Translation (Traduzione):", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.switch_translation = ctk.CTkSwitch(frame, text="Show Traditional Chinese Translation")
        self.switch_translation.pack(anchor="w", padx=10, pady=(0, 10))
        if self.config.get("show_translation", False):
            self.switch_translation.select()
        else:
            self.switch_translation.deselect()

        ctk.CTkButton(frame, text="Save Settings (Salva)", command=self.save_settings).pack(pady=20)
    
    def update_settings_options(self, language):
        # Update Personas
        personas = list(PERSONAS.get(language, {}).keys())
        self.combo_persona.configure(values=personas)
        if self.config.get("persona") in personas and self.config.get("target_language") == language:
            self.combo_persona.set(self.config.get("persona"))
        elif personas:
            self.combo_persona.set(personas[0])
            
        # Update Scenarios
        scenarios = list(SCENARIOS.get(language, {}).keys())
        self.option_scenario.configure(values=scenarios)
        if self.config.get("scenario") in scenarios and self.config.get("target_language") == language:
            self.option_scenario.set(self.config.get("scenario"))
        elif scenarios:
            self.option_scenario.set(scenarios[0])
            
        # Update Voices
        voices = list(VOICES.get(language, {}).keys())
        self.option_voice.configure(values=voices)
        if self.config.get("voice") in voices and self.config.get("target_language") == language:
             self.option_voice.set(self.config.get("voice"))
        elif voices:
            self.option_voice.set(voices[0])

    def save_settings(self):
        new_config = {
            "api_key": self.entry_api_key.get().strip(),
            "model_name": self.entry_model.get().strip(),
            "target_language": self.combo_language.get(),
            "persona": self.combo_persona.get().strip(),
            "level": self.entry_level.get().strip(),
            "scenario": self.option_scenario.get(),
            "teacher_avatar": self.option_teacher_avatar.get(),
            "user_avatar": self.option_user_avatar.get(),
            "voice": self.option_voice.get(),
            "show_translation": bool(self.switch_translation.get())
        }
        ConfigManager.save_config(new_config)
        self.config = new_config
        self.audio_handler.set_voice(new_config["voice"])
        
        # Show Saved Label
        if self.saved_label:
            self.saved_label.destroy()
        
        self.saved_label = ctk.CTkLabel(self.tab_settings, text="Settings Saved!", text_color="#2ECC71", font=("Arial", 16, "bold"))
        self.saved_label.place(relx=0.5, rely=0.9, anchor="center")
        
        # Hide after 3 seconds
        self.after(3000, lambda: self.saved_label.destroy() if self.saved_label else None)
        self.chat_frame = ctk.CTkScrollableFrame(self.tab_practice)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        control_frame = ctk.CTkFrame(self.tab_practice, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.timer_label = ctk.CTkLabel(control_frame, text="05:00", font=("Arial", 24, "bold"), text_color="#2CC985")
        self.timer_label.pack(side="left", padx=20)
        
        self.status_label = ctk.CTkLabel(control_frame, text="Ready", text_color="gray")
        self.status_label.pack(side="left", padx=10)

        self.btn_stop = ctk.CTkButton(control_frame, text="Stop (Ferma)", command=self.stop_practice, fg_color="#C0392B", state="disabled")
        self.btn_stop.pack(side="right", padx=10)

        self.btn_start = ctk.CTkButton(control_frame, text="Start (Inizia)", command=self.start_practice, fg_color="#27AE60")
        self.btn_start.pack(side="right", padx=10)

    def setup_report_tab(self):
        self.report_frame = ctk.CTkFrame(self.tab_report, fg_color="transparent")
        self.report_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.report_display = ctk.CTkTextbox(self.report_frame, state="disabled", font=("Meiryo", 14), wrap="word")
        self.report_display.pack(fill="both", expand=True, pady=(0, 10))
        
        self.btn_export = ctk.CTkButton(self.report_frame, text="Export PDF", command=self.export_pdf, fg_color="#2980B9")
        self.btn_export.pack(side="bottom", pady=10)

    def save_settings(self):
        new_config = {
            "api_key": self.entry_api_key.get().strip(),
            "model_name": self.entry_model.get().strip(),
            "persona": self.combo_persona.get().strip(),
            "level": self.entry_level.get().strip(),
            "scenario": self.option_scenario.get(),
            "teacher_avatar": self.option_teacher_avatar.get(),
            "user_avatar": self.option_user_avatar.get(),
            "voice": self.option_voice.get(),
            "show_translation": bool(self.switch_translation.get())
        }
        ConfigManager.save_config(new_config)
        self.config = new_config
        self.audio_handler.set_voice(new_config["voice"])
        ctk.CTkLabel(self.tab_settings, text="Settings Saved!", text_color="#2ECC71").place(relx=0.5, rely=0.9, anchor="center")

    def add_message(self, sender, text):
        avatar_file = self.config.get("teacher_avatar") if sender == "AI" else self.config.get("user_avatar")
        avatar_path = os.path.join(self.avatars_dir, avatar_file)
        bubble = ChatBubble(self.chat_frame, text, sender, avatar_path)
        bubble.pack(fill="x", pady=5, padx=10)
        self.chat_frame.update_idletasks()
        self.after(50, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))
        return bubble

    def update_timer_ui(self):
        if not self.is_running: return
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.timer_label.configure(text=time_str)
        if self.timer_seconds == 60:
             self.timer_label.configure(text_color="#E67E22")
        if self.timer_seconds <= 0:
            self.stop_practice()
            return
        self.timer_seconds -= 1
        self.after(1000, self.update_timer_ui)

    def start_practice(self):
        if not self.config.get("api_key"):
            self.status_label.configure(text="Error: Missing API Key", text_color="red")
            return
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.chat_frame._parent_canvas.yview_moveto(0.0)

        try:
            self.gemini_client = GeminiClient(
                self.config["api_key"],
                self.config["model_name"],
                self.config["persona"],
                self.config["level"],
                self.config["scenario"],
                self.config.get("show_translation", False),
                self.config.get("target_language", "Italian")
            )
        except Exception as e:
            self.status_label.configure(text=f"Init Error: {e}", text_color="red")
            return

        self.is_running = True
        self.timer_seconds = 300
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.timer_label.configure(text_color="#2CC985")
        self.status_label.configure(text="Session Active", text_color="#2CC985")
        self.update_timer_ui()
        self.thread = threading.Thread(target=self.audio_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop_practice(self):
        if not self.is_running:
            return
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_label.configure(text="Generating Report...", text_color="#3498DB")
        threading.Thread(target=self.finalize_session).start()

    def finalize_session(self):
        if self.gemini_client:
            report = self.gemini_client.generate_report()
            self.report_display.configure(state="normal")
            self.report_display.delete("1.0", "end")
            self.report_display.insert("end", report)
            self.report_display.configure(state="disabled")
            self.tab_view.set("Report (Rapporto)")
        self.status_label.configure(text="Session Ended", text_color="gray")

    def audio_loop(self):
        try:
    def audio_loop(self):
        try:
            intro_response = self.gemini_client.chat.send_message(f"Start the conversation now in {self.gemini_client.target_language}. Briefly greet me.")
            greeting = intro_response.text
            self.gemini_client.history.append({"role": "model", "parts": [greeting]})
        except:
            greeting = "Ciao! Cominciamo."
        formatted_greeting = greeting.replace("---", "\n\n(Traduzione)\n")
        self.add_message("AI", formatted_greeting)
        asyncio.run(self.audio_handler.speak(greeting))

        while self.is_running:
            self.status_label.configure(text="Listening...", text_color="#3498DB")
            user_text = self.audio_handler.listen(self.gemini_client)
            if not self.is_running: break 
            if user_text:
                bubble = self.add_message("You", user_text)
                if self.config.get("show_translation", False):
                    threading.Thread(target=self.update_bubble_translation, args=(bubble, user_text)).start()
                self.status_label.configure(text="Thinking...", text_color="#E67E22")
                ai_response = self.gemini_client.send_message(user_text)
                formatted_response = ai_response.replace("---", "\n\n(Traduzione)\n")
                self.add_message("AI", formatted_response)
                self.status_label.configure(text="Speaking...", text_color="#2CC985")
                asyncio.run(self.audio_handler.speak(ai_response))
            else:
                time.sleep(0.5)

    def update_bubble_translation(self, bubble, text):
        if not self.gemini_client: return
        trans = self.gemini_client.translate_user_text(text)
        if trans:
            new_text = f"{text}\n\n(Traduzione)\n{trans}"
            self.after(0, lambda: bubble.update_text(new_text))

    def export_pdf(self):
        if not self.gemini_client or not self.gemini_client.history:
             messagebox.showinfo("Export", "No conversation data to export.")
             return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF Files", "*.pdf")],
            title="Export Report"
        )
        if not file_path:
            return

        try:
            # Cross-Platform Font Selection
            system = platform.system()
            font_registered = False
            font_name = "Helvetica" # Default fallback
            
            try:
                if system == "Windows":
                    font_path = "C:/Windows/Fonts/msjh.ttc"
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont("MSJhengHei", font_path))
                        font_name = "MSJhengHei"
                        font_registered = True
                    else:
                        # Try Arial
                        font_path = "C:/Windows/Fonts/arial.ttf"
                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont("Arial", font_path))
                            font_name = "Arial"
                            font_registered = True

                elif system == "Darwin": # macOS
                    # ReportLab often works better if we don't force a TTF unless we are sure.
                    # Attempt to find a font for CJK. 
                    # Arial Unicode MS is gone in newer macOS. 
                    # Heiti is usually present.
                    possible_fonts = [
                        "/System/Library/Fonts/STHeiti Light.ttc",
                        "/System/Library/Fonts/PingFang.ttc", 
                        "/Library/Fonts/Arial Unicode.ttf"
                    ]
                    for f in possible_fonts:
                        if os.path.exists(f):
                            # TTC files need subfontIndex, usually 0 is fine
                            pdfmetrics.registerFont(TTFont("MacCJK", f))
                            font_name = "MacCJK"
                            font_registered = True
                            break
                    
                    if not font_registered:
                        # If no CJK font, fallback to built-in. CJK will likely be squares.
                        print("Warning: No CJK font found for macOS PDF export.")
            
            except Exception as e:
                print(f"Font registration failed: {e}. Falling back to default.")

            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Custom Style
            style_normal = ParagraphStyle(
                'CustomNormal', 
                parent=styles['Normal'], 
                fontName=font_name, 
                fontSize=10, 
                leading=14,
                spaceAfter=6
            )
            style_title = ParagraphStyle(
                'CustomTitle', 
                parent=styles['Title'], 
                fontName=font_name, 
                fontSize=18, 
                leading=22,
                spaceAfter=12
            )
            style_heading = ParagraphStyle(
                'CustomHeading', 
                parent=styles['Heading2'], 
                fontName=font_name, 
                fontSize=14, 
                leading=18,
                spaceAfter=10
            )

            story = []
            
            # Header
            story.append(Paragraph("Italian Practice Report", style_title))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", style_normal))
            story.append(Paragraph(f"Level: {self.config.get('level')}", style_normal))
            story.append(Paragraph(f"Scenario: {self.gemini_client.scenario_name or self.config.get('scenario')}", style_normal))
            story.append(Paragraph(f"Persona: {self.gemini_client.persona_name or self.config.get('persona')}", style_normal))
            story.append(Spacer(1, 12))
            
            # Conversation Log
            story.append(Paragraph("Conversation Log:", style_heading))
            for item in self.gemini_client.history:
                role = "User" if item["role"] == "user" else "AI"
                text = item["parts"][0]
                # Simple coloring for user
                p_text = f"<b>{role}:</b> {text}"
                style = ParagraphStyle(
                    'Log', 
                    parent=style_normal, 
                    textColor=colors.HexColor("#1F6AA5") if role == "User" else colors.black
                )
                story.append(Paragraph(p_text, style))
            
            story.append(Spacer(1, 12))

            # Feedback Report
            story.append(Paragraph("Feedback Report:", style_heading))
            report_text = self.report_display.get("1.0", "end")
            
            for line in report_text.split('\n'):
                if not line.strip(): continue
                line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                story.append(Paragraph(line, style_normal))

            doc.build(story)
            messagebox.showinfo("Success", f"PDF Exported successfully to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF:\n{e}")

if __name__ == "__main__":
    app = ItalianApp()
    app.mainloop()
