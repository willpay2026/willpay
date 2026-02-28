from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

# 1. PRIMERO DEFINIMOS LA APP (Las columnas)
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# 2. DEFINIMOS LAS RUTAS DE CARPETAS
ADN_DIGITAL = 'expedientes_willpay'
if not os.path.exists(ADN_DIGITAL):
    os.makedirs(ADN_DIGITAL)

DB_URL = os.environ.get('DATABASE_URL')

# 3. LAS FUNCIONES DE APOYO
def query_db(query, args=(), one=False, commit=False):
    # (Tu código de conexión aquí igual como lo tenías...)
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

# 4. AHORA SÍ PODEMOS USAR @app (El techo)
@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Aquí van tus CREATE TABLE que ya tenemos listos...
        # (Asegúrate de incluir los campos de saldo_wpc y saldo_usd)
        session['db_ready'] = True

# ... El resto de tus rutas (@app.route) siguen aquí abajo ...
