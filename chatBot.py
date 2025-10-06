from datetime import datetime

# --- API Key ---
# Replace with your actual Groq API key
APIKEY = ""


# --- Conversation Wrapper ---
class Human:
    """
    Represents a connected human user for the chatbot.
    Keeps track of their conversation messages for context.
    """
    def __init__(self, sid):
        self.sid = sid
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant integrated into a Forest Rights Act DSS platform. "
                    "Be concise, factual, and polite. You may help users interpret FRA claim data, "
                    "analyze eligibility summaries, or discuss LULC and GIS-based insights."
                )
            }
        ]
        self.created_at = datetime.utcnow()

    def add_message(self, role, content):
        """Add a message to the chat history."""
        self.history.append({"role": role, "content": content})

    def get_messages(self):
        """Return the full conversation history."""
        return self.history

    def clear(self):
        """Reset the chat history (optional use)."""
        self.history = self.history[:1]