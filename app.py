from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN AL BÚNKER EN RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

UPLOAD_FOLDER = 'static/comprobantes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --- RUTAS DE USUARIO ---

@app.route('/')
def dashboard():
    if 'user_id' not in session:
        return "Inicia sesión para continuar" # Aquí iría tu login
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios_willpay WHERE cedula_rif = %s", (session['user_id'],))
    user = cur.fetchone()
    
    cur.execute("SELECT * FROM movimientos_willpay WHERE cedula_usuario = %s ORDER BY fecha_movimiento DESC LIMIT 10", (session['user_id'],))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', user=user, movimientos=movimientos)

@app.route('/registro_proceso', methods=['POST'])
def registro_proceso():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    telefono = request.form.get('telefono')
    banco = request.form.get('banco_pago_movil')
    telf_pm = request.form.get('telf_pago_movil')
    tipo_user = request.form.get('tipo_usuario')

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios_willpay (nombre_completo, cedula_rif, telefono, banco_pago_movil, telf_pago_movil, tipo_usuario, saldo)
            VALUES (%s, %s, %s, %s, %s, %s, 0.00)
        """, (nombre, cedula, telefono, banco, telf_pm, tipo_user))
        conn.commit()
        flash("Registro Exitoso")
    except Exception as e:
        conn.rollback()
        return f"Error: {e}"
