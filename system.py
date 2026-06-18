import csv
import json
import os
import random

from exceptions import (
    AttendanceRecordNotFoundError,
    DuplicateRegistrationError,
    FeeRecordNotFoundError,
    InvalidMarksEntryError,
    InvalidStudentIDError,
)
from models import Attendance, Course, Exam, Faculty, Fee, Notification, Report, Result, Student
from utils import log_action, today


class StudentManagementSystem:
    def __init__(self, data_file="sms_data.json", report_dir="reports"):
        self.data_file = data_file
        self.report_dir = report_dir
        self.students = []
        self.faculty = []
        self.courses = []
        self.attendance_records = {}
        self.exams = []
        self.results = {}
        self.fees = {}
        self.notifications = []

    def __len__(self):
        return len(self.students)

    def _next_id(self, prefix):
        return f"{prefix}{random.randint(1000, 9999)}"

    def _find_student_index_recursive(self, student_id, index=0):
        if index >= len(self.students):
            return -1
        if self.students[index].student_id == student_id:
            return index
        return self._find_student_index_recursive(student_id, index + 1)

    def find_student(self, student_id):
        index = self._find_student_index_recursive(student_id)
        if index == -1:
            raise InvalidStudentIDError(f"Student ID {student_id} was not found.")
        return self.students[index]

    @log_action("Student Registration")
    def register_student(self, name, email, mobile_number, student_id, course="", semester=1, section=""):
        if any(student.student_id == student_id for student in self.students):
            raise DuplicateRegistrationError(f"Student ID {student_id} is already registered.")
        student = Student(self._next_id("P"), name, email, mobile_number, student_id, course, semester, section)
        self.students.append(student)
        self.save_data()
        return student

    def update_student(self, student_id, name=None, email=None, mobile_number=None, course=None, semester=None, section=None):
        student = self.find_student(student_id)
        student.update_details(name, email, mobile_number)
        if course:
            student.course = course
        if semester:
            student.semester = int(semester)
        if section is not None:
            student.section = section
        self.save_data()
        return student

    def delete_student(self, student_id):
        student = self.find_student(student_id)
        self.students.remove(student)
        self.attendance_records.pop(student_id, None)
        self.fees.pop(student_id, None)
        self.results = {key: value for key, value in self.results.items() if value.student_id != student_id}
        return student

    def add_faculty(self, name, email, mobile_number, faculty_id, department, subjects):
        faculty = Faculty(self._next_id("P"), name, email, mobile_number, faculty_id, department, subjects)
        self.faculty.append(faculty)
        return faculty

    def add_course(self, course_id, course_name, credits, subjects):
        course = Course(course_id, course_name, credits, subjects)
        self.courses.append(course)
        return course

    def unique_course_names(self):
        return {course.course_name for course in self.courses}

    def register_course(self, student_id, course_name):
        student = self.find_student(student_id)
        student.register_course(course_name)
        return student

    @log_action("Attendance Marking")
    def mark_attendance(self, student_id, attended, total):
        student = self.find_student(student_id)
        record = self.attendance_records.get(student_id)
        if record is None:
            record = Attendance(self._next_id("A"), student_id)
            self.attendance_records[student_id] = record
        percentage = record.mark_attendance(attended, total)
        student.attendance = percentage
        if percentage < 75:
            self.notifications.append(
                Notification(self._next_id("N"), f"Attendance alert for {student.name}: {percentage:.2f}%")
            )
        return record

    def view_attendance(self, student_id):
        if student_id not in self.attendance_records:
            raise AttendanceRecordNotFoundError(f"No attendance record found for {student_id}.")
        return self.attendance_records[student_id]

    def schedule_exam(self, exam_id, exam_name, date):
        exam = Exam(exam_id, exam_name, date)
        self.exams.append(exam)
        self.notifications.append(Notification(self._next_id("N"), f"Exam scheduled: {exam_name} on {date}"))
        return exam

    @log_action("Result Generation")
    def enter_marks(self, student_id, exam_id, subject, marks):
        self.find_student(student_id)
        try:
            marks = float(marks)
            if marks < 0 or marks > 100:
                raise ValueError
        except ValueError as exc:
            raise InvalidMarksEntryError("Marks must be a number between 0 and 100.") from exc

        existing = [
            result
            for result in self.results.values()
            if result.student_id == student_id and result.exam_id == exam_id and result.subject == subject
        ]
        if existing:
            result = existing[0]
            result.marks = marks
            result.grade = result.calculate_grade(result.marks)
            action = "updated"
        else:
            result_id = self._next_id("R")
            result = Result(result_id, student_id, exam_id, subject, marks).generate_result()
            self.results[result_id] = result
            action = "published"

        self._refresh_student_gpa(student_id)
        self.notifications.append(Notification(self._next_id("N"), f"Result {action} for student {student_id}."))
        return result

    @log_action("Result Update")
    def update_marks(self, student_id, exam_id, subject, marks):
        self.find_student(student_id)
        try:
            marks = float(marks)
            if marks < 0 or marks > 100:
                raise ValueError
        except ValueError as exc:
            raise InvalidMarksEntryError("Marks must be a number between 0 and 100.") from exc

        existing = [
            result
            for result in self.results.values()
            if result.student_id == student_id and result.exam_id == exam_id and result.subject == subject
        ]
        if not existing:
            raise InvalidMarksEntryError(
                f"No existing result found for student {student_id} in exam {exam_id} subject {subject}."
            )
        result = existing[0]
        result.marks = marks
        result.grade = result.calculate_grade(result.marks)
        self._refresh_student_gpa(student_id)
        self.notifications.append(Notification(self._next_id("N"), f"Result updated for student {student_id}."))
        return result

    def _refresh_student_gpa(self, student_id):
        student_results = [result for result in self.results.values() if result.student_id == student_id]
        if student_results:
            student = self.find_student(student_id)
            student.gpa = sum(Result.marks_to_gpa(result.marks) for result in student_results) / len(student_results)

    def generate_rank_list(self):
        return sorted(self.students, key=lambda student: student.gpa, reverse=True)

    def toppers(self, minimum_gpa=8.0):
        return [student for student in self.students if student.gpa >= minimum_gpa]

    def attendance_defaulters(self, minimum_attendance=75):
        return [student for student in self.students if student.attendance < minimum_attendance]

    def sorted_by_marks(self):
        totals = {
            student.student_id: sum(result.marks for result in self.results.values() if result.student_id == student.student_id)
            for student in self.students
        }
        return sorted(self.students, key=lambda student: totals.get(student.student_id, 0), reverse=True)

    def sorted_by_attendance(self):
        return sorted(self.students, key=lambda student: student.attendance, reverse=True)

    def sorted_by_gpa(self):
        return sorted(self.students, key=lambda student: student.gpa, reverse=True)

    def create_fee_record(self, student_id, amount):
        self.find_student(student_id)
        fee = Fee(self._next_id("F"), student_id, amount)
        self.fees[student_id] = fee
        return fee

    def collect_fee(self, student_id, amount):
        student = self.find_student(student_id)
        if student_id not in self.fees:
            raise FeeRecordNotFoundError(f"No fee record found for {student_id}.")
        fee = self.fees[student_id]
        fee.collect_fee(amount)
        student.fee_status = fee.payment_status
        if fee.due_amount() > 0:
            self.notifications.append(Notification(self._next_id("N"), f"Fee due for {student.name}: {fee.due_amount():.2f}"))
        return fee

    @log_action("Report Generation")
    def _student_name(self, student_id):
        student = next((s for s in self.students if s.student_id == student_id), None)
        return student.name if student else ""

    def generate_report(self, report_type):
        report = Report(self._next_id("RP"), report_type)
        report_type = report_type.lower()
        if report_type == "student":
            content = [student.to_dict() for student in self.students]
        elif report_type == "attendance":
            content = [dict(record.to_dict(), student_name=self._student_name(record.student_id)) for record in self.attendance_records.values()]
        elif report_type == "fee":
            content = [dict(fee.to_dict(), student_name=self._student_name(fee.student_id)) for fee in self.fees.values()]
        elif report_type == "result":
            content = [dict(result.to_dict(), student_name=self._student_name(result.student_id)) for result in self.results.values()]
        elif report_type == "performance":
            content = {
                "statistics": Student.generate_statistics(self.students),
                "toppers": [student.to_dict() for student in self.toppers()],
                "defaulters": [student.to_dict() for student in self.attendance_defaulters()],
            }
        else:
            content = {"message": "Unknown report type."}
        return report.generate_report(content)

    def report_rows(self, report_type):
        report_type = report_type.lower()
        if report_type == "attendance":
            return [dict(record.to_dict(), student_name=self._student_name(record.student_id)) for record in self.attendance_records.values()]
        if report_type == "result":
            return [dict(result.to_dict(), student_name=self._student_name(result.student_id)) for result in self.results.values()]
        if report_type == "fee":
            return [dict(fee.to_dict(), student_name=self._student_name(fee.student_id)) for fee in self.fees.values()]
        if report_type == "performance":
            return [
                {
                    "student_id": student.student_id,
                    "name": student.name,
                    "course": student.course,
                    "attendance": student.attendance,
                    "gpa": student.gpa,
                    "fee_status": student.fee_status,
                }
                for student in self.students
            ]
        return [student.to_dict() for student in self.students]

    def export_csv_report(self, report_type):
        os.makedirs(self.report_dir, exist_ok=True)
        rows = self.report_rows(report_type)
        filename = os.path.join(self.report_dir, f"{report_type.lower()}_report_{today()}.csv")
        fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else ["message"]
        with open(filename, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            if rows:
                writer.writerows(rows)
            else:
                writer.writerow({"message": "No records available"})
        return filename

    def get_notifications(self):
        return [notification.display_notification() for notification in self.notifications]

    def clear_notifications(self):
        self.notifications.clear()

    def get_student_report(self, student_id):
        student = self.find_student(student_id)
        return {
            "student": student.to_dict(),
            "attendance": self.attendance_records.get(student.student_id).to_dict() if student.student_id in self.attendance_records else None,
            "results": [result.to_dict() for result in self.results.values() if result.student_id == student.student_id],
            "fee": self.fees.get(student.student_id).to_dict() if student.student_id in self.fees else None,
        }

    def save_report(self, report_type, filename=None):
        report_data = self.generate_report(report_type)
        os.makedirs(self.report_dir, exist_ok=True)
        filename = filename or os.path.join(self.report_dir, f"{report_type.lower()}_report_{today()}.json")
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(report_data, json_file, indent=4)
        return filename

    def generate_student_reports(self):
        for student in self.students:
            yield {
                "student": student.to_dict(),
                "attendance": self.attendance_records.get(student.student_id).to_dict()
                if student.student_id in self.attendance_records
                else None,
                "results": [result.to_dict() for result in self.results.values() if result.student_id == student.student_id],
                "fee": self.fees.get(student.student_id).to_dict() if student.student_id in self.fees else None,
            }

    def save_data(self):
        data = {
            "students": [student.to_dict() for student in self.students],
            "faculty": [faculty.to_dict() for faculty in self.faculty],
            "courses": [course.to_dict() for course in self.courses],
            "attendance_records": {key: value.to_dict() for key, value in self.attendance_records.items()},
            "exams": [exam.to_dict() for exam in self.exams],
            "results": {key: value.to_dict() for key, value in self.results.items()},
            "fees": {key: value.to_dict() for key, value in self.fees.items()},
            "notifications": [notification.to_dict() for notification in self.notifications],
        }
        with open(self.data_file, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        return self.data_file

    def load_data(self):
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"{self.data_file} was not found.")
        with open(self.data_file, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        self.students = [Student.from_dict(item) for item in data.get("students", [])]
        self.faculty = [Faculty.from_dict(item) for item in data.get("faculty", [])]
        self.courses = [Course.from_dict(item) for item in data.get("courses", [])]
        self.attendance_records = {
            key: Attendance.from_dict(value) for key, value in data.get("attendance_records", {}).items()
        }
        self.exams = [Exam.from_dict(item) for item in data.get("exams", [])]
        self.results = {key: Result.from_dict(value) for key, value in data.get("results", {}).items()}
        self.fees = {key: Fee.from_dict(value) for key, value in data.get("fees", {}).items()}
        self.notifications = [Notification.from_dict(item) for item in data.get("notifications", [])]
        return True
