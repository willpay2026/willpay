from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'willpay_legado_final_v2'
DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        user_input = request.form.get('nombre') # Usamos nombre/cédula según tu captura
        pin = request.form.get('pin')
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM usuarios WHERE (nombre=%s OR cedula=%s) AND pin=%s", (user_input, user_input, pin))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['rol'] = user['rol']
            return redirect(url_for('dashboard') if user['rol'] == 'SOCIO' else url_for('tablero_maestro'))
    return render_template('acceso.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        tel = request.form.get('telefono')
        pin = request.form.get('pin')
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nombre, cedula, telefono, pin, rol) VALUES (%s, %s, %s, %s, 'SOCIO')", 
                    (nombre, cedula, tel, pin))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('acceso'))
    return render_template('registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    cur.execute("SELECT * FROM pagos WHERE emisor_id=%s OR receptor_id=%s ORDER BY fecha DESC LIMIT 5", (u['id'], u['id']))
    movs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', u=u, movimientos=movs)

@app.route('/tablero_maestro')
def tablero_maestro():
    if 'user_id' not in session or session['rol'] != 'CEO': return redirect(url_for('acceso'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    cur.execute("SELECT * FROM usuarios WHERE rol='SOCIO'")
    socios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('tablero_maestro.html', u=u, socios=socios)

@app.route('/instalar')
def instalar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios, pagos CASCADE")
    cur.execute("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, nombre TEXT, cedula TEXT UNIQUE, telefono TEXT, 
        pin TEXT, saldo_bs FLOAT DEFAULT 0.0, saldo_usd FLOAT DEFAULT 0.0, rol TEXT)""")
    cur.execute("""CREATE TABLE pagos (
        id SERIAL PRIMARY KEY, emisor_id INTEGER, receptor_id INTEGER, 
        monto FLOAT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("INSERT INTO usuarios (nombre, cedula, pin, rol, saldo_bs) VALUES ('WILFREDO DONQUIZ', '13496133', '1234', 'CEO', 100.00)")
    conn.commit()
    cur.close()
    conn.close()
    return "SISTEMA SINCRONIZADO"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
