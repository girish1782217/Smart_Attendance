"""Seed the database with demo data for local development/manual testing.

Assumes migrations have already been applied (`alembic upgrade head`).
Safe to re-run against a fresh database only — it does not check for
existing data and will raise on duplicate emails/codes if run twice against
the same database.

Usage (from backend/):
    ./venv/Scripts/python.exe scripts/seed.py
"""

import random
import sys
from datetime import date, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.roles import RoleName  # noqa: E402
from app.models.attendance_record import AttendanceStatus  # noqa: E402
from app.services import (  # noqa: E402
    attendance_record_service,
    attendance_session_service,
    faculty_assignment_service,
    faculty_service,
    student_service,
    user_service,
)
from app.services.master_data import (  # noqa: E402
    academic_year_service,
    class_service,
    department_service,
    program_service,
    section_service,
    semester_service,
    subject_service,
)

DEMO_PASSWORD = "Password123!"

DEPARTMENTS = [
    ("Computer Science", "CSE"),
    ("Electronics & Communication", "ECE"),
    ("Mechanical Engineering", "MECH"),
]

SUBJECTS_PER_DEPARTMENT = {
    "CSE": ["Data Structures", "Algorithms", "Database Systems", "Operating Systems"],
    "ECE": ["Circuit Theory", "Digital Electronics", "Signals & Systems", "Communication Systems"],
    "MECH": ["Thermodynamics", "Fluid Mechanics", "Machine Design", "Manufacturing Processes"],
}

FACULTY_PER_DEPARTMENT = 8
STUDENTS_PER_SECTION = 20
SESSIONS_PER_ASSIGNMENT = 3
ABSENT_PROBABILITY = 0.12
LATE_PROBABILITY = 0.05


def main() -> None:
    db = SessionLocal()
    random.seed(42)

    try:
        print("Creating admin user...")
        user_service.create_user_with_roles(
            db,
            email="admin@college.edu",
            full_name="System Administrator",
            password=DEMO_PASSWORD,
            role_names=[RoleName.ADMIN],
        )

        print("Creating academic year and semester...")
        academic_year = academic_year_service.create_academic_year(
            db, name="2025-2026", start_date=date(2025, 6, 1), end_date=date(2026, 5, 31)
        )
        semester = semester_service.create_semester(
            db,
            name="Semester 1",
            academic_year_id=academic_year.id,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 11, 30),
        )

        all_students = []

        for dept_name, dept_code in DEPARTMENTS:
            print(f"\n--- {dept_name} ({dept_code}) ---")
            department = department_service.create_department(db, name=dept_name, code=dept_code)
            program = program_service.create_program(
                db, name=f"B.Tech {dept_code}", code=f"BT{dept_code}", department_id=department.id
            )
            academic_class = class_service.create_class(
                db, name="First Year", program_id=program.id
            )

            subjects = [
                subject_service.create_subject(
                    db, name=name, code=f"{dept_code}{i + 1:02d}", department_id=department.id, credits=4
                )
                for i, name in enumerate(SUBJECTS_PER_DEPARTMENT[dept_code])
            ]

            faculty_list = []
            for i in range(FACULTY_PER_DEPARTMENT):
                faculty = faculty_service.create_faculty(
                    db,
                    email=f"faculty.{dept_code.lower()}{i + 1}@college.edu",
                    full_name=f"Dr. {dept_code} Faculty {i + 1}",
                    password=DEMO_PASSWORD,
                    employee_id=f"EMP-{dept_code}-{i + 1:03d}",
                    department_id=department.id,
                )
                faculty_list.append(faculty)
            print(f"  {len(faculty_list)} faculty created")

            sections = []
            for section_name in ("A", "B"):
                section = section_service.create_section(
                    db, name=section_name, class_id=academic_class.id, capacity=STUDENTS_PER_SECTION + 5
                )
                sections.append(section)

                section_students = []
                for i in range(STUDENTS_PER_SECTION):
                    roll_number = f"{dept_code}{section_name}{i + 1:03d}"
                    student = student_service.create_student(
                        db,
                        email=f"student.{roll_number.lower()}@college.edu",
                        full_name=f"Student {roll_number}",
                        password=DEMO_PASSWORD,
                        roll_number=roll_number,
                        section_id=section.id,
                    )
                    section_students.append(student)
                all_students.extend(section_students)
                print(f"  Section {section_name}: {len(section_students)} students")

                # Assign 3 of the department's 4 subjects to 3 different
                # faculty members for this section, then run a few weeks of
                # attendance for each assignment.
                assigned_subjects = subjects[:3]
                for subject_index, subject in enumerate(assigned_subjects):
                    faculty = faculty_list[subject_index % len(faculty_list)]
                    faculty_assignment_service.create_assignment(
                        db,
                        faculty_id=faculty.id,
                        subject_id=subject.id,
                        section_id=section.id,
                        semester_id=semester.id,
                    )

                    for session_offset in range(SESSIONS_PER_ASSIGNMENT):
                        session_date = date.today() - timedelta(
                            days=(SESSIONS_PER_ASSIGNMENT - session_offset) * 2
                        )
                        session = attendance_session_service.create_session(
                            db,
                            faculty_id=faculty.id,
                            subject_id=subject.id,
                            section_id=section.id,
                            session_date=session_date,
                            start_time=time(9 + subject_index, 0),
                            end_time=time(10 + subject_index, 0),
                        )

                        items = []
                        for student in section_students:
                            roll = random.random()
                            if roll < ABSENT_PROBABILITY:
                                status = AttendanceStatus.ABSENT
                            elif roll < ABSENT_PROBABILITY + LATE_PROBABILITY:
                                status = AttendanceStatus.LATE
                            else:
                                status = AttendanceStatus.PRESENT
                            items.append((student.id, status))

                        attendance_record_service.bulk_mark(
                            db,
                            session_id=session.id,
                            items=items,
                            recorded_by_user_id=faculty.user_id,
                        )
                        attendance_record_service.submit_session(db, session.id)

                print(f"  Section {section_name}: attendance seeded for {len(assigned_subjects)} subjects")

        print(f"\nTotal students created: {len(all_students)}")
        print("\nSeed complete.")
        print(f"Demo password for every seeded account: {DEMO_PASSWORD}")
        print("Admin login: admin@college.edu")

    finally:
        db.close()


if __name__ == "__main__":
    main()
