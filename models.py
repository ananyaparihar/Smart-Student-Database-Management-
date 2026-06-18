from abc import ABC, abstractmethod
from datetime import datetime

from utils import GRADE_RANGES, today


class Person(ABC):
    def __init__(self, person_id, name, email, mobile_number):
        self.person_id = person_id
        self.name = name
        self.email = email
        self.mobile_number = mobile_number

    @abstractmethod
    def display_details(self):
        pass

    def update_details(self, name=None, email=None, mobile_number=None):
        if name:
            self.name = name
        if email:
            self.email = email
        if mobile_number:
            self.mobile_number = mobile_number

    def to_dict(self):
        return {
            "person_id": self.person_id,
            "name": self.name,
            "email": self.email,
            "mobile_number": self.mobile_number,
        }


class Student(Person):
    total_students = 0

    def __init__(
        self,
        person_id,
        name,
        email,
        mobile_number,
        student_id,
        course="",
        semester=1,
        section="",
        attendance=0.0,
        fee_status="Unpaid",
        gpa=0.0,
    ):
        super().__init__(person_id, name, email, mobile_number)
        self.student_id = student_id
        self.course = course
        self.semester = int(semester)
        self.section = section
        self.attendance = float(attendance)
        self.fee_status = fee_status
        self._gpa = float(gpa)
        Student.total_students += 1

    @property
    def gpa(self):
        return self._gpa

    @gpa.setter
    def gpa(self, value):
        value = float(value)
        if 0 <= value <= 10:
            self._gpa = value

    def register_course(self, course_name):
        self.course = course_name

    def view_result(self, results):
        return [result for result in results.values() if result.student_id == self.student_id]

    def pay_fee(self):
        self.fee_status = "Paid"

    def display_details(self):
        return (
            f"Student ID: {self.student_id}, Name: {self.name}, Section: {self.section}, Course: {self.course}, "
            f"Semester: {self.semester}, Attendance: {self.attendance:.2f}%, "
            f"Fee: {self.fee_status}, GPA: {self.gpa:.2f}"
        )

    def to_dict(self):
        data = super().to_dict()
        data.update(
            {
                "student_id": self.student_id,
                "course": self.course,
                "semester": self.semester,
                "section": self.section,
                "attendance": self.attendance,
                "fee_status": self.fee_status,
                "gpa": self.gpa,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @classmethod
    def generate_statistics(cls, students):
        if not students:
            return {"total": 0, "average_gpa": 0, "average_attendance": 0}
        return {
            "total": len(students),
            "average_gpa": sum(student.gpa for student in students) / len(students),
            "average_attendance": sum(student.attendance for student in students) / len(students),
        }

    def __str__(self):
        return self.display_details()

    def __repr__(self):
        return f"Student(student_id={self.student_id!r}, name={self.name!r})"


class Faculty(Person):
    def __init__(self, person_id, name, email, mobile_number, faculty_id, department, assigned_subjects=None):
        super().__init__(person_id, name, email, mobile_number)
        self.faculty_id = faculty_id
        self.department = department
        self.assigned_subjects = assigned_subjects or []

    def mark_attendance(self, system, student_id, attended, total):
        return system.mark_attendance(student_id, attended, total)

    def enter_marks(self, system, student_id, exam_id, subject, marks):
        return system.enter_marks(student_id, exam_id, subject, marks)

    def display_details(self):
        subjects = ", ".join(self.assigned_subjects) or "None"
        return f"Faculty ID: {self.faculty_id}, Name: {self.name}, Department: {self.department}, Subjects: {subjects}"

    def to_dict(self):
        data = super().to_dict()
        data.update(
            {
                "faculty_id": self.faculty_id,
                "department": self.department,
                "assigned_subjects": self.assigned_subjects,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __str__(self):
        return self.display_details()

    def __repr__(self):
        return f"Faculty(faculty_id={self.faculty_id!r}, name={self.name!r})"


class Course:
    def __init__(self, course_id, course_name, credits, subjects=None):
        self.course_id = course_id
        self.course_name = course_name
        self.credits = int(credits)
        self.subjects = subjects or []

    def add_course(self):
        return self

    def display_course(self):
        subjects = ", ".join(self.subjects) or "No subjects allocated"
        return f"{self.course_id} - {self.course_name} ({self.credits} credits): {subjects}"

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __str__(self):
        return self.display_course()

    def __repr__(self):
        return f"Course(course_id={self.course_id!r}, course_name={self.course_name!r})"


class Attendance:
    def __init__(self, attendance_id, student_id, attended_classes=0, total_classes=0, attendance_percentage=0.0):
        self.attendance_id = attendance_id
        self.student_id = student_id
        self.attended_classes = int(attended_classes)
        self.total_classes = int(total_classes)
        self.attendance_percentage = float(attendance_percentage)

    def mark_attendance(self, attended, total):
        self.attended_classes += int(attended)
        self.total_classes += int(total)
        self.attendance_percentage = self.calculate_percentage(self.attended_classes, self.total_classes)
        return self.attendance_percentage

    @staticmethod
    def calculate_percentage(attended, total):
        return 0.0 if int(total) == 0 else (int(attended) / int(total)) * 100

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Attendance(student_id={self.student_id!r}, percentage={self.attendance_percentage:.2f})"


class Exam:
    def __init__(self, exam_id, exam_name, date):
        self.exam_id = exam_id
        self.exam_name = exam_name
        self.date = date

    def schedule_exam(self):
        return self

    def display_exam(self):
        return f"{self.exam_id} - {self.exam_name} on {self.date}"

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Exam(exam_id={self.exam_id!r}, exam_name={self.exam_name!r})"


class Result:
    def __init__(self, result_id, student_id, exam_id, subject, marks, grade=None):
        self.result_id = result_id
        self.student_id = student_id
        self.exam_id = exam_id
        self.subject = subject
        self._marks = 0
        self.marks = marks
        self.grade = grade or self.calculate_grade(self.marks)

    @property
    def marks(self):
        return self._marks

    @marks.setter
    def marks(self, value):
        value = float(value)
        if value < 0 or value > 100:
            raise ValueError("Marks must be between 0 and 100.")
        self._marks = value

    @staticmethod
    def calculate_grade(marks):
        marks = float(marks)
        for low, high, grade in GRADE_RANGES:
            if low <= marks <= high:
                return grade
        return "Invalid"

    @staticmethod
    def marks_to_gpa(marks):
        return round(float(marks) / 10, 2)

    def generate_result(self):
        self.grade = self.calculate_grade(self.marks)
        return self

    def to_dict(self):
        return {
            "result_id": self.result_id,
            "student_id": self.student_id,
            "exam_id": self.exam_id,
            "subject": self.subject,
            "marks": self.marks,
            "grade": self.grade,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Result(student_id={self.student_id!r}, subject={self.subject!r}, marks={self.marks!r})"


class Fee:
    def __init__(self, fee_id, student_id, amount, payment_status="Due", paid_amount=0.0, payment_date=None):
        self.fee_id = fee_id
        self.student_id = student_id
        self.amount = float(amount)
        self.payment_status = payment_status
        self.paid_amount = float(paid_amount)
        self.payment_date = payment_date

    def collect_fee(self, amount):
        self.paid_amount += float(amount)
        self.payment_date = today()
        self.payment_status = "Paid" if self.paid_amount >= self.amount else "Partial"
        return self.payment_status

    def due_amount(self):
        return max(self.amount - self.paid_amount, 0.0)

    def generate_receipt(self):
        return (
            f"Receipt: {self.fee_id}\nStudent: {self.student_id}\nPaid: {self.paid_amount:.2f}\n"
            f"Due: {self.due_amount():.2f}\nStatus: {self.payment_status}\nDate: {self.payment_date}"
        )

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Fee(student_id={self.student_id!r}, status={self.payment_status!r})"


class Notification:
    def __init__(self, notification_id, message, date=None):
        self.notification_id = notification_id
        self.message = message
        self.date = date or today()

    def send_notification(self):
        return f"[{self.date}] {self.message}"

    def display_notification(self):
        return self.send_notification()

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class Report:
    def __init__(self, report_id, report_type, generated_date=None):
        self.report_id = report_id
        self.report_type = report_type
        self.generated_date = generated_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_report(self, content):
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "generated_date": self.generated_date,
            "content": content,
        }

    def export_report(self, content):
        return self.generate_report(content)
