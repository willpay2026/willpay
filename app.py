from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2, os, random
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny' # El legado para Wilyanny Donquiz
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

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index(): 
    return render_template('splash.html')

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html')

@app.route('/registro')
def registro(): 
    return render_template('registro.html')

# --- PROCESAMIENTO DE REGISTRO (SINCRONIZADO) ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    telefono = request.form.get('telefono', '').strip()
    actividad = request.form.get('actividad', 'usuario')
    nombre_linea = request.form.get('nombre_linea', '')
    pin = request.form.get('pin', '').strip()[:4] # Sincronizado a 4 pines
    id_dna = f"WP-26-{random.randint(1000, 9999)}" 
    
    actividad_final = f"{actividad} - {nombre_linea}" if nombre_linea else actividad

    try:
        query_db("""INSERT INTO usuarios (id_dna, nombre, cedula, telefono, pin, actividad_economica, saldo_bs, saldo_usd, saldo_wpc) 
                 VALUES (%s, %s, %s, %s, %s, %s, 0.0, 0.0, 0.0)
                 ON CONFLICT (cedula) DO UPDATE SET pin = EXCLUDED.pin, telefono = EXCLUDED.telefono, actividad_economica = EXCLUDED.actividad_economica""", 
                 (id_dna, nombre, cedula, telefono, pin, actividad_final), commit=True)
        return f"<h1>✅ ¡Bienvenido {nombre}!</h1><p>ID DNA: {id_dna}</p><a href='/acceso'>ENTRAR A MI BÓVEDA</a>"
    except Exception as e:
        return f"<h1>⚠️ Error en Registro</h1><p>{str(e)}</p><a href='/registro'>Reintentar</a>"

# --- LOGIN SEGURO ---
@app.route('/login', methods=['POST'])
def login():
    dato = request.form.get('telefono_login', '').strip()
    pin = request.form.get('pin_login', '').strip()
    user = query_db("SELECT * FROM usuarios WHERE (telefono=%s OR cedula=%s) AND pin=%s", (dato, dato, pin), one=True)
    
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))
    return "<h1>❌ Datos Incorrectos</h1><a href='/acceso'>Volver a intentar</a>"

# --- DASHBOARD Y PANEL CEO ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    m = query_db("SELECT * FROM movimientos WHERE usuario_id=%s ORDER BY id DESC LIMIT 5", (u['id'],))
    
    # Wilfredo va al Panel CEO, otros a Billetera
    if u['cedula'] == '13496133':
        return render_template('ceo_panel.html', u=u, m=m)
    return render_template('dashboard.html', u=u, m=m)

@app.route('/actualizar_ceo', methods=['POST'])
def actualizar_ceo():
    if 'user_id' not in session: return jsonify({"status": "error"}), 403
    data = request.json
    query_db(f"UPDATE usuarios SET {data['campo']} = %s WHERE id = %s", (data['valor'], session['user_id']), commit=True)
    return jsonify({"status": "ok"})

# --- INSTALACIÓN Y REPARACIÓN DE RAÍZ ---
@app.route('/instalar')
def instalar():
    query_db("DROP TABLE IF EXISTS movimientos CASCADE", commit=True)
    query_db("DROP TABLE IF EXISTS usuarios CASCADE", commit=True)
    
    # Se crean todas las columnas que los HTMLs solicitan para evitar el Error 500
    query_db("""CREATE TABLE usuarios (
        id SERIAL PRIMARY KEY, id_dna TEXT, nombre TEXT, telefono TEXT, 
        cedula TEXT UNIQUE, pin TEXT, actividad_economica TEXT, 
        banco TEXT DEFAULT 'WILL-PAY', numero_cuenta TEXT DEFAULT '0000-0000-00-0000000000',
        estatus_kyc TEXT DEFAULT 'VERIFICADO',
        saldo_bs FLOAT DEFAULT 0.0, saldo_wpc FLOAT DEFAULT 0.0, 
        saldo_usd FLOAT DEFAULT 0.0, ganancia_neta FLOAT DEFAULT 0.0,
        porcentaje_pago FLOAT DEFAULT 1.5, porcentaje_retiro FLOAT DEFAULT 2.1,
        auto_recargas BOOLEAN DEFAULT FALSE)""", commit=True)
    
    query_db("""CREATE TABLE movimientos (
        id SERIAL PRIMARY KEY, usuario_id INTEGER, 
        correlativo TEXT, monto_bs FLOAT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""", commit=True)
    
    # Registro del Fundador Wilfredo Donquiz (PIN de 4 dígitos para coincidir con el Acceso)
    query_db("""INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad_economica, saldo_bs, saldo_wpc, saldo_usd) 
        VALUES ('CEO-001', 'WILFREDO DONQUIZ', '04126602555', '13496133', '1234', 'FUNDADOR', 1000.0, 500.0, 100.0)""", commit=True)
    
    return "<h1>🏛️ Bóveda Reseteda y Blindada</h1><p>Entra con tu cédula y el PIN de 4 dígitos: 1234</p>"

if __name__ == '__main__':
    app.run(debug=True)
