from flask import Flask, render_template, request, redirect, session, flash
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# CONFIGURACIÓN
BASE_DIR = "expedientes_usuarios"
if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

# CONTROL DE COMISIONES (Decimales soportados)
# Valores iniciales por defecto
config_willpay = {
    'ganancia_pago': 2.5,   # Ejemplo: 2.5%
    'ganancia_retiro': 3.0  # Ejemplo: 3.0%
}

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute(query, args)
        if commit: conn.commit()
        rv = cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return rv

@app.route('/')
def splash(): 
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro_kyc')
def registro_kyc():
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    actividad = request.form.get('actividad')
    ahora = datetime.datetime.now()
    
    if nombre.strip().upper() == "WILFREDO DONQUIZ":
        correlativo = "CEO-0001-FOUNDER"
    else:
        prefijo = {'usuario': 'US', 'chofer_ind': 'TR'}.get(actividad, 'SR')
        correlativo = f"{prefijo}-{ahora.strftime('%Y%m%d-%H%M%S')}"

    u_path = os.path.join(BASE_DIR, correlativo)
    if not os.path.exists(u_path):
        os.makedirs(u_path)
        for s in ['KYC', 'Recibos', 'Retiros']: os.makedirs(os.path.join(u_path, s))

    try:
        query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, saldo_bs) VALUES (%s, %s, %s, %s, 0.00)", 
                 (correlativo, nombre, cedula, actividad), commit=True)
    except: pass
    
    session['u'] = correlativo
    return redirect('/ticket_bienvenida')

@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('ticket_bienvenida.html', user=u)

# --- PANEL DE CONTROL DE COMISIONES (EL GRIFO) ---
@app.route('/actualizar_grifo', methods=['POST'])
def actualizar_grifo():
    if 'u' not in session or "CEO" not in session['u']: return redirect('/acceso')
    
    # Captura de decimales (1.3, 2.7, etc)
    config_willpay['ganancia_pago'] = float(request.form.get('g_pago'))
    config_willpay['ganancia_retiro'] = float(request.form.get('g_retiro'))
    
    return redirect('/dashboard')

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/acceso')
    monto = request.form.get('monto
