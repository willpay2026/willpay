from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

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
    nombre_linea = request.form.get('nombre_linea') or "N/A"
    
    # LÓGICA DE INICIALES PARA EL CORRELATIVO
    prefijos = {
        'usuario': 'US', 'chofer_ind': 'TR', 'linea_transporte': 'TR', 
        'moto_taxi': 'TR', 'taxi': 'TR', 'buhonero': 'CM', 'delivery': 'SR'
    }
    prefijo = prefijos.get(actividad, 'SR')
    
    # GENERAR CORRELATIVO ÚNICO (Fecha + Hora + Prefijo)
    ahora = datetime.datetime.now()
    correlativo = f"{prefijo}-{ahora.year}{ahora.month:02d}-{ahora.strftime('%H%M%S')}"
    
    # GUARDAR EN BASE DE DATOS
    query_db("""
        INSERT INTO usuarios (id, nombre, cedula, actividad, nombre_linea, saldo_bs) 
        VALUES (%s, %s, %s, %s, %s, 0.00)
    """, (correlativo, nombre, cedula, actividad, nombre_linea), commit=True)
    
    session['u'] = correlativo
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    # Aquí es donde el QR se genera visualmente usando el correlativo
    qr_data = f"https://will-pay.render.com/pagar/{u['id']}"
    return render_template('dashboard.html', user=u, qr_data=qr_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
