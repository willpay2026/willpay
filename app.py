from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_from_directory
import psycopg2, os, datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# --- CARPETA PARA EXPEDIENTES Y CAPTURES ---
UPLOAD_FOLDER = 'expedientes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

DB_URL = os.environ.get('DATABASE_URL') # Oregón Directo

def query_db(query, args=(), one=False, commit=False):
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        if commit:
            conn.commit()
            rv = None
        else:
            rv = cur.fetchone() if one else cur.fetchall()
        cur.close(); conn.close()
        return rv
    except Exception as e:
        print(f"Error DB: {e}"); return None

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Tablas finales: Usuarios con PIN y Transacciones con Auditoría
        query_db("CREATE TABLE IF NOT EXISTS usuarios (id VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100), cedula VARCHAR(50), pin VARCHAR(6), actividad VARCHAR(50), saldo_bs DECIMAL(15, 2) DEFAULT 0.00);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS transacciones (id SERIAL PRIMARY KEY, usuario_id VARCHAR(50), tipo VARCHAR(20), monto DECIMAL(15, 2), referencia VARCHAR(50), capture_path VARCHAR(200), estatus VARCHAR(20), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/procesar_acceso', methods=['POST'])
def procesar_acceso():
    id_u = request.form.get('id').strip()
    pin = request.form.get('pin').strip()
    u = query_db("SELECT * FROM usuarios WHERE (id=%s OR cedula=%s) AND pin=%s", (id_u, id_u, pin), one=True)
    if u:
        session['u'] = u['id']
        return redirect('/dashboard')
    flash("Datos incorrectos", "danger")
    return redirect('/acceso')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre').upper()
    cedula = request.form.get('cedula')
    pin = request.form.get('pin')
    actividad = request.form.get('actividad')
    
    # Generar Correlativo Único de Will-Pay
    prefijo = {'usuario': 'US', 'chofer_ind': 'TR'}.get(actividad, 'SR')
    correlativo = f"{prefijo}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Crear Carpeta de Expediente
    u_path = os.path.join(UPLOAD_FOLDER, correlativo)
    if not os.path.exists(u_path): os.makedirs(u_path)

    query_db("INSERT INTO usuarios (id, nombre, cedula, pin, actividad) VALUES (%s,%s,%s,%s,%s)", 
             (correlativo, nombre, cedula, pin, actividad), commit=True)
    session['u'] = correlativo
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    es_ceo = "WILFREDO" in u['nombre']
    transacciones = query_db("SELECT * FROM transacciones WHERE usuario_id=%s ORDER BY fecha DESC", (session['u'],))
    return render_template('dashboard.html', user=u, es_ceo=es_ceo, transacciones=transacciones)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/acceso')
    monto = request.form.get('monto')
    ref = request.form.get('referencia')
    file = request.files['capture']
    if file:
        filename = secure_filename(f"REF_{ref}_{file.filename}")
        path = os.path.join(UPLOAD_FOLDER, session['u'], filename)
        file.save(path)
        query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, capture_path, estatus) VALUES (%s,'RECARGA', %s, %s, %s, 'PENDIENTE')",
                 (session['u'], monto, ref, path), commit=True)
    return redirect('/dashboard')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
