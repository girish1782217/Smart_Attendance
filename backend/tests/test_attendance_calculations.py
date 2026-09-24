from app.models.attendance_record import AttendanceStatus
from app.services.attendance_calculations import calculate_attendance_percentage

PRESENT = AttendanceStatus.PRESENT
ABSENT = AttendanceStatus.ABSENT
LATE = AttendanceStatus.LATE
EXCUSED = AttendanceStatus.EXCUSED


def test_all_present_is_100_percent():
    assert calculate_attendance_percentage([PRESENT, PRESENT, PRESENT]) == 100.0


def test_all_absent_is_0_percent():
    assert calculate_attendance_percentage([ABSENT, ABSENT]) == 0.0


def test_mixed_statuses_computed_correctly():
    # 2 present-equivalent (PRESENT, LATE) out of 4 applicable -> 50%
    assert calculate_attendance_percentage([PRESENT, ABSENT, LATE, ABSENT]) == 50.0


def test_late_counts_as_present_equivalent():
    assert calculate_attendance_percentage([LATE, LATE]) == 100.0


def test_excused_excluded_from_numerator_and_denominator():
    # 1 present out of 1 applicable (the 2 EXCUSED are removed entirely) -> 100%
    assert calculate_attendance_percentage([PRESENT, EXCUSED, EXCUSED]) == 100.0


def test_all_excused_returns_none_not_zero_or_hundred():
    assert calculate_attendance_percentage([EXCUSED, EXCUSED]) is None


def test_empty_list_returns_none():
    assert calculate_attendance_percentage([]) is None


def test_rounds_to_two_decimal_places():
    # 1 present out of 3 applicable -> 33.333...% -> 33.33
    assert calculate_attendance_percentage([PRESENT, ABSENT, ABSENT]) == 33.33
