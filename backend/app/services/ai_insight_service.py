from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services import attendance_history_service
from app.services.gemini_client import (
    GeminiInvalidResponseError,
    GeminiProviderError,
    GeminiTimeoutError,
)

_PROMPT_GROUNDING_RULES = (
    "You are an attendance insights assistant for a college attendance system.\n"
    "Use only the data provided below. Do not invent facts. Do not modify "
    "attendance records. Do not make decisions on behalf of administrators. "
    "Clearly distinguish calculated facts (given below) from your own "
    "suggestions.\n\n"
)


def _format_percentage(percentage: float | None) -> str:
    return f"{percentage}%" if percentage is not None else "no data yet"


def _build_prompt(summary: dict) -> str:
    overall = summary["overall"]
    subject_lines = "\n".join(
        f"- {row['subject_name']} ({row['subject_code']}): {_format_percentage(row['percentage'])} "
        f"(present {row['present_count']}, absent {row['absent_count']}, late {row['late_count']}, "
        f"excused {row['excused_count']})"
        for row in summary["by_subject"]
    ) or "(no subject data yet)"

    return (
        _PROMPT_GROUNDING_RULES
        + f"Overall attendance: {_format_percentage(overall['percentage'])}\n"
        + f"Present: {overall['present_count']}, Absent: {overall['absent_count']}, "
        + f"Late: {overall['late_count']}, Excused: {overall['excused_count']}\n\n"
        + f"Subject-wise attendance:\n{subject_lines}\n\n"
        + "In 3-5 sentences: summarize this student's attendance pattern, identify "
        + "which subjects (if any) need attention, and suggest administrative "
        + "follow-up actions. Clearly separate the factual summary from your "
        + "suggestions."
    )


def get_insight(
    db: Session, *, student_id: int, faculty_id_scope: int | None, generate_fn: Callable[[str], str]
) -> dict:
    """Always returns the deterministically-computed summary (`overall`/
    `by_subject`) — these are never derived from or altered by the Gemini
    call. `ai_available`/`insight_text`/`ai_error_code` report the advisory
    narrative's outcome separately."""
    summary = attendance_history_service.get_summary(
        db, student_id=student_id, faculty_id=faculty_id_scope
    )

    settings = get_settings()
    if not settings.gemini_api_key:
        return {**summary, "ai_available": False, "insight_text": None, "ai_error_code": "MISSING_API_KEY"}

    prompt = _build_prompt(summary)
    try:
        insight_text = generate_fn(prompt)
    except GeminiTimeoutError:
        return {**summary, "ai_available": False, "insight_text": None, "ai_error_code": "TIMEOUT"}
    except GeminiInvalidResponseError:
        return {**summary, "ai_available": False, "insight_text": None, "ai_error_code": "INVALID_RESPONSE"}
    except GeminiProviderError:
        return {**summary, "ai_available": False, "insight_text": None, "ai_error_code": "PROVIDER_ERROR"}

    return {**summary, "ai_available": True, "insight_text": insight_text, "ai_error_code": None}
