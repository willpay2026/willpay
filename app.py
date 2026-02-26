from flask import Flask, render_template, request, redirect, session, flash, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
# Usamos una clave secreta consistente para las sesiones
app.secret_key = 'willpay_2026_legado_wilyanny'

# Base de Datos (Se recomienda usar variables de entorno en Render para mayor seguridad)
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

# DATOS DE RECEPCIÓN
DATOS_PAGO_MOVIL = {
    "banco": "Banesco",
    "telefono": "0412-6602555",
    "cedula": "13.496.133"
}

# CONTROL DE COMISIONES
config_willpay = {
    'ganancia_pago': 2.5,
    'ganancia_retiro': 3.0
}

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    rv = None
    try:
        cur.execute(query, args)
        if commit: 
            conn.commit()
        else:
            rv = cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return rv

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Crear tabla usuarios
        query_db("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(100),
                saldo_bs DECIMAL(15, 2) DEFAULT 0.00
            );
        """, commit=True)
        
        # Crear tabla transacciones
        query_db("""
            CREATE TABLE IF NOT EXISTS transacciones (
                id SERIAL PRIMARY KEY,
                emisor VARCHAR(50),
                receptor VARCHAR(50),
                monto DECIMAL(10, 2),
                referencia VARCHAR(20),
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estatus VARCHAR(20) DEFAULT 'PENDIENTE'
            );
        """, commit=True)
        
        # Insertar al CEO (Wilfredo)
        query_db("""
            INSERT INTO usuarios (id, nombre, saldo_bs) 
            VALUES ('13496133', 'WILFREDO DONQUIZ (CEO)', 5000.00)
            ON CONFLICT (id) DO NOTHING;
        """, commit=True)
        
        session['db_ready'] = True

@app.route('/')
def splash(): 
    return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        user_id = request.form.get('id', '').strip()
        if not user_id: return "Por favor ingresa tu cédula"
        
        u = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
        if u:
            session['u'] = u['id']
            return redirect('/dashboard')
        return "ID Incorrecto o Usuario no registrado"
    return render_template('acceso.html')

# --- NUEVA RUTA: PROCESAR REGISTRO (CORRIGE EL ERROR 404) ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nuevo_id = request.form.get('id', '').strip()
    nuevo_nombre = request.form.get('nombre', '').strip()
    
    if not nuevo_id or not nuevo_nombre:
        return "Error: Faltan datos obligatorios."

    # Verificar si ya existe
    existe = query_db("SELECT id FROM usuarios WHERE id=%s", (nuevo_id,), one=True)
    if existe:
        return "Este usuario ya está registrado. Intenta iniciar sesión."

    # Registrar nuevo usuario con saldo 0
    query_db("INSERT INTO usuarios (id, nombre, saldo_bs) VALUES (%s, %s, 0.00)", 
             (nuevo_id, nuevo_nombre), commit=True)
    
    session['u'] = nuevo_id
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    pendientes = []
    # Panel de control para el CEO
    if "13496133" in u['id']:
        pendientes = query_db("SELECT * FROM transacciones WHERE estatus='PENDIENTE' ORDER BY fecha DESC")
        
    return render_template('dashboard.html', 
                           user=u, 
                           es_ceo=("13496133" in u['id']), 
                           pendientes=pendientes,
                           banco_ce=DATOS_PAGO_MOVIL)

@app.route('/enviar_pago', methods=['POST'])
def enviar_pago():
    if 'u' not in session: return redirect('/acceso')
    
    emisor_id = session['u']
    receptor_id = request.form.get('receptor_id', '').strip()
    try:
        monto = float(request.form.get('monto', 0))
    except ValueError:
        return "Monto inválido."
    
    if monto <= 0: return "El monto debe ser mayor a cero."

    emisor = query_db("SELECT * FROM usuarios WHERE id=%s", (emisor_id,), one=True)
    receptor = query_db("SELECT * FROM usuarios WHERE id=%s", (receptor_id,), one=True)
    
    if not receptor: return "ERROR: Receptor no existe."
    if emisor['saldo_bs'] < monto: return "ERROR: Saldo insuficiente."
    if emisor_id == receptor_id: return "ERROR: Auto-pago no permitido."

    comision = monto * (config_willpay['ganancia_pago'] / 100)
    monto_neto = monto - comision
    referencia = f"WP-{datetime.datetime.now().strftime('%H%M%S')}"

    # Nota: Para máxima seguridad, estas tres operaciones deberían estar en una sola transacción SQL
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, emisor_id), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto_neto, receptor_id), commit=True)
    query_db("INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus) VALUES (%s, %s, %s, %s, 'EXITOSO')",
             (emisor_id, receptor_id, monto, referencia), commit=True)
    
    return f"¡Pago Enviado con éxito! Referencia: {referencia}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
