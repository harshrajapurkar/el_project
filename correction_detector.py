
import re


CORRECTION_CUES = [
    r"\bnot\b",
    r"\bactually\b",
    r"\binstead\b",
    r"\bcorrection\b",
    r"\bi meant\b",
    r"\bshould be\b",
    r"\bchanged to\b",
    r"\bis wrong\b",
    r"\bwas wrong\b",
    r"\bno longer\b",
]


def clean_text(text):
    """Normalize line endings and unnecessary whitespace."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.split("\n")
    ]
    return "\n".join(lines).strip()


def split_statements(text):
    """Split a conversation into sentence-like statements."""
    text = clean_text(text)

    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+|\n+", text)

    return [part.strip() for part in parts if part.strip()]


def normalize_statement(statement):
    """Normalize a statement for exact duplicate comparison."""
    statement = statement.lower().strip()
    statement = re.sub(r"[^\w\s]", "", statement)
    return re.sub(r"\s+", " ", statement)


def find_corrections(text):
    """
    Detect likely corrections using simple rules and word overlap.

    These are possible corrections, not guaranteed semantic matches.
    """
    statements = split_statements(text)
    events = []

    for index, statement in enumerate(statements):
        lower = statement.lower()

        has_cue = any(
            re.search(cue, lower)
            for cue in CORRECTION_CUES
        )

        if not has_cue:
            continue

        current_words = set(
            normalize_statement(statement).split()
        )
        previous_match = None
        best_similarity = 0.0

        for previous in statements[:index]:
            previous_words = set(
                normalize_statement(previous).split()
            )

            if not previous_words or not current_words:
                continue

            similarity = len(
                previous_words & current_words
            ) / len(previous_words | current_words)

            if similarity > best_similarity:
                best_similarity = similarity
                previous_match = previous

        # Only link the correction when there is reasonable word overlap.
        if best_similarity < 0.15:
            previous_match = None

        events.append({
            "original": previous_match,
            "correction": statement,
            "status": (
                "possible_correction"
                if previous_match
                else "needs_review"
            ),
        })

    return events
