from flask import Flask, render_template, request, redirect, session, flash
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

# DATOS DE RECEPCIÓN (TUS DATOS)
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
    try:
        cur.execute(query, args)
        if commit: conn.commit()
        rv = cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return rv

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    pendientes = []
    if "CEO" in u['id']:
        try:
            pendientes = query_db("SELECT * FROM transacciones WHERE estatus='PENDIENTE' ORDER BY fecha DESC")
        except: pass
        
    return render_template('dashboard.html', 
                           user=u, 
                           es_ceo=("CEO" in u['id']), 
                           pendientes=pendientes,
                           g_pago=config_willpay['ganancia_pago'],
                           g_retiro=config_willpay['ganancia_retiro'],
                           banco_ce=DATOS_PAGO_MOVIL)

@app.route('/aprobar_pago/<int:transaccion_id>')
def aprobar_pago(transaccion_id):
    if 'u' not in session or "CEO" not in session['u']: return redirect('/acceso')
    t = query_db("SELECT * FROM transacciones WHERE id=%s", (transaccion_id,), one=True)
    if t and t['estatus'] == 'PENDIENTE':
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (t['monto'], t['usuario_id']), commit=True)
        query_db("UPDATE transacciones SET estatus = 'COMPLETADA' WHERE id = %s", (transaccion_id,), commit=True)
    return redirect('/dashboard')

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/acceso')
    monto = request.form.get('monto')
    referencia = request.form.get('referencia')
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, estatus, fecha) VALUES (%s, 'RECARGA', %s, %s, 'PENDIENTE', NOW())",
             (session['u'], monto, referencia), commit=True)
    return redirect('/dashboard')

@app.route('/solicitar_retiro', methods=['POST'])
def solicitar_retiro():
    if 'u' not in session: return redirect('/acceso')
    monto = float(request.form.get('monto'))
    datos_banco = request.form.get('datos_bancarios') # Captura los datos del usuario
    
    comision = monto * (config_willpay['ganancia_retiro'] / 100)
    total_a_pagar = monto - comision
    
    obs = f"BANCO USUARIO: {datos_banco} | A PAGAR: {total_a_pagar}"
    
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, estatus, observacion, fecha) VALUES (%s, 'RETIRO', %s, 'PENDIENTE', %s, NOW())",
             (session['u'], monto, obs), commit=True)
    return redirect('/dashboard')

# ... (El resto de rutas procesar_registro y ticket siguen igual)
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    actividad = request.form.get('actividad')
    correlativo = "CEO-0001-FOUNDER" if nombre.strip().upper() == "WILFREDO DONQUIZ" else f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    try:
        query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, saldo_bs) VALUES (%s, %s, %s, %s, 0.00)", 
                 (correlativo, nombre, cedula, actividad), commit=True)
    except: pass
    session['u'] = correlativo
    return redirect('/ticket_bienvenida')

@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('ticket_bienvenida.html', user=u)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
