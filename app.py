from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

# Forzamos a Flask a buscar en las carpetas correctas
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

# URL de tu base de datos actual
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
    # Esta es la que te daba error, ahora está blindada
    return render_template('acceso.html')

@app.route('/registro_kyc')
def registro_kyc():
    # Aquí es donde saldrá el formulario de choferes, buhoneros, etc.
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre')
    cedula = request.form.get('cedula')
    actividad = request.form.get('actividad')
    nombre_linea = request.form.get('nombre_linea') or "N/A"
    
    # Generamos el correlativo con iniciales
    prefijos = {'usuario': 'US', 'chofer_ind': 'TR', 'linea_transporte': 'TR', 'buhonero': 'CM'}
    prefijo = prefijos.get(actividad, 'SR')
    ahora = datetime.datetime.now()
    correlativo = f"{prefijo}-{ahora.strftime('%Y%m%d-%H%M%S')}"
    
    # Guardamos en la base de datos
    query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, nombre_linea, saldo_bs) VALUES (%s, %s, %s, %s, %s, 0.00)", 
             (correlativo, nombre, cedula, actividad, nombre_linea), commit=True)
    
    session['u'] = correlativo
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('dashboard.html', user=u)

# Ruta para servir el logo correctamente
@app.route('/static/logonuevo.png')
def servir_logo():
    return send_from_directory('static', 'logonuevo.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
