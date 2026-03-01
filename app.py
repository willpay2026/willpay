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
    except Exception as e:
        conn.rollback()
        raise e
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

# --- LOGIN TODOTERRENO ---
@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login').strip()
    pin = request.form.get('pin_login').strip()
    user = query_db("SELECT * FROM usuarios WHERE (telefono=%s OR cedula=%s) AND pin=%s", (dato, dato, pin), one=True)
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver</a>"

# --- REGISTRO KYC ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre').upper()
    cedula = request.form.get('cedula').strip()
    telefono = request.form.get('telefono').strip()
    actividad = request.form.get('actividad')
    nombre_linea = request.form.get('nombre_linea') or "PARTICULAR"
    pin = request.form.get('pin')
    id_dna = f"WP-{cedula[-4:]}-{actividad[:3].upper()}"
    try:
        query_db("INSERT INTO usuarios (nombre, cedula, telefono, actividad, nombre_linea, pin, id_dna) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                 (nombre, cedula, telefono, actividad, nombre_linea, pin, id_dna), commit=True)
        u = query_db("SELECT id FROM usuarios WHERE cedula=%s", (cedula,), one=True)
        return redirect(url_for('ver_certificado', user_id=u['id']))
    except: return "<h1>⚠️ El usuario ya existe</h1><a href='/acceso'>Entrar</a>"

# --- DASHBOARD CON COMISIÓN 1.5% ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    m_datos = {"banco": "BANESCO", "pago_movil": "04126602555", "cedula": "13496133"}
    # Lógica del Tablero 8 para el CEO
    if u['cedula'] == '13496133':
        usuarios = query_db("SELECT * FROM usuarios ORDER BY id DESC LIMIT 5")
        return render_template('tablero8.html', u=u, m=m_datos, usuarios=usuarios)
    return render_template('dashboard.html', u=u, m=m_datos)

@app.route('/certificado/<int:user_id>')
def ver_certificado(user_id):
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
    return render_template('certificado.html', user=u)

# --- INSTALACIÓN LIMPIA (CON CASCADE) ---
@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS movimientos CASCADE", commit=True)
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, id_dna TEXT UNIQUE, nombre TEXT, telefono TEXT UNIQUE, 
        cedula TEXT UNIQUE, pin TEXT, actividad TEXT, nombre_linea TEXT, 
        saldo_bs FLOAT DEFAULT 0.0, ganancia_neta FLOAT DEFAULT 0.0)""", commit=True)
    # Creación automática del CEO Wilfredo
    query_db("""INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad, saldo_bs) 
        VALUES ('CEO-0001-FOUNDER', 'WILFREDO DONQUIZ', '04126602555', '13496133', '1234', 'CEO', 100000.0)""", commit=True)
    return "<h1>🏛️ Bóveda Will-Pay V3 Lista</h1><a href='/acceso'>Entrar como CEO</a>"

if __name__ == '__main__': app.run(debug=True)
