# ============================================================
#  Medicare Robot - Voice Controller
#  Speech recognition using SpeechRecognition + Google API
#  Requires internet (which is already needed for gTTS & Gemini)
# ============================================================

import time
import threading

import speech_recognition as sr

from config import (
    SAMPLE_RATE, LISTEN_TIMEOUT, PHRASE_TIME_LIMIT,
    WAKE_WORD, COMMANDS
)


class VoiceController:
    """Handles voice recognition using Google Speech Recognition API."""

    def __init__(self, callback=None):
        """
        Initialize the voice controller.

        Args:
            callback: Function to call when a command is recognized.
                      Receives (command_key, raw_text) as arguments.
        """
        self.callback = callback
        self.is_listening = False
        self._listen_thread = None
        self.conversation_mode = False
        self.conversation_callback = None
        self._muted = False  # Mute mic while robot is speaking

        # Initialize recognizer and microphone
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone(sample_rate=SAMPLE_RATE)

        # Calibrate for ambient noise
        print("[VOICE] Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("[VOICE] Microphone calibrated and ready")

    def mute(self):
        """Mute the mic (call before robot speaks to avoid feedback)."""
        self._muted = True

    def unmute(self):
        """Unmute the mic (call after robot finishes speaking)."""
        self._muted = False

    def _process_text(self, text):
        """Process recognized text and map to commands."""
        text = text.lower().strip()
        if not text:
            return

        print(f"[VOICE] Heard: '{text}'")

        # If in conversation mode, send everything to Gemini
        if self.conversation_mode and self.conversation_callback:
            self.conversation_mode = False
            self.conversation_callback(text)
            return

        # Check for wake word first
        if WAKE_WORD in text:
            print(f"[VOICE] ★ Wake word detected: '{WAKE_WORD}'")
            if self.callback:
                self.callback("wake_word", text)
            return

        # Check for known commands
        for phrase, command_key in COMMANDS.items():
            if phrase in text:
                print(f"[VOICE] ★ Command detected: {command_key}")
                if self.callback:
                    self.callback(command_key, text)
                return

        # Unknown phrase
        print("[VOICE] (no matching command)")

    def _listen_loop(self):
        """Main listening loop - runs in separate thread."""
        print("[VOICE] 🎤 Listening for commands...")

        while self.is_listening:
            # Skip listening while robot is speaking (prevents feedback)
            if self._muted:
                time.sleep(0.2)
                continue

            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=LISTEN_TIMEOUT,
                        phrase_time_limit=PHRASE_TIME_LIMIT
                    )

                # Skip recognition if muted during capture
                if self._muted:
                    continue

                # Recognize speech using Google's free API
                try:
                    text = self.recognizer.recognize_google(audio)
                    if text:
                        self._process_text(text)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"[VOICE] Google API error: {e}")
                    print("[VOICE] Check internet connection!")

            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"[VOICE] Error in listen loop: {e}")

    def start_listening(self):
        """Start listening for voice commands in background."""
        if self.is_listening:
            print("[VOICE] Already listening")
            return

        self.is_listening = True
        self._listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="VoiceController"
        )
        self._listen_thread.start()
        print("[VOICE] Started listening thread")

    def stop_listening(self):
        """Stop listening for voice commands."""
        self.is_listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=3)
        print("[VOICE] Stopped listening")

    def enter_conversation_mode(self, callback):
        """
        Enter conversation mode - next recognized phrase goes to Gemini.

        Args:
            callback: Function to call with the user's question text.
        """
        self.conversation_mode = True
        self.conversation_callback = callback
        print("[VOICE] 💬 Conversation mode - listening for question...")

    def cleanup(self):
        """Clean up audio resources."""
        self.stop_listening()
        print("[VOICE] Cleaned up")


if __name__ == "__main__":
    def on_command(command, text):
        print(f"  -> COMMAND: {command} | RAW: {text}")

    voice = VoiceController(callback=on_command)
    try:
        voice.start_listening()
        print("Press Ctrl+C to stop...")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        voice.cleanup()
