from flask import Flask, render_template, request, redirect, session, flash
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# CONFIGURACIÓN
BASE_DIR = "expedientes_usuarios"
if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

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

    # Crear Carpetas
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

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/acceso')
    monto = request.form.get('monto')
    referencia = request.form.get('referencia')
    
    # ANTI-ESTAFA: Verificar si la referencia ya existe
    existe = query_db("SELECT id FROM transacciones WHERE referencia=%s", (referencia,), one=True)
    if existe:
        return "ERROR: Esta referencia ya fue utilizada."

    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus) VALUES (%s, 'RECARGA', %s, %s, 'PENDIENTE')",
             (session['u'], monto, referencia), commit=True)
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    pendientes = []
    if "CEO" in u['id']:
        # Corregido: Si no hay tabla transacciones, esto podría fallar, pero por ahora lo dejamos listo
        try:
            pendientes = query_db("SELECT * FROM transacciones WHERE estatus='PENDIENTE'")
        except:
            pendientes = []
        
    return render_template('dashboard.html', user=u, es_ceo=("CEO" in u['id']), pendientes=pendientes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
