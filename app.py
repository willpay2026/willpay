from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# Conexión Directa a la Base de Datos de Wilfredo
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        rv = None
        cur.execute(query, args)
        if not commit:
            rv = cur.fetchone() if one else cur.fetchall()
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        print(f"Error en BD: {e}")
        return None

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Creación de Tablas de Wilfredo (Will-Pay)
        query_db("CREATE TABLE IF NOT EXISTS usuarios (id VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100), cedula VARCHAR(20), actividad VARCHAR(100), saldo_bs DECIMAL(15, 2) DEFAULT 0.00);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS transacciones (id SERIAL PRIMARY KEY, usuario_id VARCHAR(50), tipo VARCHAR(20), monto DECIMAL(15, 2), referencia VARCHAR(50), estatus VARCHAR(20), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS configuracion (id INT PRIMARY KEY, p_envio DECIMAL(5,2), p_retiro DECIMAL(5,2), modo_auto BOOLEAN);", commit=True)
        
        # Inyección de ADN Multimoneda (WPC y USD)
        try:
            query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS saldo_wpc DECIMAL(15, 2) DEFAULT 0.00;", commit=True)
            query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS saldo_usd DECIMAL(15, 2) DEFAULT 0.00;", commit=True)
            query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS puntos_mineria INT DEFAULT 0;", commit=True)
            query_db("ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS tasa_wpc DECIMAL(15, 2) DEFAULT 15.50;", commit=True)
        except: pass

        query_db("INSERT INTO configuracion (id, p_envio, p_retiro, modo_auto, tasa_wpc) VALUES (1, 2.5, 3.0, FALSE, 15.50) ON CONFLICT DO NOTHING", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula = request.form.get('id', '').strip()
        u = query_db("SELECT * FROM usuarios WHERE cedula=%s", (cedula,), one=True)
