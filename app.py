from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import psycopg2, os, datetime, random
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

@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('acceso'))

@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS movimientos", commit=True)
    query_db("DROP TABLE IF EXISTS usuarios", commit=True)
    query_db("""
        CREATE TABLE usuarios (
            id SERIAL PRIMARY KEY,
            id_dna TEXT UNIQUE,
            nombre TEXT,
            telefono TEXT UNIQUE,
            cedula TEXT UNIQUE,
            pin TEXT,
            actividad_economica TEXT,
            saldo_bs FLOAT DEFAULT 0.0,
            saldo_wpc FLOAT DEFAULT 0.0,
            saldo_usd FLOAT DEFAULT 0.0,
            ganancia_neta FLOAT DEFAULT 0.0,
            auto_recargas BOOLEAN DEFAULT FALSE,
            auto_retiros BOOLEAN DEFAULT FALSE,
            auto_envios BOOLEAN DEFAULT FALSE,
            es_ceo BOOLEAN DEFAULT FALSE
        )
    """, commit=True)
    query_db("""
        CREATE TABLE movimientos (
            id SERIAL PRIMARY KEY,
            correlativo TEXT UNIQUE,
            usuario_id INTEGER REFERENCES usuarios(id),
            tipo TEXT,
            monto_bs FLOAT,
            referencia TEXT,
            estatus TEXT DEFAULT 'PENDIENTE',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tasa_bcv FLOAT DEFAULT 36.50
        )
    """, commit=True)
    return "<h1>🏛️ PASO 2 COMPLETADO: ADN Digital Blindado</h1>"

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/login', methods=['POST'])
def login():
    t_in = request.form.get('telefono').strip()
    p_in = request.form.get('pin').strip()
    user = query_db("SELECT * FROM usuarios WHERE telefono=%s AND pin=%s", (t_in, p_in), one=True)
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "Error de acceso"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    m = query_db("SELECT * FROM movimientos WHERE usuario_id=%s ORDER BY fecha DESC LIMIT 5", (u['id'],))
    # Si es CEO, mandamos al tablero maestro, si no, al del usuario
    if u['es_ceo']: return render_template('ceo_panel.html', u=u, m=m)
    return render_template('user_panel.html', u=u, m=m)

@app.route('/actualizar_switch', methods=['POST'])
def actualizar_switch():
    data = request.json
    query_db(f"UPDATE usuarios SET {data['campo']} = %s WHERE id = %s", (data['estado'], session['user_id']), commit=True)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
