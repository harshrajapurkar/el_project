
import json
import time
from collections import OrderedDict

from correction_detector import (
    clean_text,
    split_statements,
    normalize_statement,
    find_corrections,
)


def remove_exact_duplicates(statements):
    """Remove exact duplicates while preserving original order."""
    unique = []
    seen = set()
    duplicates_removed = 0

    for statement in statements:
        key = normalize_statement(statement)

        if key in seen:
            duplicates_removed += 1
        else:
            seen.add(key)
            unique.append(statement)

    return unique, duplicates_removed


def categorize_statement(statement):
    """Assign a statement to its most appropriate topic."""
    text = statement.lower()

    # Corrections must be checked before ordinary planning keywords.
    correction_keywords = [
        "not", "actually", "instead", "correction",
        "i meant", "should be", "changed to",
        "is wrong", "was wrong", "no longer",
    ]

    if any(word in text for word in correction_keywords):
        return "Corrections and Updates"

    task_keywords = [
        "finish", "complete", "presentation", "slides",
        "submit", "prepare", "implement", "build",
        "create", "assigned", "task",
    ]

    if any(word in text for word in task_keywords):
        return "Tasks and Actions"

    planning_keywords = [
        "meeting", "scheduled", "schedule", "plan",
        "decided", "decision", "deadline", "thursday",
        "friday", "monday", "tuesday", "wednesday",
        "tomorrow", "calendar date",
    ]

    if any(word in text for word in planning_keywords):
        return "Decisions and Plans"

    return "Facts and Reference Information"


def is_important(statement):
    """Identify potentially important statements using transparent rules."""
    text = statement.lower()

    important_keywords = [
        "must", "need to", "required", "deadline",
        "important", "remember", "decided", "agreed",
        "not", "actually", "instead", "correction",
        "should be", "changed to",
    ]

    return any(word in text for word in important_keywords)


def estimate_tokens(text):
    """
    Approximate token count.

    This is a rough estimate, not an exact tokenizer.
    """
    word_count = len(text.split())
    return round(word_count * 1.35) if word_count else 0


def chunk_statements(statements, max_chunk_words=100):
    """Group statements into chunks without splitting statements."""
    if max_chunk_words < 1:
        raise ValueError("max_chunk_words must be at least 1.")

    chunks = []
    current_chunk = []
    current_words = 0

    for statement in statements:
        statement_words = len(statement.split())

        if (
            current_chunk
            and current_words + statement_words > max_chunk_words
        ):
            chunks.append(current_chunk)
            current_chunk = []
            current_words = 0

        # An individual long statement stays intact in its own chunk.
        current_chunk.append(statement)
        current_words += statement_words

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def compress_conversation(
    text,
    max_chunk_words=100,
    correction_events=None,
):
    """Process a conversation and return summary, history and metrics."""
    start_time = time.perf_counter()

    cleaned_text = clean_text(text)
    original_statements = split_statements(cleaned_text)
    original_words = len(cleaned_text.split())

    unique_statements, duplicates_removed = remove_exact_duplicates(
        original_statements
    )

    if correction_events is None:
        correction_events = find_corrections(cleaned_text)

    # Group unique statements by topic while preserving their order.
    topic_groups = OrderedDict()

    for statement in unique_statements:
        topic = categorize_statement(statement)
        topic_groups.setdefault(topic, []).append(statement)

    summary_lines = []

    for topic, statements in topic_groups.items():
        summary_lines.append(f"{topic}:")

        for statement in statements:
            summary_lines.append(f"- {statement}")

    summary_text = "\n".join(summary_lines)

    # Count content words, not formatting headings or bullet markers.
    summary_words = sum(
        len(statement.split())
        for statements in topic_groups.values()
        for statement in statements
    )

    # Preserve correction history separately from the summary.
    correction_history = []

    for event in correction_events:
        correction_history.append({
            "original": event.get("original"),
            "correction": event.get("correction"),
            "status": event.get("status", "needs_review"),
        })

    history_lines = []

    if correction_history:
        history_lines.append("Correction History:")

        for event in correction_history:
            original = (
                event["original"]
                or "Earlier statement not identified"
            )
            correction = (
                event["correction"]
                or "Correction not identified"
            )

            history_lines.append(
                f"- Earlier: {original} | Latest: {correction} "
                f"| Status: {event['status']}"
            )

    compressed_text = summary_text

    if history_lines:
        compressed_text += "\n\n" + "\n".join(history_lines)

    final_output_words = len(compressed_text.split())

    important_statements = [
        statement
        for statement in unique_statements
        if is_important(statement)
    ]

    chunks = chunk_statements(
        unique_statements,
        max_chunk_words=max_chunk_words,
    )

    original_tokens = estimate_tokens(cleaned_text)
    summary_tokens = estimate_tokens(
        " ".join(
            statement
            for statements in topic_groups.values()
            for statement in statements
        )
    )
    final_tokens = estimate_tokens(compressed_text)

    summary_reduction = (
        ((original_words - summary_words) / original_words) * 100
        if original_words
        else 0.0
    )

    final_output_reduction = (
        ((original_words - final_output_words) / original_words) * 100
        if original_words
        else 0.0
    )

    token_reduction = (
        ((original_tokens - summary_tokens) / original_tokens) * 100
        if original_tokens
        else 0.0
    )

    elapsed = time.perf_counter() - start_time

    return {
        "original_text": cleaned_text,
        "original_words": original_words,
        "unique_statement_count": len(unique_statements),
        "duplicates_removed": duplicates_removed,
        "topic_count": len(topic_groups),
        "topics": dict(topic_groups),
        "summary_text": summary_text,
        "summary_words": summary_words,
        "summary_reduction_percentage": round(summary_reduction, 2),
        "compressed_text": compressed_text,
        "final_output_words": final_output_words,
        "word_reduction_percentage": round(
            final_output_reduction, 2
        ),
        "important_context_count": len(important_statements),
        "important_statements": important_statements,
        "correction_count": len(correction_history),
        "correction_history": correction_history,
        "chunk_count": len(chunks),
        "chunks": [
            {
                "chunk_number": index + 1,
                "statements": chunk,
                "word_count": sum(
                    len(statement.split()) for statement in chunk
                ),
            }
            for index, chunk in enumerate(chunks)
        ],
        "original_estimated_tokens": original_tokens,
        "summary_estimated_tokens": summary_tokens,
        "final_estimated_tokens": final_tokens,
        "estimated_token_reduction_percentage": round(
            token_reduction, 2
        ),
        "metrics_note": (
            "Summary reduction measures duplicate removal by word count; "
            "it does not measure semantic sentence shortening. "
            "Final output includes correction history and may be longer "
            "than the original. Token counts are approximate."
        ),
        "processing_time_seconds": round(elapsed, 6),
    }


def to_json(result):
    """Convert the full result to JSON for export and integration."""
    return json.dumps(result, indent=2, ensure_ascii=False)
