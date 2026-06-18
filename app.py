import os

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from exceptions import StudentManagementError
from system import StudentManagementSystem

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

DATA_FILE = os.environ.get("SDM_DATA_FILE", "sms_data.json")
system = StudentManagementSystem(data_file=DATA_FILE)

try:
    system.load_data()
except FileNotFoundError:
    pass


def persist():
    system.save_data()


@app.context_processor
def inject_summary():
    due_count = sum(1 for fee in system.fees.values() if fee.due_amount() > 0)
    return {
        "summary_total": len(system.students),
        "summary_top_gpa": max((s.gpa for s in system.students), default=0.0),
        "summary_low_attendance": len(system.attendance_defaulters()),
        "summary_fees_due": due_count,
    }


def get_student_choices():
    return [s.student_id for s in system.students]


# ---------------------------------------------------------------- Students
@app.route("/")
def dashboard():
    return render_template("students.html", students=system.students)


@app.route("/students/add", methods=["POST"])
def add_student():
    try:
        student = system.register_student(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            mobile_number=request.form.get("mobile", "").strip(),
            student_id=request.form.get("student_id", "").strip(),
            course=request.form.get("course", "").strip(),
            semester=int(request.form.get("semester") or 1),
            section=request.form.get("section", "").strip(),
        )
        persist()
        flash(f"Registered {student.name} successfully.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


@app.route("/students/update", methods=["POST"])
def update_student():
    try:
        student_id = request.form.get("student_id", "").strip()
        if not student_id:
            raise ValueError("Student ID is required for update.")
        semester = request.form.get("semester", "").strip()
        student = system.update_student(
            student_id,
            name=request.form.get("name", "").strip() or None,
            email=request.form.get("email", "").strip() or None,
            mobile_number=request.form.get("mobile", "").strip() or None,
            course=request.form.get("course", "").strip() or None,
            semester=int(semester) if semester else None,
            section=request.form.get("section", "").strip() or None,
        )
        persist()
        flash(f"Updated {student.name}.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


@app.route("/students/delete", methods=["POST"])
def delete_student():
    try:
        student_id = request.form.get("student_id", "").strip()
        if not student_id:
            raise ValueError("Student ID is required for deletion.")
        student = system.delete_student(student_id)
        persist()
        flash(f"Deleted {student.name}.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


# ------------------------------------------------------------- Attendance
@app.route("/attendance")
def attendance():
    return render_template(
        "attendance.html",
        records=system.attendance_records,
        student_choices=get_student_choices(),
    )


@app.route("/attendance/mark", methods=["POST"])
def mark_attendance():
    try:
        student_id = request.form.get("student_id", "").strip()
        attended = int(request.form.get("attended", "").strip())
        total = int(request.form.get("total", "").strip())
        record = system.mark_attendance(student_id, attended, total)
        persist()
        flash(f"Attendance updated: {record.attendance_percentage:.2f}%.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("attendance"))


# -------------------------------------------------------------------- Fees
@app.route("/fees")
def fees():
    return render_template("fees.html", fees=system.fees, student_choices=get_student_choices())


@app.route("/fees/create", methods=["POST"])
def create_fee():
    try:
        student_id = request.form.get("student_id", "").strip()
        amount = float(request.form.get("amount", "").strip())
        fee = system.create_fee_record(student_id, amount)
        persist()
        flash(f"Fee record created for {fee.student_id}.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("fees"))


@app.route("/fees/collect", methods=["POST"])
def collect_fee():
    try:
        student_id = request.form.get("student_id", "").strip()
        amount = float(request.form.get("amount", "").strip())
        fee = system.collect_fee(student_id, amount)
        persist()
        flash(f"Payment recorded: {fee.payment_status}, due {fee.due_amount():.2f}.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("fees"))


# ------------------------------------------------------------------- Exams
@app.route("/exams")
def exams():
    return render_template("exams.html", exams=system.exams)


@app.route("/exams/schedule", methods=["POST"])
def schedule_exam():
    try:
        exam_id = request.form.get("exam_id", "").strip()
        exam_name = request.form.get("exam_name", "").strip()
        date = request.form.get("date", "").strip()
        if not exam_id or not exam_name or not date:
            raise ValueError("Exam ID, name, and date are required.")
        exam = system.schedule_exam(exam_id, exam_name, date)
        persist()
        flash(f"Scheduled exam {exam.exam_name}.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("exams"))


# ----------------------------------------------------------------- Results
@app.route("/results")
def results():
    return render_template(
        "results.html",
        results=system.results,
        student_choices=get_student_choices(),
        exam_choices=[e.exam_id for e in system.exams],
    )


@app.route("/results/enter", methods=["POST"])
def enter_result():
    try:
        student_id = request.form.get("student_id", "").strip()
        exam_id = request.form.get("exam_id", "").strip()
        subject = request.form.get("subject", "").strip()
        marks = request.form.get("marks", "").strip()
        system.enter_marks(student_id, exam_id, subject, marks)
        persist()
        flash("Result entered successfully.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("results"))


@app.route("/results/update", methods=["POST"])
def update_result():
    try:
        student_id = request.form.get("student_id", "").strip()
        exam_id = request.form.get("exam_id", "").strip()
        subject = request.form.get("subject", "").strip()
        marks = request.form.get("marks", "").strip()
        if not student_id or not exam_id or not subject:
            raise ValueError("Student ID, exam, and subject must all be provided.")
        system.update_marks(student_id, exam_id, subject, marks)
        persist()
        flash("Marks updated successfully.", "success")
    except (StudentManagementError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("results"))


# -------------------------------------------------------------- Performance
@app.route("/performance")
def performance():
    stats = system.students and system.students[0].generate_statistics(system.students) or {
        "total": 0,
        "average_gpa": 0,
        "average_attendance": 0,
    }
    return render_template(
        "performance.html",
        stats=stats,
        toppers=system.toppers(),
        defaulters=system.attendance_defaulters(),
    )


# ------------------------------------------------------------------ Reports
@app.route("/reports")
def reports():
    student_report = None
    requested_id = request.args.get("student_id", "").strip()
    if requested_id:
        try:
            student_report = system.get_student_report(requested_id)
        except StudentManagementError as exc:
            flash(str(exc), "error")
    return render_template("reports.html", student_report=student_report, requested_id=requested_id)


@app.route("/reports/json/<report_type>")
def download_json_report(report_type):
    try:
        filename = system.save_report(report_type)
        return send_file(os.path.abspath(filename), as_attachment=True)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("reports"))


@app.route("/reports/csv/<report_type>")
def download_csv_report(report_type):
    try:
        filename = system.export_csv_report(report_type)
        return send_file(os.path.abspath(filename), as_attachment=True)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("reports"))


# ------------------------------------------------------------- Notifications
@app.route("/notifications")
def notifications():
    return render_template("notifications.html", notifications=system.get_notifications())


@app.route("/notifications/clear", methods=["POST"])
def clear_notifications():
    system.clear_notifications()
    persist()
    flash("Notifications cleared.", "success")
    return redirect(url_for("notifications"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
