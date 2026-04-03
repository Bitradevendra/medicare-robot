# ============================================================
#  Medicare Robot - Audio Output (Text-to-Speech)
#  Speaks text through Bluetooth speaker using gTTS
#  Mutes microphone during playback to prevent feedback loop
# ============================================================

import os
import subprocess

from gtts import gTTS

from config import TTS_LANGUAGE, TTS_SLOW, AUDIO_TEMP_FILE


class AudioOutput:
    """Handles text-to-speech output via Bluetooth speaker."""

    def __init__(self, voice_controller=None):
        """
        Args:
            voice_controller: VoiceController instance to mute/unmute
                              during speech to prevent feedback loop.
        """
        self.is_speaking = False
        self.voice = voice_controller
        self._check_audio_setup()

    def set_voice_controller(self, voice_controller):
        """Set the voice controller reference (for muting during speech)."""
        self.voice = voice_controller

    def _check_audio_setup(self):
        """Check if audio output is configured."""
        print("[AUDIO] Initializing text-to-speech engine...")
        print("[AUDIO] Make sure Bluetooth speaker is paired and connected!")
        print("[AUDIO] To pair: bluetoothctl -> scan on -> pair XX:XX:XX -> connect XX:XX:XX")

    def _play_audio(self, filepath, timeout=30):
        """Play an audio file using mpg321 or mpg123."""
        try:
            subprocess.run(
                ["mpg321", "-q", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout
            )
        except FileNotFoundError:
            try:
                subprocess.run(
                    ["mpg123", "-q", filepath],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout
                )
            except FileNotFoundError:
                print("[AUDIO] ERROR: Install mpg321 or mpg123:")
                print("[AUDIO]   sudo apt install mpg321")
        except subprocess.TimeoutExpired:
            print("[AUDIO] Playback timed out")

    def speak(self, text):
        """
        Convert text to speech and play through speakers.
        Mutes microphone during playback to prevent feedback.

        Args:
            text: The text to speak.
        """
        if not text:
            return

        self.is_speaking = True

        # Mute mic to prevent robot hearing itself
        if self.voice:
            self.voice.mute()

        print(f"[AUDIO] 🔊 Speaking: '{text}'")

        try:
            tts = gTTS(text=text, lang=TTS_LANGUAGE, slow=TTS_SLOW)
            tts.save(AUDIO_TEMP_FILE)
            self._play_audio(AUDIO_TEMP_FILE)
        except Exception as e:
            print(f"[AUDIO] Error speaking: {e}")
        finally:
            self.is_speaking = False
            if os.path.exists(AUDIO_TEMP_FILE):
                os.remove(AUDIO_TEMP_FILE)

            # Unmute mic after speaking is done
            if self.voice:
                self.voice.unmute()

    def play_beep(self):
        """Play a short beep sound to acknowledge wake word."""
        # Mute mic during beep too
        if self.voice:
            self.voice.mute()

        try:
            tts = gTTS(text="yes?", lang=TTS_LANGUAGE, slow=False)
            tts.save(AUDIO_TEMP_FILE)
            self._play_audio(AUDIO_TEMP_FILE, timeout=5)
        except Exception:
            pass
        finally:
            if os.path.exists(AUDIO_TEMP_FILE):
                os.remove(AUDIO_TEMP_FILE)
            if self.voice:
                self.voice.unmute()

    def play_confirmation(self, action_name):
        """Speak a short confirmation of an action."""
        confirmations = {
            "box_1": "Moving to box one",
            "box_2": "Moving to box two",
            "box_3": "Moving to box three",
            "move_forward": "Coming to you",
            "move_backward": "Going back",
            "turn_left": "Turning left",
            "turn_right": "Turning right",
            "stop": "Stopping",
        }
        text = confirmations.get(action_name, action_name)
        self.speak(text)

    def cleanup(self):
        """Clean up resources."""
        if os.path.exists(AUDIO_TEMP_FILE):
            os.remove(AUDIO_TEMP_FILE)
        print("[AUDIO] Cleaned up")


if __name__ == "__main__":
    audio = AudioOutput()
    audio.speak("Hello! I am the Medicare Robot. How can I help you today?")
    audio.play_confirmation("box_1")
    audio.cleanup()
