from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_donquiz_2026'

# CONEXIÓN MAESTRA A RENDER
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a.oregon-postgres.render.com/willpay_db?sslmode=require"

UPLOAD_FOLDER = 'static/comprobantes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@app.route('/')
def dashboard():
    # Simulación de usuario en sesión (En producción usar login real)
    if 'user_id' not in session:
        session['user_id'] = '13496133' # Tu ID para pruebas
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios_willpay WHERE cedula_rif = %s", (session['user_id'],))
    user = cur.fetchone()
    
    cur.execute("SELECT * FROM movimientos_willpay WHERE cedula_usuario = %s ORDER BY fecha_movimiento DESC LIMIT 5", (session['user_id'],))
    movimientos = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', user=user, movimientos=movimientos)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    monto = request.form.get('monto')
    referencia = request.form.get('referencia')
    archivo = request.files.get('captura')
    user_id = session.get('user_id')

    conn = get_db()
    cur = conn.cursor()

    # BLOQUEO ANTI-ESTAFA: Verificar si la referencia ya existe
    cur.execute("SELECT id FROM movimientos_willpay WHERE referencia = %s", (referencia,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return "ERROR: Esta referencia ya fue utilizada en el sistema.", 403

    # Guardar Captura
    if archivo:
        filename = secure_filename(f"REC_{referencia}_{user_id}.png")
        path = os.path.join(UPLOAD_FOLDER, filename)
        archivo.save(path)
    
    # Registrar movimiento como "PENDIENTE"
    cur.execute("""
        INSERT INTO movimientos_willpay (cedula_usuario, tipo_operacion, monto, referencia, comprobante_url)
        VALUES (%s, 'Recarga Pendiente', %s, %s, %s)
    """, (user_id, monto, referencia, filename))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('dashboard'))

# RUTA PARA EL CEO (AUDITORÍA)
@app.route('/buscar_usuario')
def buscar_usuario():
    query = request.args.get('query')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios_willpay WHERE cedula_rif = %s OR telefono = %s", (query, query))
    u = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('expediente_usuario.html', u=u) if u else "No encontrado"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
