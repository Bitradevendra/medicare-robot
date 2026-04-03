# ============================================================
#  Medicare Robot - Gemini AI Handler
#  Handles conversation with Google's Gemini API
#  Uses the new google-genai SDK
# ============================================================

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_SYSTEM_PROMPT


class GeminiHandler:
    """Handles AI conversation using Google's Gemini API."""

    def __init__(self):
        self.client = None
        self.chat = None
        self._setup()

    def _setup(self):
        """Configure and initialize the Gemini API."""
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            print("[GEMINI] ⚠ WARNING: API key not set! Edit config.py")
            print("[GEMINI] Get your key at: https://aistudio.google.com/apikey")
            return

        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.chat = self.client.chats.create(
                model=GEMINI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_PROMPT
                )
            )
            print(f"[GEMINI] Initialized with model: {GEMINI_MODEL}")
        except Exception as e:
            print(f"[GEMINI] Error initializing: {e}")

    def ask(self, question):
        """
        Send a question to Gemini and get a response.

        Args:
            question: The user's question text.

        Returns:
            Response text string, or error message.
        """
        if not self.chat:
            return "Sorry, the AI service is not configured. Please check the API key."

        try:
            print(f"[GEMINI] Question: '{question}'")
            response = self.chat.send_message(question)
            answer = response.text.strip()
            print(f"[GEMINI] Answer: '{answer}'")
            return answer
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(f"[GEMINI] Error: {e}")
            return error_msg

    def reset_chat(self):
        """Reset the conversation history."""
        self._setup()
        print("[GEMINI] Chat history reset")


if __name__ == "__main__":
    gemini = GeminiHandler()
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        response = gemini.ask(question)
        print(f"Bot: {response}")
