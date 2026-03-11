from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# TU URL DE RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (cedula, nombre, rol, saldo) VALUES (%s, %s, 'cliente', 0.00)", (cedula, nombre))
            conn.commit()
            return redirect(url_for('acceso'))
        except:
            conn.rollback()
            return "Error: Cédula ya registrada."
        finally:
            cur.close()
            conn.close()
    return render_template('registro.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula_input = request.form.get('cedula')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE cedula = %s", (cedula_input,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('acceso'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('dashboard.html', user=user)

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('acceso'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
