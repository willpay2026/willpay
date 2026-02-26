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

# CONTROL DE COMISIONES (Decimales soportados)
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

# --- MOTOR DE PAGOS ENTRE USUARIOS ---
@app.route('/enviar_pago', methods=['POST'])
def enviar_pago():
    if 'u' not in session: return redirect('/acceso')
    
    emisor_id = session['u']
    receptor_id = request.form.get('receptor_id').strip()
    monto = float(request.form.get('monto'))
    
    emisor = query_db("SELECT * FROM usuarios WHERE id=%s", (emisor_id,), one=True)
    receptor = query_db("SELECT * FROM usuarios WHERE id=%s", (receptor_id,), one=True)
    
    if not receptor:
        return "ERROR: El ID del receptor no existe."
    if emisor['saldo_bs'] < monto:
        return "ERROR: Saldo insuficiente."
    if emisor_id == receptor_id:
        return "ERROR: No puedes enviarte a ti mismo."

    # Cálculo de comisión Will-Pay
    comision = monto * (config_willpay['ganancia_pago'] / 100)
    monto_neto = monto - comision

    # Ejecutar transferencia
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, emisor_id), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto_neto, receptor_id), commit=True)
    
    ref = f"WP-{datetime.datetime.now().strftime('%H%M%S')}"
