from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

# 1. INICIALIZACIÓN
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

ADN_DIGITAL = 'expedientes_willpay'
if not os.path.exists(ADN_DIGITAL):
    os.makedirs(ADN_DIGITAL)

DB_URL = os.environ.get('DATABASE_URL')

def query_db(query, args=(), one=False, commit=False):
    conn = None
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        if commit:
            rv = None
        else:
            rv = cur.fetchone() if one else cur.fetchall()
        cur.close(); conn.close()
        return rv
    except Exception as e:
        if conn: conn.close()
        print(f"Error DB: {e}"); return None

# 2. RUTAS DE ACCESO (La Puerta Principal)
@app.route('/')
def index():
    # Esta ruta elimina el error 404 al abrir la app
    return render_template('splash.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session:
        return redirect('/')
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('dashboard.html', user=user)

# 3. CONFIGURACIÓN DE TABLAS
@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY, 
            id_dna VARCHAR(50) UNIQUE,
            nombre VARCHAR(100), 
            telefono VARCHAR(20) UNIQUE, 
            cedula VARCHAR(50),
            pin VARCHAR(6), 
            tipo_usuario VARCHAR(50), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00,
            saldo_wpc DECIMAL(15, 2) DEFAULT 0.00,
            saldo_usd DECIMAL(15, 2) DEFAULT 0.00,
            es_socio BOOLEAN DEFAULT FALSE,
            es_ceo BOOLEAN DEFAULT FALSE
        );""", commit=True)
        session['db_ready'] = True

# 4. PROCESAMIENTO CON PODER DE CEO
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = request.form.get('nombre').upper().strip()
    t = request.form.get('telefono').strip()
    c = request.form.get('cedula').strip()
    p = request.form.get('pin').strip()
    tipo = request.form.get('tipo_usuario')
    
    if "WILFREDO" in n:
        u_id_dna = "CEO-0001-FOUNDER"
        s_bs, s_wpc, s_usd = 100000.00, 100000.00, 1000.00
        soy_ceo = True
    else:
        u_id_dna = f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
        s_bs, s_wpc, s_usd = 0.00, 0.00, 0.00
        soy_ceo = False

    query_db("""
        INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, tipo_usuario, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (u_id_dna, n, t, c, p, tipo, s_bs, s_wpc, s_usd, soy_ceo), commit=True)
    
    u = query_db("SELECT id FROM usuarios WHERE telefono=%s", (t,), one=True)
    user_folder = os.path.join(ADN_DIGITAL, f"{u_id_dna}_{t}")
    for sub in ['documentos', 'recargas', 'comprobantes_pago', 'retiros']:
        os.makedirs(os.path.join(user_folder, sub), exist_ok=True)
        
    session['u'] = u['id']
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
