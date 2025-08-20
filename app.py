from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "database.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT NOT NULL,
                            idade INTEGER,
                            telefone TEXT)''')
        conn.commit()

@app.route('/')
def index():
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pacientes")
        pacientes = cursor.fetchall()
    return render_template("index.html", pacientes=pacientes)

@app.route('/add', methods=['POST'])
def add():
    nome = request.form['nome']
    idade = request.form['idade']
    telefone = request.form['telefone']
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pacientes (nome, idade, telefone) VALUES (?, ?, ?)", (nome, idade, telefone))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pacientes WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
