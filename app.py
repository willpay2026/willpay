from flask import Flask, render_template, request, redirect, session, os, datetime
import psycopg2
from psycopg2.extras import DictCursor

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
def inicializar_sistema():
    if not session.get('db_ready'):
        # Tabla Maestra con KYC y Datos Bancarios Detallados
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
        query_db("CREATE TABLE IF NOT EXISTS transacciones (id SERIAL PRIMARY KEY, usuario_id VARCHAR(50), tipo VARCHAR(20), monto DECIMAL(15, 2), referencia VARCHAR(50), estatus VARCHAR(20), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS configuracion (id INT PRIMARY KEY, p_envio DECIMAL(5,2), p_retiro DECIMAL(5,2), modo_auto BOOLEAN);", commit=True)
        query_db("INSERT INTO configuracion (id, p_envio, p_retiro, modo_auto) VALUES (1, 2.5, 3.0, FALSE) ON CONFLICT DO NOTHING", commit=True)
        session['db_ready'] = True

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    d = request.form
    n_caps = d.get('nombre').upper()
    corr = "CEO-0001-FOUNDER" if "WILFREDO" in n_caps else f"WP-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    saldo = 5000.0 if "CEO" in corr else 0.0
    
    query_db("""INSERT INTO usuarios (id, nombre, cedula, telefono, actividad, nombre_negocio, tipo_transporte, banco, metodo_retiro, numero_cuenta, tipo_cuenta, tipo_titular, saldo_bs) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
             (corr, n_caps, d.get('cedula'), d.get('telefono'), d.get('actividad'), d.get('nombre_negocio'), 
              d.get('tipo_transporte'), d.get('banco'), d.get('metodo_pago'), d.get('numero_cuenta'), 
              d.get('tipo_cuenta'), d.get('tipo_titular'), saldo), commit=True)
    
    session['u'] = corr
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    es_ceo = "CEO" in str(u['id'])
    auditoria = query_db("SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 50") if es_ceo else []
    return render_template('dashboard.html', user=u, conf=conf, es_ceo=es_ceo, auditoria=auditoria)

# ... (Rutas de actualizar_config, solicitar_recarga y aprobar_pago iguales al respaldo anterior)
