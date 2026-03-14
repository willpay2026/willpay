from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, psycopg2, datetime, qrcode, io, base64
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026_legacy'

# --- CONEXIÓN A LA BASE DE DATOS ---
def get_db():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

# --- REPARACIÓN AUTOMÁTICA Y CARGA DE DATOS (PARA QUE NO SE JODA NADA) ---
@app.route('/inyectar_datos')
def inyectar_datos():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, nombre VARCHAR(100), cedula VARCHAR(20) UNIQUE,
                password VARCHAR(20), saldo DECIMAL(12,2) DEFAULT 0.00, rol VARCHAR(20) DEFAULT 'CLIENTE'
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transacciones (
                id SERIAL PRIMARY KEY, emisor VARCHAR(20), receptor VARCHAR(20),
                monto DECIMAL(12,2), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referencia VARCHAR(20), estatus VARCHAR(20) DEFAULT 'EXITOSO', tipo VARCHAR(20) DEFAULT 'EGRESO'
            );
        """)
        # Reparación de columnas por si acaso
        cur.execute("ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'EGRESO';")
        cur.execute("ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS estatus VARCHAR(20) DEFAULT 'EXITOSO';")
        cur.execute("ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS referencia VARCHAR(20);")
        conn.commit()
        return "✅ Búnker Actualizado. Ve al /"
    except Exception as e:
        return f"Error: {e}"
    finally:
        cur.close(); conn.close()

# --- RUTAS DE FLUJO (SPLASH -> ACCESO -> DASHBOARD) ---

@app.route('/')
def splash():
    # Esta ruta carga tu Splash serio
    return render_template('auth/splash.html')

@app.route('/acceso')
def acceso():
    # Esta ruta carga tu Login serio
    return render_template('auth/acceso.html')

@app.route('/login', methods=['POST'])
def login():
    cedula = request.form.get('cedula'); pin = request.form.get('pin')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE cedula = %s AND password = %s", (cedula, pin))
    user = cur.fetchone(); cur.close(); conn.close()
    if user:
        session['user_id'] = user['id']; session['cedula'] = user['cedula']
        return redirect(url_for('dashboard'))
    return "Credenciales incorrectas."

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('acceso'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    # Historial de 10 movimientos
    cur.execute("""
        SELECT fecha, referencia, monto, estatus, tipo FROM transacciones 
        WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 10
    """, (user['cedula'], user['cedula']))
    movimientos = cur.fetchall(); cur.close(); conn.close()
    return render_template('user/dashboard.html', u=user, movimientos=movimientos)

# --- SISTEMA DE PAGOS CON QR DINÁMICO ---

@app.route('/pagar')
def pagar():
    # Carga el escáner de cámara para pagar
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/pagar_camara.html')

@app.route('/cobrar')
def cobrar():
    # Carga la pantalla para generar el QR de cobro
    if 'user_id' not in session: return redirect(url_for('acceso'))
    return render_template('user/cobrar_qr.html', cedula=session['cedula'])

@app.route('/generar_qr_dinamico', methods=['POST'])
def generar_qr_dinamico():
    # Genera la imagen QR con los datos: emisor|monto
    if 'user_id' not in session: return jsonify({'status': 'error'})
    monto = request.form.get('monto')
    receptor_ced = session['cedula']
    datos_qr = f"{receptor_ced}|{monto}"
    img = qrcode.make(datos_qr)
    buf = io.BytesIO(); img.save(buf)
    image_stream = base64.b64encode(buf.getvalue()).decode('utf-8')
    return jsonify({'status': 'ok', 'qr_image': image_stream})

@app.route('/procesar_pago_qr', methods=['POST'])
def procesar_pago_qr():
    # Procesa el pago escaneado y redirige al comprobante
    if 'user_id' not in session: return redirect(url_for('acceso'))
    datos_scanned = request.form.get('datos_scanned') # emisor|monto
    receptor_ced, monto = datos_scanned.split('|')
    monto = float(monto)
    emisor_ced = session['cedula']
    referencia = f"WP{datetime.datetime.now().strftime('%M%S%f')[:6]}"
    conn = get_db(); cur = conn.cursor()
    try:
        # Lógica de saldos y registros (como antes)
        cur.execute("UPDATE users SET saldo = saldo - %s WHERE cedula = %s AND saldo >= %s", (monto, emisor_ced, monto))
        cur.execute("UPDATE users SET saldo = saldo + %s WHERE cedula = %s", (monto, receptor_ced))
        cur.execute("INSERT INTO transacciones (emisor, receptor, monto, referencia) VALUES (%s, %s, %s, %s)", (emisor_ced, receptor_ced, monto
