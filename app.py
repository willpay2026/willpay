from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# --- BLOQUE ADN DIGITAL (CREACIÓN DE EXPEDIENTES) ---
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

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Actualizado con CEDULA para el ADN Digital
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY, 
            nombre VARCHAR(100), 
            telefono VARCHAR(20) UNIQUE, 
            cedula VARCHAR(50),
            pin VARCHAR(6), 
            tipo_usuario VARCHAR(50), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00
        );""", commit=True)
        query_db("""CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            usuario_id INT, 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            referencia VARCHAR(50), 
            capture_path VARCHAR(255),
            estatus VARCHAR(20) DEFAULT 'PENDIENTE', 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/procesar_acceso', methods=['POST'])
def procesar_acceso():
    nombre = request.form.get('nombre', '').strip().upper()
    tel = request.form.get('telefono', '').strip()
    pin = request.form.get('pin', '').strip()
    
    u = query_db("SELECT * FROM usuarios WHERE nombre=%s AND telefono=%s AND pin=%s", 
                 (nombre, tel, pin), one=True)
    if u:
        session['u'] = u['id']
        return redirect('/dashboard')
    flash("Datos incorrectos. Verifique Nombre, Teléfono y PIN.", "danger")
    return redirect('/acceso')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = request.form.get('nombre').upper()
    t = request.form.get('telefono')
    c = request.form.get('cedula') # Nuevo campo necesario para expediente
    p = request.form.get('pin')
    tipo = request.form.get('tipo_usuario')
    
    # Registro en DB
    query_db("INSERT INTO usuarios (nombre, telefono, cedula, pin, tipo_usuario) VALUES (%s,%s,%s,%s,%s)", 
             (n, t, c, p, tipo), commit=True)
    u = query_db("SELECT id FROM usuarios WHERE telefono=%s", (t,), one=True)
    
    # GENERACIÓN DE CARPETAS DE ADN DIGITAL
    user_folder = os.path.join(ADN_DIGITAL, f"USER_{u['id']}_{t}")
    subcarpetas = ['documentos', 'recargas', 'comprobantes_pago', 'retiros']
    for sub in subcarpetas:
        os.makedirs(os.path.join(user_folder, sub), exist_ok=True)
        
    session['u'] = u['id']
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    es_ceo = "WILFREDO" in u['nombre']
    trans = query_db("SELECT * FROM transacciones WHERE usuario_id=%s ORDER BY fecha DESC LIMIT 5", (session['u'],))
    res = query_db("SELECT SUM(monto * 0.02) as ganancia FROM transacciones WHERE estatus='EXITOSO'", one=True)
    ganancias = res['ganancia'] if res and res['ganancia'] else 0
    return render_template('dashboard.html', user=u, es_ceo=es_ceo, transacciones=trans, ganancias=ganancias)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/acceso')
    monto = request.form.get('monto')
    ref = request.form.get('referencia')
    file = request.files.get('comprobante')
    if file:
        u = query_db("SELECT telefono FROM usuarios WHERE id=%s", (session['u'],), one=True)
        filename = secure_filename(f"REF_{ref}_{file.filename}")
        path = os.path.join(ADN_DIGITAL, f"USER_{session['u']}_{u['telefono']}", 'recargas', filename)
        file.save(path)
        query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, capture_path, estatus) VALUES (%s,'RECARGA', %s, %s, %s, 'PENDIENTE')",
                 (session['u'], monto, ref, path), commit=True)
    return redirect('/dashboard')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
