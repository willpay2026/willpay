import os
import datetime
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        rv = (cur.fetchone() if one else cur.fetchall()) if not commit else None
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        print(f"Error DB: {e}")
        return None

@app.before_request
def inicializar_boveda():
    if not session.get('db_ready'):
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id VARCHAR(50) PRIMARY KEY, 
            nombre VARCHAR(100), 
            cedula VARCHAR(20) UNIQUE, 
            telefono VARCHAR(20),
            actividad VARCHAR(100), 
            nombre_negocio VARCHAR(100),
            tipo_transporte VARCHAR(50),
            banco VARCHAR(50),
            metodo_retiro VARCHAR(20),
            numero_cuenta VARCHAR(25),
            tipo_cuenta VARCHAR(20),
            tipo_titular VARCHAR(20),
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00,
            estatus_kyc VARCHAR(20) DEFAULT 'PENDIENTE'
        );""", commit=True)
        query_db("""CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            usuario_id VARCHAR(50), 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            referencia VARCHAR(50) UNIQUE, 
            estatus VARCHAR(20), 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)
        session['db_ready'] = True

@app.route('/')
def index():
    if 'u' in session: return redirect('/dashboard')
    return render_template('dashboard.html', user=None)

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    d = request.form
    n_caps = d.get('nombre', '').upper()
    corr = "CEO-0001-FOUNDER" if "WILFREDO" in n_caps else f"WP-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    
    query_db("""INSERT INTO usuarios (id, nombre, cedula, telefono, actividad, nombre_negocio, tipo_transporte, banco, metodo_retiro, numero_cuenta, tipo_cuenta, tipo_titular) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (cedula) DO NOTHING""", 
             (corr, n_caps, d.get('cedula'), d.get('telefono'), d.get('actividad'), d.get('nombre_negocio'), 
              d.get('tipo_transporte'), d.get('banco'), d.get('metodo_pago'), d.get('numero_cuenta'), 
              d.get('tipo_cuenta'), d.get('tipo_titular')), commit=True)
    
    session['u'] = corr
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('dashboard.html', user=u)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
