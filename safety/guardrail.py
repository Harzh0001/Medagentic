FORBIDDEN_PATTERNS = [
    "suicide",
    "kill myself",
    "want to die",
    "self harm",
    "self-harm",
    "how to overdose",
    "prescribe me",
    "prescription for",
]

EMERGENCY_MESSAGE = (
    "I'm sorry you're going through this. You deserve immediate support. "
    "Please call your local emergency number right now "
    "(in India: 108 or 112) or a crisis helpline. "
    "I cannot provide medical guidance on this, but there are people who "
    "can help immediately."
)

DISCLAIMER = (
    "Educational decision-support output, not medical advice and not a "
    "diagnosis. Always consult a qualified clinician for medical decisions."
)


def check_query(message: str) -> str | None:
    # Return an emergency message if the query looks unsafe, else None.
    low = message.lower()
    if any(p in low for p in FORBIDDEN_PATTERNS):
        return EMERGENCY_MESSAGE
    return None
