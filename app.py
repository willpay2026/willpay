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
        print(f"Error: {e}")
        return None

@app.before_request
def inicializar_kyc():
    if not session.get('db_ready'):
        # Tabla extendida con campos KYC y Detalles de Negocio
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id VARCHAR(50) PRIMARY KEY, 
            nombre VARCHAR(100), 
            cedula VARCHAR(20) UNIQUE, 
            actividad VARCHAR(100), 
            nombre_negocio VARCHAR(100),
            tipo_transporte VARCHAR(50),
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00,
            estatus_kyc VARCHAR(20) DEFAULT 'PENDIENTE'
        );""", commit=True)
        session['db_ready'] = True

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = request.form.get('nombre').upper()
    c = request.form.get('cedula')
    act = request.form.get('actividad')
    negocio = request.form.get('nombre_negocio', '')
    transporte = request.form.get('tipo_transporte', '')
    
    corr = "CEO-0001-FOUNDER" if "WILFREDO" in n else f"WP-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    saldo = 5000.0 if "CEO" in corr else 0.0
    
    query_db("""INSERT INTO usuarios (id, nombre, cedula, actividad, nombre_negocio, tipo_transporte, saldo_bs) 
                VALUES (%s,%s,%s,%s,%s,%s,%s)""", 
             (corr, n, c, act, negocio, transporte, saldo), commit=True)
    
    session['u'] = corr
    return redirect('/dashboard')

# ... (Mantenemos las otras rutas de dashboard y config del chorizo anterior)
