FORBIDDEN_PATTERNS = [
    "suicide",
    "kill myself",
    "want to die",
    "self harm",
    "self-harm",
    "how to overdose",
]

CLINICAL_RED_FLAGS = [
    "chest pain",
    "crushing",
    "heart attack",
    "stroke",
    "drooping",
    "can't speak",
    "cannot breathe",
    "shortness of breath",
    "breathing difficulty",
    "gushing blood",
    "unconscious",
]

EMERGENCY_MESSAGE = (
    "🚨 **EMERGENCY WARNING** 🚨\n\n"
    "Your symptoms suggest a potentially life-threatening medical emergency. "
    "Please call your local emergency number right now (e.g., 911 in US, 108/112 in India) "
    "or go to the nearest emergency room immediately.\n\n"
    "I cannot provide further medical guidance on this issue."
)


def check_red_flags(message: str) -> str | None:
    # Return an emergency message if the query looks unsafe, else None.
    low = message.lower()
    if any(p in low for p in FORBIDDEN_PATTERNS):
        return EMERGENCY_MESSAGE
        
    if any(p in low for p in CLINICAL_RED_FLAGS):
        return EMERGENCY_MESSAGE
        
    return None
