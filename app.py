from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# CONEXIÓN A BASE DE DATOS
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

# DATOS DE RECEPCIÓN
DATOS_PAGO_MOVIL = {
    "banco": "Banesco",
    "telefono": "0412-6602555",
    "cedula": "13.496.133"
}

# CONFIGURACIÓN DE COMISIONES
config_willpay = {
    'ganancia_pago': 2.5,
    'ganancia_retiro': 3.0
}

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor(cursor_factory=DictCursor)
    rv = None
    try:
        cur.execute(query, args)
        if not commit:
            rv = cur.fetchone() if one else cur.fetchall()
    except Exception as e:
        print(f"Error en query: {e}")
    finally:
        cur.close()
        conn.close()
    return rv

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Crear tabla de usuarios con todas las columnas necesarias
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id VARCHAR(50) PRIMARY KEY, 
            nombre VARCHAR(100), 
            cedula VARCHAR(20), 
            actividad VARCHAR(100), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00
        );""", commit=True)
        # Crear tabla de transacciones
        query_db("""CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            usuario_id VARCHAR(50), 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            referencia VARCHAR(50), 
            estatus VARCHAR(20), 
            observacion TEXT, 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula_ingresada = request.form.get('id', '').strip()
        # Buscamos por cédula directamente para facilitar el acceso
        u = query_db("SELECT * FROM usuarios WHERE cedula=%s", (cedula_ingresada,), one=True)
        if u:
            session['u'] = u['id']
            return redirect('/dashboard')
        return "Usuario no encontrado. Por favor regístrate."
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    if not u: return redirect('/acceso')

    es_ceo = "CEO" in u['id']
    pendientes = []
    if es_ceo:
        pendientes = query_db("SELECT * FROM transacciones WHERE estatus='PENDIENTE' ORDER BY fecha DESC")
        
    return render_template('dashboard.html', 
                           user=u, 
                           es_ceo=es_ceo, 
                           pendientes=pendientes,
                           g_pago=config_willpay['ganancia_pago'],
                           g_retiro=config_willpay['ganancia_retiro'],
                           banco_ce=DATOS_PAGO_MOVIL)

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').strip()
    cedula = request.form.get('cedula', '').strip()
    actividad = request.form.get('actividad', '').strip()
    
    # Lógica de ID especial para ti
    if "WILFREDO" in nombre.upper() and "DONQUIZ" in nombre.upper():
        correlativo = "CEO-0001-FOUNDER"
        saldo_inicial = 5000.00
    else:
        correlativo = f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
        saldo_inicial = 0.00

    query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, saldo_bs) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", 
             (correlativo, nombre, cedula, actividad, saldo_inicial), commit=True)
    
    session['u'] = correlativo
    return redirect('/ticket_bienvenida')

@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    if 'u' not in session: return redirect('/')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('ticket_bienvenida.html', user=u)

@app.route('/enviar_pago', methods=['POST'])
def enviar_pago():
    if 'u' not in session: return redirect('/acceso')
    emisor_id = session['u']
    receptor_cedula = request.form.get('receptor_id').strip()
    monto = float(request.form.get('monto'))
    
    emisor = query_db("SELECT * FROM usuarios WHERE id=%s", (emisor_id,), one=True)
    receptor = query_db("SELECT * FROM usuarios WHERE cedula=%s", (receptor_cedula,), one=True)
    
    if not receptor: return "ERROR: El receptor no existe."
    if emisor['saldo_bs'] < monto: return "ERROR: Saldo insuficiente."
    
    comision = monto * (config_willpay['ganancia_pago'] / 100)
    monto_neto = monto - comision
    ref = f"WP-{datetime.datetime.now().strftime('%H%M%S')}"

    query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, emisor_id), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto_neto, receptor['id']), commit=True)
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus, observacion) VALUES (%s, 'ENVIO', %s, %s, 'COMPLETADA', %s)",
             (emisor_id, monto, ref, f"Pago a {receptor['nombre']}"), commit=True)
    
    return render_template('comprobante.html', t={'ref': ref, 'emisor': emisor['nombre'], 'receptor': receptor['nombre'], 'monto': monto, 'fecha': datetime.datetime.now()})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
