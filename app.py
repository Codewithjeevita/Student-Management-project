

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# Database connection
def get_db_connection():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create table
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT NOT NULL,
            department TEXT NOT NULL,
            marks INTEGER NOT NULL,
            attendance INTEGER NOT NULL,
            fees TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid login credentials"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        department = request.form["department"]
        marks = request.form["marks"]
        attendance = request.form["attendance"]
        fees = request.form["fees"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO students (name, roll, department, marks, attendance, fees) VALUES (?, ?, ?, ?, ?, ?)",
            (name, roll, department, marks, attendance, fees)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("view_students"))

    return render_template("add_student.html")

@app.route("/students")
def view_students():
    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search")
    department = request.args.get("department")

    conn = get_db_connection()
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR roll LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if department:
        query += " AND department = ?"
        params.append(department)

    students = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("view_students.html", students=students)


@app.route("/export")
def export_students():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    import csv
    from io import StringIO
    from flask import Response

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Name", "Roll", "Department", "Marks", "Attendance", "Fees"])

    for s in students:
        writer.writerow([s["id"], s["name"], s["roll"], s["department"], s["marks"], s["attendance"], s["fees"]])

    output = si.getvalue()
    return Response(output, mimetype="text/csv",
    headers={"Content-Disposition": "attachment;filename=students.csv"})


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        department = request.form["department"]
        marks = request.form["marks"]
        attendance = request.form["attendance"]
        fees = request.form["fees"]

        conn.execute("""
            UPDATE students
            SET name=?, roll=?, department=?, marks=?, attendance=?, fees=?
            WHERE id=?
        """, (name, roll, department, marks, attendance, fees, id))
        conn.commit()
        conn.close()
        return redirect(url_for("view_students"))

    conn.close()
    return render_template("edit_student.html", student=student)

@app.route("/delete/<int:id>")
def delete_student(id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_students"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
