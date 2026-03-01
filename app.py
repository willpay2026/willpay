from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'
DB_URL = os.environ.get('DATABASE_URL')

# --- MOTOR DE BASE DE DATOS ---
def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute(query, args)
        if commit:
            conn.commit()
            return None
        return cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

# --- LÓGICA DE REGISTRO KYC ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre').upper()
    cedula = request.form.get('cedula').strip()
    telefono = request.form.get('telefono').strip()
    actividad = request.form.get('actividad')
    nombre_linea = request.form.get('nombre_linea') or "PARTICULAR"
    pin = request.form.get('pin')

    # GENERACIÓN DE ID DNA (WP + Últimos 4 Cédula + Siglas Actividad)
    id_dna = f"WP-{cedula[-4:]}-{actividad[:3].upper()}"

    try:
        query_db("""
            INSERT INTO usuarios 
            (nombre, cedula, telefono, actividad, nombre_linea, pin, id_dna, saldo_bs, estatus_kyc)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0.0, 'AUDITADO')
        """, (nombre, cedula, telefono, actividad, nombre_linea, pin, id_dna), commit=True)
        
        user = query_db("SELECT id FROM usuarios WHERE cedula=%s", (cedula,), one=True)
        return redirect(url_for('ver_certificado', user_id=user['id']))
    except Exception as e:
        return f"Error: {str(e)} <a href='/registro'>Volver</a>"

# --- CERTIFICADO Y EXPEDIENTE ---
@app.route('/certificado/<int:user_id>')
def ver_certificado(user_id):
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
    return render_template('certificado.html', user=user)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    # Datos de tu cuenta para la sección de recarga
    mis_datos = {"banco": "BANESCO", "pago_movil": "04126602555", "cedula": "13496133"}
    return render_template('dashboard.html', u=u, m=mis_datos)

@app.route('/actualizar_config', methods=['POST'])
def actualizar_config():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.json
    query_db(f"UPDATE usuarios SET {data['campo']} = %s WHERE id = %s", (data['estado'], session['user_id']), commit=True)
    return jsonify({"status": "ok"})

# --- INICIALIZACIÓN (IMPORTANTE CORRER UNA VEZ) ---
@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS usuarios", commit=True)
    query_db("""
        CREATE TABLE usuarios (
            id SERIAL PRIMARY KEY,
            id_dna TEXT UNIQUE,
            nombre TEXT,
            telefono TEXT UNIQUE,
            cedula TEXT UNIQUE,
            pin TEXT,
            actividad TEXT,
            nombre_linea TEXT,
            saldo_bs FLOAT DEFAULT 0.0,
            sw_pagos BOOLEAN DEFAULT TRUE,
            sw_legado BOOLEAN DEFAULT TRUE,
            estatus_kyc TEXT DEFAULT 'AUDITADO'
        )
    """, commit=True)
    return "<h1>🏛️ Bóveda Will-Pay V3 Inicializada</h1>"

if __name__ == '__main__':
    app.run(debug=True)
