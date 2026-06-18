class StudentManagementError(Exception):
    """Base exception for the student management system."""


class InvalidStudentIDError(StudentManagementError):
    pass


class DuplicateRegistrationError(StudentManagementError):
    pass


class InvalidMarksEntryError(StudentManagementError):
    pass


class AttendanceRecordNotFoundError(StudentManagementError):
    pass


class FeeRecordNotFoundError(StudentManagementError):
    pass
