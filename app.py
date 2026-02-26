from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# CONFIGURACIÓN DE EXPEDIENTES
BASE_DIR = "expedientes_usuarios"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute(query, args)
        if commit:
            conn.commit()
            rv = None
        else:
            rv = cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return rv

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    return render_template('acceso.html')

@app.route('/registro_kyc')
def registro_kyc():
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    actividad = request.form.get('actividad')
    telefono = request.form.get('telefono')
    nombre_linea = request.form.get('nombre_linea') or "N/A"
    
    # 1. Generar ID Correlativo
    prefijos = {'usuario': 'US', 'chofer_ind': 'TR', 'linea_transporte': 'TR', 'buhonero': 'CM'}
    prefijo = prefijos.get(actividad, 'SR')
    ahora = datetime.datetime.now()
    correlativo = f"{prefijo}-{ahora.strftime('%Y%m%d-%H%M%S')}"
    
    # 2. CREACIÓN DEL BÚNKER DE AUDITORÍA (Carpetas)
    user_path = os.path.join(BASE_DIR, correlativo)
    subcarpetas = ['KYC', 'Recibos', 'Historial_Recargas']
    
    if not os.path.exists(user_path):
        os.makedirs(user_path)
        for sub in subcarpetas:
            os.makedirs(os.path.join(user_path, sub))
            
    # 3. Crear Ficha de Apertura (Primer documento del expediente)
    with open(os.path.join(user_path, "ficha_apertura.txt"), "w") as f:
        f.write(f"EXPEDIENTE WILL-PAY GLOBAL\n")
        f.write(f"ID: {correlativo}\n")
        f.write(f"Nombre: {nombre}\n")
        f.write(f"Cédula: {cedula}\n")
        f.write(f"Actividad: {actividad}\n")
        f.write(f"Fecha de Creación: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")

    # 4. Guardar en DB
    query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, nombre_linea, saldo_bs) VALUES (%s, %s, %s, %s, %s, 0.00)", 
             (correlativo, nombre, cedula, actividad, nombre_linea), commit=True)
    
    session['u'] = correlativo
    return redirect('/ticket_bienvenida')

@app.route('/ticket_bienvenida')
def ticket_bienvenida():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('ticket_bienvenida.html', user=u)

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('dashboard.html', user=u)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
