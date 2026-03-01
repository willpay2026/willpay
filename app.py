from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os
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
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    user = query_db("SELECT * FROM usuarios WHERE (telefono=%s OR cedula=%s) AND pin=%s", (dato, dato, pin), one=True)
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    m = query_db("SELECT * FROM movimientos WHERE usuario_id=%s ORDER BY id DESC LIMIT 5", (u['id'],))
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u, m=m)
    return render_template('dashboard.html', u=u)

# --- CONTROL MAESTRO (SWITCH Y TASAS) ---
@app.route('/actualizar_ceo', methods=['POST'])
def actualizar_ceo():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.json
    campo = data.get('campo') # porcentaje_pago, porcentaje_retiro o auto_recargas
    valor = data.get('valor')
    query_db(f"UPDATE usuarios SET {campo} = %s WHERE id = %s", (valor, session['user_id']), commit=True)
    return jsonify({"status": "ok"})

@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS movimientos CASCADE", commit=True)
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, id_dna TEXT, nombre TEXT, telefono TEXT UNIQUE, 
        cedula TEXT UNIQUE, pin TEXT, actividad_economica TEXT,
        saldo_bs FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0, 
        saldo_usd FLOAT DEFAULT 0.0, ganancia_neta FLOAT DEFAULT 0.0,
        porcentaje_pago FLOAT DEFAULT 1.5, porcentaje_retiro FLOAT DEFAULT 2.1,
        auto_recargas BOOLEAN DEFAULT FALSE)""", commit=True)
    
    query_db("""CREATE TABLE movimientos (
        id SERIAL PRIMARY KEY, usuario_id INTEGER, 
        correlativo TEXT, monto_bs FLOAT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""", commit=True)
    
    query_db("""INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad_economica, saldo_bs, saldo_wpc, saldo_usd) 
        VALUES ('CEO-001', 'WILFREDO DONQUIZ', '04126602555', '13496133', '1234', 'FUNDADOR', 100.0, 50.0, 10.0)""", commit=True)
    return "<h1>🏛️ Bóveda Restaurada con Switch</h1><p>Entra a /acceso con 13496133 y 1234</p>"

if __name__ == '__main__': app.run(debug=True)
