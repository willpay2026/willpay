from flask import Flask, render_template, request, redirect, session, flash, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# Base de Datos
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
        query_db("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(100),
                saldo_bs DECIMAL(15, 2) DEFAULT 0.00
            );
        """, commit=True)
        
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
        
        query_db("""
            INSERT INTO usuarios (id, nombre, saldo_bs) 
            VALUES ('13496133', 'WILFREDO DONQUIZ (CEO)', 5000.00)
            ON CONFLICT (id) DO NOTHING;
        """, commit=True)
        session['db_ready'] = True

# --- RUTAS DE NAVEGACIÓN ---

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

# ESTA ES LA RUTA QUE TE FALTABA PARA EL REGISTRO
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    user_id = request.form.get('id', '').strip()
    nombre = request.form.get('nombre', '').strip()
    
    if not user_id or not nombre:
        return "Por favor, rellena todos los campos."

    # Verificar si ya existe para evitar errores de llave primaria
    existe = query_db("SELECT id FROM usuarios WHERE id=%s", (user_id,), one=True)
    if existe:
        return "Este usuario ya existe en Will-Pay."

    # Insertar nuevo usuario
    query_db("INSERT INTO usuarios (id, nombre, saldo_bs) VALUES (%s, %s, 0.00)", 
             (user_id, nombre), commit=True)
    
    session['u'] = user_id
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    # Manejo de error si el usuario se borra de la DB pero sigue en sesión
    if not u:
        session.clear()
        return redirect('/acceso')

    pendientes = []
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
    except:
        return "Monto inválido."

    emisor = query_db("SELECT * FROM usuarios WHERE id=%s", (emisor_id,), one=True)
    receptor = query_db("SELECT * FROM usuarios WHERE id=%s", (receptor_id,), one=True)
    
    if not receptor: return "ERROR: El receptor no está registrado en Will-Pay."
    if emisor['saldo_bs'] < monto: return "ERROR: No tienes saldo suficiente."
    if emisor_id == receptor_id: return "ERROR: No puedes enviarte dinero a ti mismo."

    # Lógica de comisiones
    comision = monto * (config_willpay['ganancia_pago'] / 100)
    monto_neto = monto - comision
    referencia = f"WP-{datetime.datetime.now().strftime('%H%M%S')}"

    # Ejecución de la transacción
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, emisor_id), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto_neto, receptor_id), commit=True)
    query_db("INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus) VALUES (%s, %s, %s, %s, 'EXITOSO')",
             (emisor_id, receptor_id, monto, referencia), commit=True)
    
    return f"¡Pago realizado! Ref: {referencia}. El receptor recibió {monto_neto} Bs."

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Render usa la variable de entorno PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

