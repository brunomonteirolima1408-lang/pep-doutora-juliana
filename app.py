from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3, os, json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.sqlite3")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

def get_settings():
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cpf TEXT,
            birthdate TEXT,
            sex TEXT,
            phone TEXT,
            address TEXT,
            allergies TEXT,
            conditions TEXT,
            medications TEXT,
            notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            anamnesis TEXT,
            physical_exam TEXT,
            diagnosis TEXT,
            plan TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            items TEXT,
            observations TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    con.commit()
    con.close()

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

app = Flask(__name__)
app.secret_key = "change-this-secret"
init_db()

@app.template_filter("brdate")
def brdate(value):
    try:
        d = datetime.fromisoformat(value)
        return d.strftime("%d/%m/%Y %H:%M")
    except:
        return value or ""

@app.route("/")
def index():
    return redirect(url_for("patients"))

@app.route("/patients")
def patients():
    q = request.args.get("q","").strip()
    con = db()
    cur = con.cursor()
    if q:
        cur.execute("SELECT * FROM patients WHERE name LIKE ? OR cpf LIKE ? ORDER BY name", (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM patients ORDER BY id DESC LIMIT 100")
    items = cur.fetchall()
    con.close()
    return render_template("patients.html", items=items, q=q)

@app.route("/patients/new", methods=["GET","POST"])
def new_patient():
    if request.method == "POST":
        data = {k: request.form.get(k) for k in ["name","cpf","birthdate","sex","phone","address","allergies","conditions","medications","notes"]}
        if not data["name"]:
            flash("Nome é obrigatório.")
            return redirect(url_for("new_patient"))
        con = db()
        cur = con.cursor()
        cur.execute("""INSERT INTO patients (name, cpf, birthdate, sex, phone, address, allergies, conditions, medications, notes)
                       VALUES (:name,:cpf,:birthdate,:sex,:phone,:address,:allergies,:conditions,:medications,:notes)""", data)
        con.commit()
        pid = cur.lastrowid
        con.close()
        flash("Paciente cadastrado com sucesso.")
        return redirect(url_for("patient_detail", patient_id=pid))
    return render_template("new_patient.html")

@app.route("/patients/<int:patient_id>")
def patient_detail(patient_id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    p = cur.fetchone()
    if not p:
        con.close()
        return "Paciente não encontrado", 404
    cur.execute("SELECT * FROM consultations WHERE patient_id = ? ORDER BY date DESC", (patient_id,))
    consultations = cur.fetchall()
    cur.execute("SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY date DESC", (patient_id,))
    prescriptions = cur.fetchall()
    con.close()
    return render_template("patient_detail.html", p=p, consultations=consultations, prescriptions=prescriptions)

@app.route("/patients/<int:patient_id>/consultations/new", methods=["POST"])
def add_consultation(patient_id):
    data = {
        "patient_id": patient_id,
        "date": datetime.now().isoformat(timespec="minutes"),
        "anamnesis": request.form.get("anamnesis"),
        "physical_exam": request.form.get("physical_exam"),
        "diagnosis": request.form.get("diagnosis"),
        "plan": request.form.get("plan"),
    }
    con = db()
    cur = con.cursor()
    cur.execute("""INSERT INTO consultations (patient_id, date, anamnesis, physical_exam, diagnosis, plan)
                   VALUES (:patient_id,:date,:anamnesis,:physical_exam,:diagnosis,:plan)""", data)
    con.commit()
    con.close()
    flash("Consulta registrada.")
    return redirect(url_for("patient_detail", patient_id=patient_id))

@app.route("/patients/<int:patient_id>/prescriptions/new", methods=["POST"])
def add_prescription(patient_id):
    data = {
        "patient_id": patient_id,
        "date": datetime.now().isoformat(timespec="minutes"),
        "items": request.form.get("items"),
        "observations": request.form.get("observations"),
    }
    con = db()
    cur = con.cursor()
    cur.execute("""INSERT INTO prescriptions (patient_id, date, items, observations)
                   VALUES (:patient_id,:date,:items,:observations)""", data)
    con.commit()
    con.close()
    flash("Receita salva.")
    return redirect(url_for("patient_detail", patient_id=patient_id))

@app.route("/prescriptions/<int:prescription_id>/pdf")
def prescription_pdf(prescription_id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT pr.*, p.name as patient_name, p.cpf, p.birthdate FROM prescriptions pr JOIN patients p ON p.id = pr.patient_id WHERE pr.id = ?", (prescription_id,))
    pr = cur.fetchone()
    con.close()
    if not pr:
        return "Receita não encontrada", 404

    settings = get_settings()

    # Generate PDF in memory
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, height - 20*mm, settings.get("clinic_header",""))
    c.setFont("Helvetica", 12)
    c.drawString(20*mm, height - 27*mm, settings.get("doctor_name",""))
    c.drawString(20*mm, height - 33*mm, settings.get("crm",""))
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, height - 40*mm, settings.get("address",""))
    c.drawString(20*mm, height - 46*mm, f"Tel: {settings.get('phone','')} — {settings.get('city','')}")

    # Optional signature image
    sig_path = os.path.join(BASE_DIR, "static", "assinatura.png")
    if os.path.exists(sig_path):
        try:
            c.drawImage(sig_path, width - 70*mm, height - 50*mm, 45*mm, 15*mm, preserveAspectRatio=True, mask='auto')
        except:
            pass

    # Patient info
    y = height - 60*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, "Receita Médica")
    y -= 8*mm
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Paciente: {pr['patient_name']}")
    y -= 6*mm
    c.drawString(20*mm, y, f"CPF: {pr['cpf'] or '-'}  |  Nasc.: {pr['birthdate'] or '-'}")
    y -= 6*mm
    c.drawString(20*mm, y, f"Data: {pr['date']}")
    y -= 10*mm

    # Items
    c.setFont("Helvetica", 11)
    text = c.beginText(20*mm, y)
    items = (pr["items"] or "").strip().splitlines()
    if not items:
        items = ["—"]
    for line in items:
        text.textLine(line)
    c.drawText(text)

    # Observations
    y = text.getY() - 10*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, "Observações:")
    y -= 6*mm
    c.setFont("Helvetica", 10)
    obs = (pr["observations"] or "").strip()
    if obs:
        t2 = c.beginText(20*mm, y)
        for line in obs.splitlines():
            t2.textLine(line)
        c.drawText(t2)

    # Footer
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, 15*mm, "Assinatura do Médico:")
    # Draw a line for signature
    c.line(20*mm, 13*mm, 80*mm, 13*mm)
    c.drawRightString(width - 20*mm, 13*mm, "Carimbo e Assinatura")

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"receita_{prescription_id}.pdf")

if __name__ == "__main__":
    app.run(debug=True)
