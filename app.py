from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_from_directory
import psycopg2, os, datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# --- CONFIGURACIÓN DE CARPETAS ---
UPLOAD_FOLDER = 'expedientes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# URL de Oregón desde las variables de entorno de Render
DB_URL = os.environ.get('DATABASE_URL')

def query_db(query, args=(), one=False, commit=False):
    conn = None
    try:
        # Añadimos sslmode para seguridad con Oregón
        conn = psycopg2.connect(DB_URL, sslmode='require')
        # Isolation level para asegurar que los commits se guarden de una
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        
        if commit:
            rv = None
        else:
            rv = cur.fetchone() if one else cur.fetchall()
            
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        if conn: conn.close()
        print(f"Error crítico en DB: {e}")
        return None

@app.before_request
def inicializar_sistema():
    # Evitamos que se ejecute en cada click, solo una vez por sesión de servidor
    if not getattr(app, 'db_iniciada', False):
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id VARCHAR(50) PRIMARY KEY, 
            nombre VARCHAR(100), 
            cedula VARCHAR(50), 
            pin VARCHAR(6), 
            actividad VARCHAR(50), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00
        );""", commit=True)
        
        query_db("""CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            usuario_id VARCHAR(50), 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            referencia VARCHAR(50), 
            capture_path VARCHAR(200), 
            estatus VARCHAR(20), 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)
        app.db_iniciada = True

@app.route('/')
def splash(): 
    return render_template('splash.html')

@app.route('/acceso')
def acceso(): 
    return render_template('acceso.html')

@app.route('/procesar_acceso', methods=['POST'])
def procesar_acceso():
    id_u = request.form.get('id', '').strip()
    pin = request.form.get('pin', '').strip()
    # Buscamos por ID (Correlativo) o Cédula
    u = query_db("SELECT * FROM usuarios WHERE (id=%s OR cedula=%s) AND pin=%s", (id_u, id_u, pin), one=True)
    if u:
        session['u'] = u['id']
        return redirect('/dashboard')
    flash("Datos incorrectos o PIN inválido", "danger")
    return redirect('/acceso')

@app.route('/registro')
def registro(): 
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre', '').upper()
    cedula = request.form.get('cedula', '').strip()
    pin = request.form.get('pin', '').strip()
    actividad = request.form.get('actividad', 'usuario')
    
    if len(pin) != 6:
        flash("El PIN debe ser de 6 dígitos", "warning")
        return redirect('/registro')
    
    # Generar Correlativo único
    prefijo = {'usuario': 'US', 'chofer_ind': 'TR', 'juridico': 'JR'}.get(actividad, 'SR')
    correlativo = f"{prefijo}-{datetime.datetime.now().strftime('%y%m%d%H%M%S')}"
    
    # Crear carpeta de expediente local
    u_path = os.path.join(UPLOAD_FOLDER, correlativo)
    if not os.path.exists(u_path): 
        os.makedirs(u_path)

    success = query_db("INSERT INTO usuarios (id, nombre, cedula, pin, actividad) VALUES (%s,%s,%s,%s,%s)", 
             (correlativo, nombre, cedula, pin, actividad), commit=True)
    
    session['u'] = correlativo
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: 
        return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    if not u:
        session.clear()
        return redirect('/acceso')
        
    es_ceo = "WILFREDO" in u['nombre']
    # Si es CEO ve todo, si no solo lo suyo
    if es_ceo:
        transacciones = query_db("SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 10")
    else:
        transacciones = query_db("SELECT * FROM transacciones WHERE usuario_id=%s ORDER BY fecha DESC", (session['u'],))
        
    return render_template('dashboard.html', user=u, es_ceo=es_ceo, transacciones=transacciones)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/acceso')
    monto = request.form.get('monto')
    ref = request.form.get('referencia')
    file = request.files.get('capture')
    
    path = ""
    if file:
        filename = secure_filename(f"REF_{ref}_{file.filename}")
        u_path = os.path.join(UPLOAD_FOLDER, session['u'])
        if not os.path.exists(u_path): os.makedirs(u_path)
        path = os.path.join(u_path, filename)
        file.save(path)
        
    query_db("INSERT INTO transacciones (usuario_id, tipo, monto, referencia, capture_path, estatus) VALUES (%s,'RECARGA', %s, %s, %s, 'PENDIENTE')",
             (session['u'], monto, ref, path), commit=True)
    
    flash("Recarga enviada a revisión", "success")
    return redirect('/dashboard')

@app.route('/logout')
def logout(): 
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # IMPORTANTE: Port dinámico para evitar el 502 en Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
