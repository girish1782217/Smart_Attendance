from app.models.academic_class import AcademicClass
from app.models.academic_year import AcademicYear
from app.models.department import Department
from app.models.program import Program
from app.models.section import Section
from app.models.semester import Semester
from app.models.subject import Subject
from app.repositories.crud_base import CRUDBase

department_crud = CRUDBase(Department)
program_crud = CRUDBase(Program)
academic_year_crud = CRUDBase(AcademicYear)
semester_crud = CRUDBase(Semester)
class_crud = CRUDBase(AcademicClass)
section_crud = CRUDBase(Section)
subject_crud = CRUDBase(Subject)
