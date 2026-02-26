from flask import Flask, render_template, request, redirect, session, flash, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# Base de Datos
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

# DATOS DE RECEPCIÓN (TUS DATOS PARA PAGO MÓVIL)
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

@app.route('/')
def splash(): 
    return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        user_id = request.form.get('id').strip()
        u = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
        if u:
            session['u'] = u['id']
            return redirect('/dashboard')
        return "ID Incorrecto"
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    pendientes = []
    if "CEO" in u['id']:
        pendientes = query_db("SELECT * FROM transacciones WHERE estatus='PENDIENTE' ORDER BY fecha DESC")
        
    return render_template('dashboard.html', 
                           user=u, 
                           es_ceo=("CEO" in u['id']), 
                           pendientes=pendientes,
                           banco_ce=DATOS_PAGO_MOVIL)

# --- EL OÍDO DIGITAL (API PARA EL BEEP) ---
@app.route('/api/get_balance')
def get_balance():
    if 'u' not in session: return jsonify({"error": "No login"}), 401
    u = query_db("SELECT saldo_bs FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return jsonify({"saldo": u['saldo_bs']})

# --- MOTOR DE PAGOS ---
@app.route('/enviar_pago', methods=['POST'])
def enviar_pago():
    if 'u' not in session: return redirect('/acceso')
    
    emisor_id = session['u']
    receptor_id = request.form.get('receptor_id').strip()
    monto = float(request.form.get('monto'))
    
    emisor = query_db("SELECT * FROM usuarios WHERE id=%s", (emisor_id,), one=True)
    receptor = query_db("SELECT * FROM usuarios WHERE id=%s", (receptor_id,), one=True)
    
    if not receptor: return "ERROR: Receptor no existe."
    if emisor['saldo_bs'] < monto: return "ERROR: Saldo insuficiente."
    if emisor_id == receptor_id: return "ERROR: Auto-pago no permitido."

    # Cálculo de comisiones
    comision = monto * (config_willpay['ganancia_pago'] / 100)
    monto_neto = monto - comision
    referencia = f"WP-{datetime.datetime.now().strftime('%H%M%S')}"

    # Ejecutar en BD
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (monto, emisor_id), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (monto_neto, receptor_id), commit=True)
    
    # Registrar Transacción
    query_db("INSERT INTO transacciones (emisor, receptor, monto, referencia, estatus) VALUES (%s, %s, %s, %s, 'EXITOSO')",
             (emisor_id, receptor_id, monto, referencia), commit=True)
    
    return render_template('comprobante.html', ref=referencia, monto=monto, receptor=receptor['nombre'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
