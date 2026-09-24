from app.models.attendance_record import AttendanceStatus

# See docs/sdd/00-product-spec.md Assumption A-2: EXCUSED is removed from
# both numerator and denominator (an excused absence never penalizes a
# student); LATE counts as a full present-equivalent (the student did
# attend). This is the single source of truth for attendance % — never
# computed ad hoc elsewhere, by the frontend, or by the AI (SPEC 15).
PRESENT_EQUIVALENT_STATUSES = frozenset({AttendanceStatus.PRESENT, AttendanceStatus.LATE})


def calculate_percentage_from_counts(present_equivalent: int, total_applicable: int) -> float | None:
    """The same formula, taking pre-aggregated counts instead of a raw
    status list — used where the aggregation already happened in SQL
    (SPEC 11's cross-student reports) so the DB does the heavy per-record
    grouping and only one row per student flows into Python."""
    if total_applicable == 0:
        return None
    return round((present_equivalent / total_applicable) * 100, 2)


def calculate_attendance_percentage(statuses: list[AttendanceStatus]) -> float | None:
    """Returns None (not 0 or 100) when there are zero applicable
    (non-EXCUSED) records — "no data" is a distinct case from "0%"."""
    applicable = [status for status in statuses if status != AttendanceStatus.EXCUSED]
    present_equivalent = sum(1 for status in applicable if status in PRESENT_EQUIVALENT_STATUSES)
    return calculate_percentage_from_counts(present_equivalent, len(applicable))
