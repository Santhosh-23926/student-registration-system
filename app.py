
from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from io import BytesIO
from datetime import date
import os

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('DB_USERNAME')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Student(db.Model):
    __tablename__ = "studentdata"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(15), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)


@app.route("/")
def index():
    return render_template("base.html")


@app.route("/insert", methods=["GET", "POST"])
def insert():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        lastname = request.form.get("lastname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        dob = request.form.get("date", "").strip()
        number = request.form.get("number", "").strip()
        gender = request.form.get("gender", "").strip()
        address = request.form.get("address", "").strip()

        if password != confirm_password:
            return "Passwords do not match!"

        if not all([name, lastname, email, password, dob, number, gender, address]):
            return "Please fill all required fields!"

        existing_email = Student.query.filter_by(email=email).first()
        if existing_email:
            return "Email already exists!"

        existing_number = Student.query.filter_by(number=number).first()
        if existing_number:
            return "Phone number already exists!"

        student = Student(
            name=name,
            lastname=lastname,
            email=email,
            password=generate_password_hash(password),
            date=dob,
            number=number,
            gender=gender,
            address=address
        )

        try:
            db.session.add(student)
            db.session.commit()
            return render_template("success.html", student=student)

        except Exception as e:
            db.session.rollback()
            return f"Database error: {e}"

    return render_template("login.html")


@app.route("/certificate/<int:student_id>")
def certificate(student_id):
    student = db.session.get(Student, student_id)

    if student is None:
        return "Student not found!", 404

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))

    pdf.setLineWidth(4)
    pdf.rect(30, 30, 782, 535)

    pdf.setLineWidth(1)
    pdf.rect(40, 40, 762, 515)

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(421, 490, "REGISTRATION CERTIFICATE")

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(421, 440, "This certificate is presented to")

    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawCentredString(421, 390, student.name + " " + student.lastname)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(421, 345, "For successful student registration.")

    pdf.setFont("Helvetica", 13)
    pdf.drawString(150, 285, f"Student ID: {student.id}")
    pdf.drawString(150, 255, f"Email: {student.email}")
    pdf.drawString(150, 225, f"Date of Birth: {student.date}")
    pdf.drawString(150, 195, f"Phone: {student.number}")
    pdf.drawString(150, 165, f"Gender: {student.gender}")
    pdf.drawString(150, 110, f"Issue Date: {date.today().strftime('%d-%m-%Y')}")

    signature_path = os.path.join(app.root_path, "static", "signature.png.jpeg")

    if os.path.exists(signature_path):
        pdf.drawImage(
            signature_path,
            620, 100,
            width=120,
            height=50,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto"
        )

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(680, 80, "Authorized Signature")

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"certificate_{student.id}.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
