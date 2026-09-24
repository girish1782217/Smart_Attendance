from app.models.attendance_record import AttendanceStatus

# See docs/sdd/00-product-spec.md Assumption A-2: EXCUSED is removed from
# both numerator and denominator (an excused absence never penalizes a
# student); LATE counts as a full present-equivalent (the student did
# attend). This is the single source of truth for attendance % — never
# computed ad hoc elsewhere, by the frontend, or by the AI (SPEC 15).
PRESENT_EQUIVALENT_STATUSES = frozenset({AttendanceStatus.PRESENT, AttendanceStatus.LATE})


def calculate_attendance_percentage(statuses: list[AttendanceStatus]) -> float | None:
    """Returns None (not 0 or 100) when there are zero applicable
    (non-EXCUSED) records — "no data" is a distinct case from "0%"."""
    applicable = [status for status in statuses if status != AttendanceStatus.EXCUSED]
    if not applicable:
        return None

    present_equivalent = sum(1 for status in applicable if status in PRESENT_EQUIVALENT_STATUSES)
    return round((present_equivalent / len(applicable)) * 100, 2)
