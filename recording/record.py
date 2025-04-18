import tkinter as tk
from tkinter import scrolledtext, messagebox
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import threading
import subprocess
import os
import tempfile
import queue 

WHISPER_CPP_PATH = r"C:\Users\mucef\Desktop\hackthun\whisper.cpp" 
WHISPER_CPP_EXECUTABLE = os.path.join(WHISPER_CPP_PATH, "build", "bin", "Release", "whisper-cli.exe") 
WHISPER_MODEL_PATH = os.path.join(WHISPER_CPP_PATH, "models", "ggml-base.bin") 

SAMPLE_RATE = 16000  
CHANNELS = 1

class VoiceRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Voice Recorder")

        self.is_recording = False
        self.audio_data = []
        self.stream = None
        self.temp_wav_file = None
        self.result_queue = queue.Queue() 

        self.status_label = tk.Label(root, text="Status: Idle", width=40)
        self.status_label.pack(pady=5)

        self.record_button = tk.Button(root, text="Record", command=self.toggle_recording, width=20, height=2)
        self.record_button.pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15)
        self.result_text.pack(pady=10, padx=10)
        self.result_text.insert(tk.END, "Transcription will appear here...")
        self.result_text.config(state=tk.DISABLED)

        if not os.path.exists(WHISPER_CPP_EXECUTABLE):
            messagebox.showerror("Error", f"Whisper executable not found at:\n{WHISPER_CPP_EXECUTABLE}\nPlease check the WHISPER_CPP_EXECUTABLE path in the script.")
            self.record_button.config(state=tk.DISABLED)
        if not os.path.exists(WHISPER_MODEL_PATH):
             messagebox.showerror("Error", f"Whisper model not found at:\n{WHISPER_MODEL_PATH}\nPlease check the WHISPER_MODEL_PATH path in the script.")
             self.record_button.config(state=tk.DISABLED)

        try:
            sd.check_input_settings(samplerate=SAMPLE_RATE, channels=CHANNELS)
        except Exception as e:
             messagebox.showerror("Audio Error", f"Could not open microphone. Make sure one is connected and permissions are granted.\nError: {e}")
             self.record_button.config(state=tk.DISABLED)

        self.root.after(100, self.check_queue)


    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio Status Warning: {status}", flush=True)
        self.audio_data.append(indata.copy())

    def start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.audio_data = [] 
        self.status_label.config(text="Status: Recording...")
        self.record_button.config(text="Stop Recording")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Recording...")
        self.result_text.config(state=tk.DISABLED)

        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=self._audio_callback,
                dtype='int16'
            )
            self.stream.start()
        except Exception as e:
            messagebox.showerror("Recording Error", f"Could not start recording stream: {e}")
            self.is_recording = False
            self.status_label.config(text="Status: Error")
            self.record_button.config(text="Record")


    def stop_recording(self):
        if not self.is_recording:
            return

        self.status_label.config(text="Status: Stopping...")
        self.record_button.config(state=tk.DISABLED) 

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            self.is_recording = False
            self.record_button.config(text="Record")

            if not self.audio_data:
                self.status_label.config(text="Status: No audio recorded.")
                self.record_button.config(state=tk.NORMAL)
                return

            self.status_label.config(text="Status: Processing audio...")

            recording = np.concatenate(self.audio_data, axis=0)


            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                self.temp_wav_file = f.name
            wav.write(self.temp_wav_file, SAMPLE_RATE, recording)
            print(f"Audio saved temporarily to: {self.temp_wav_file}")

            self.status_label.config(text="Status: Transcribing...")
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Transcribing, please wait...")
            self.result_text.config(state=tk.DISABLED)

            transcribe_thread = threading.Thread(target=self.run_whisper, args=(self.temp_wav_file,))
            transcribe_thread.daemon = True 
            transcribe_thread.start()

        except Exception as e:
            messagebox.showerror("Processing Error", f"Error processing audio: {e}")
            self.status_label.config(text="Status: Error")
            self.record_button.config(state=tk.NORMAL)
            self.cleanup_temp_file() 


    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def run_whisper(self, audio_file_path):
        try:
            command = [
                WHISPER_CPP_EXECUTABLE,
                "-l", "ar",
                "-f", audio_file_path,
                "-m", WHISPER_MODEL_PATH,
                "-nt", 
                "-t", "8", 
            ]
            print(f"Running command: {' '.join(command)}")

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True, # Raise exception on non-zero exit code
                encoding='utf-8' # Ensure correct decoding
            )

            transcription = process.stdout.strip()
            print(f"Whisper Output:\n{transcription}")
            # Put result in queue for main thread
            self.result_queue.put(("success", transcription))

        except FileNotFoundError:
             self.result_queue.put(("error", f"Error: Whisper executable not found at {WHISPER_CPP_EXECUTABLE}"))
        except subprocess.CalledProcessError as e:
            error_message = f"Whisper.cpp failed (exit code {e.returncode}):\n{e.stderr}"
            print(error_message, flush=True)
            self.result_queue.put(("error", error_message))
        except Exception as e:
            error_message = f"An unexpected error occurred during transcription: {e}"
            print(error_message, flush=True)
            self.result_queue.put(("error", error_message))
        finally:
            # Cleanup should ideally happen after the result is processed in main thread
            # But putting it here ensures it runs even if queue processing fails somehow.
            # We will also call cleanup from the main thread after processing the queue item.
            # self.cleanup_temp_file() # Moved to main thread after processing result
            pass # Let main thread handle cleanup via queue signal

    def check_queue(self):
        """Checks the result queue and updates the GUI. Runs periodically."""
        try:
            status, result = self.result_queue.get_nowait()

            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.config(state=tk.DISABLED)

            if status == "success":
                 self.status_label.config(text="Status: Transcription Complete")
            else: # status == "error"
                 self.status_label.config(text="Status: Transcription Error")
                 # Optionally show message box again for critical errors
                 # messagebox.showerror("Transcription Error", result)

            # Re-enable button and cleanup after processing
            self.record_button.config(state=tk.NORMAL)
            self.cleanup_temp_file()

        except queue.Empty:
            # No message yet, continue checking
            pass
        finally:
            # Schedule the next check
            self.root.after(100, self.check_queue)


    def cleanup_temp_file(self):
        if self.temp_wav_file and os.path.exists(self.temp_wav_file):
            try:
                os.remove(self.temp_wav_file)
                print(f"Temporary file deleted: {self.temp_wav_file}")
                self.temp_wav_file = None
            except OSError as e:
                print(f"Error deleting temporary file {self.temp_wav_file}: {e}", flush=True)
                # Log error, maybe show a warning to the user if important

    def on_closing(self):
        if self.is_recording:
            messagebox.showwarning("Recording", "Please stop the recording before closing.")
            return # Prevent closing while recording

        # Clean up stream if somehow left open (shouldn't happen with normal flow)
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.cleanup_temp_file()
        self.root.destroy()


if __name__ == "__main__":
    # --- Check paths ---
    if not os.path.isdir(os.path.dirname(WHISPER_CPP_EXECUTABLE)):
         print(f"WARNING: Directory for executable does not exist: {os.path.dirname(WHISPER_CPP_EXECUTABLE)}")
    if not os.path.isdir(os.path.dirname(WHISPER_MODEL_PATH)):
         print(f"WARNING: Directory for model does not exist: {os.path.dirname(WHISPER_MODEL_PATH)}")

    # --- Run App ---
    root = tk.Tk()
    app = VoiceRecorderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle closing cleanly
    root.mainloop()