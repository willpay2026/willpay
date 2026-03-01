from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'
DB_URL = os.environ.get('DATABASE_URL')

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

# --- SOLUCIÓN AL 404: Redirección Inteligente ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('acceso'))

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
            saldo_bs FLOAT DEFAULT 100000.0,
            saldo_wpc FLOAT DEFAULT 100000.0,
            saldo_usd FLOAT DEFAULT 1000.0,
            sw_pagos BOOLEAN DEFAULT TRUE,
            sw_sms BOOLEAN DEFAULT TRUE,
            sw_bio BOOLEAN DEFAULT FALSE,
            sw_legado BOOLEAN DEFAULT TRUE,
            es_ceo BOOLEAN DEFAULT FALSE
        )
    """, commit=True)
    return "<h1>🏛️ Bóveda Will-Pay Reiniciada con Memoria de Switches</h1>"

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/login', methods=['POST'])
def login():
    t_in = request.form.get('telefono_login').strip().replace(" ", "").replace("+58", "")
    p_in = request.form.get('pin_login').strip()
    user = query_db("SELECT * FROM usuarios WHERE telefono=%s AND pin=%s", (t_in, p_in), one=True)
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>Acceso Denegado</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    return render_template('dashboard.html', u=user)

# RUTA PARA GUARDAR ESTADOS EN TIEMPO REAL
@app.route('/actualizar_config', methods=['POST'])
def actualizar_config():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.json
    query_db(f"UPDATE usuarios SET {data['campo']} = %s WHERE id = %s", (data['estado'], session['user_id']), commit=True)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
