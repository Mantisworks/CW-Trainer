import tkinter as tk
import random
import threading
import numpy as np
import pygame

# Configurazione Audio
SAMPLING_RATE = 44100
FREQUENCY = 600
WHITE_NOISE_LEVEL = 0.002

class UltraRealCWTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Allenamento CW - IZ7ZKR")
        self.root.geometry("480x620")
        self.root.configure(bg="#121212")

        self.wpm = 10
        self.score = 0
        self.current_sequence = ""
        self.instruction_text = "Scrivi la sequenza e batti invio"
        self.game_running = False
        
        # Variabile per il controllo del testo maiuscolo
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.force_uppercase)
        
        # Inizializzazione Mixer Stereo
        pygame.mixer.quit()
        pygame.mixer.init(frequency=SAMPLING_RATE, size=-16, channels=2)
        
        # Dizionario Morse Esteso
        self.morse_dict = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..',
            '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
            '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
            '?': '..--..', '/': '-..-.', '=': '-...-', '!': '-.-.--', 
            '.': '.-.-.-', ',': '--..--'
        }

        self.groups = {
            "Solo Lettere": [k for k in self.morse_dict if k.isalpha()],
            "Solo Numeri": [k for k in self.morse_dict if k.isdigit()],
            "Caratteri Speciali": ['?', '/', '=', '!', '.', ','],
            "Tutto": list(self.morse_dict.keys())
        }

        self.setup_ui()

    def force_uppercase(self, *args):
        current_text = self.entry_var.get()
        self.entry_var.set(current_text.upper())

    def create_element(self, duration_ms, is_silent=False):
        n_samples = int(SAMPLING_RATE * (duration_ms / 1000.0))
        if is_silent: return np.zeros(n_samples)
        t = np.linspace(0, duration_ms / 1000.0, n_samples, False)
        signal = np.sin(2 * np.pi * FREQUENCY * t)
        rf_s = int(SAMPLING_RATE * 0.005)
        if n_samples > 2 * rf_s:
            window = np.ones(n_samples)
            window[:rf_s] = 0.5 * (1 - np.cos(np.pi * np.arange(rf_s) / rf_s))
            window[-rf_s:] = 0.5 * (1 + np.cos(np.pi * np.arange(rf_s) / rf_s))
            signal *= window
        return signal

    def generate_sequence_audio(self, sequence, wpm):
        dot_ms = 1200 / wpm
        dot = self.create_element(dot_ms)
        dash = self.create_element(dot_ms * 3)
        intra_space = self.create_element(dot_ms, is_silent=True)
        letter_space = self.create_element(dot_ms * 3, is_silent=True)
        
        full_audio = []
        for i, char in enumerate(sequence):
            symbols = self.morse_dict.get(char, "")
            for j, sym in enumerate(symbols):
                full_audio.append(dot if sym == '.' else dash)
                if j < len(symbols) - 1: full_audio.append(intra_space)
            if i < len(sequence) - 1: full_audio.append(letter_space)

        combined = np.concatenate(full_audio)
        noise = (np.random.rand(len(combined)) * 2 - 1) * WHITE_NOISE_LEVEL
        combined += noise
        combined_int = (combined * 32767).clip(-32768, 32767).astype(np.int16)
        return np.column_stack((combined_int, combined_int))

    def play_sequence(self):
        if not self.current_sequence or not self.game_running: return
        audio_data = self.generate_sequence_audio(self.current_sequence, self.wpm)
        sound = pygame.sndarray.make_sound(audio_data)
        sound.play()

    def play_threaded(self):
        if self.game_running:
            threading.Thread(target=self.play_sequence, daemon=True).start()

    def setup_ui(self):
        style_base = {"bg": "#121212", "fg": "#00FF41"}
        
        self.label_stats = tk.Label(self.root, text=f"WPM: {self.wpm} | SCORE: {self.score}", 
                                   **style_base, font=("Courier", 16, "bold"))
        self.label_stats.pack(pady=15)

        tk.Label(self.root, text="Modalità di allenamento:", **style_base, font=("Arial", 9)).pack()
        self.mode_var = tk.StringVar(self.root)
        self.mode_var.set("Solo Lettere")
        self.dropdown = tk.OptionMenu(self.root, self.mode_var, *self.groups.keys())
        self.dropdown.config(bg="#333", fg="white", highlightthickness=0, relief="flat")
        self.dropdown["menu"].config(bg="#333", fg="white")
        self.dropdown.pack(pady=5)

        # Container Bottoni START/STOP
        self.btn_frame = tk.Frame(self.root, bg="#121212")
        self.btn_frame.pack(pady=10)

        self.btn_start = tk.Button(self.btn_frame, text="INIZIA", command=self.start_game, 
                                  bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), width=10, relief="flat")
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = tk.Button(self.btn_frame, text="STOP", command=self.stop_game, 
                                 bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=10, relief="flat", state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.btn_repeat = tk.Button(self.root, text="RIPETI (F1)", command=self.play_threaded, 
                                   state="disabled", bg="#222", fg="#777", relief="flat")
        self.btn_repeat.pack(pady=5)
        self.root.bind('<F1>', lambda e: self.play_threaded())

        self.entry_input = tk.Entry(self.root, textvariable=self.entry_var, font=("Courier", 35), 
                                   justify='center', bg="#000", fg="#00FF41", 
                                   insertbackground="white", borderwidth=0)
        self.entry_input.pack(pady=20, padx=20)
        self.entry_input.bind('<Return>', self.check_answer)
        self.entry_input.config(state="disabled")

        self.label_feedback = tk.Label(self.root, text=self.instruction_text, **style_base, font=("Courier", 10))
        self.label_feedback.pack(pady=10)

        info_text = (
            "COMANDI: INVIO per confermare, F1 per riascoltare.\n"
            "REGOLE: +5 punti se ok. -2 WPM se sbagli.\n"
            "Sotto 10 WPM non si scende."
        )
        self.label_info = tk.Label(self.root, text=info_text, bg="#121212", fg="#555", 
                                  font=("Arial", 8), justify="center")
        self.label_info.pack(side="bottom", pady=20)

    def start_game(self):
        self.game_running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.dropdown.config(state="disabled")
        self.btn_repeat.config(state="normal")
        self.entry_input.config(state="normal")
        self.entry_input.focus_set()
        self.next_round()

    def stop_game(self):
        self.game_running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.dropdown.config(state="normal")
        self.btn_repeat.config(state="disabled")
        self.entry_input.delete(0, tk.END)
        self.entry_input.config(state="disabled")
        # Reset statistiche opzionale
        self.score = 0
        self.wpm = 10
        self.label_stats.config(text=f"WPM: {self.wpm} | SCORE: {self.score}")
        self.label_feedback.config(text="Allenamento terminato", fg="#00FF41")
        self.root.after(2000, self.reset_instruction)

    def next_round(self):
        if not self.game_running: return
        self.entry_input.delete(0, tk.END)
        selected_mode = self.mode_var.get()
        pool = self.groups[selected_mode]
        self.current_sequence = "".join(random.choices(pool, k=3))
        self.root.after(800, self.play_threaded)

    def reset_instruction(self):
        self.label_feedback.config(text=self.instruction_text, fg="#00FF41")

    def check_answer(self, event):
        if not self.game_running: return
        ans = self.entry_var.get().strip()
        if not ans: return

        if ans == self.current_sequence:
            self.score += 5
            self.label_feedback.config(text=f"CORRETTO! ({ans})", fg="#00FF41")
            if self.score > 0 and self.score % 20 == 0: 
                self.wpm += 1
        else:
            self.wpm = max(10, self.wpm - 2)
            self.label_feedback.config(text=f"ERRORE: ERA {self.current_sequence}", fg="#FF3131")
        
        self.label_stats.config(text=f"WPM: {self.wpm} | PUNTEGGIO: {self.score}")
        self.root.after(2000, self.reset_instruction)
        self.next_round()

if __name__ == "__main__":
    root = tk.Tk()
    app = UltraRealCWTrainer(root)
    root.mainloop()