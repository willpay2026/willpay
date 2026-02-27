from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = os.environ.get('DATABASE_URL')

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
        flash(f"Error de base de datos: {e}", 'danger')
        return None

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Estructura final con PIN y Tipo de Usuario
        query_db("""CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY, 
            nombre VARCHAR(100), 
            cedula_rif VARCHAR(50) UNIQUE, 
            pin VARCHAR(6), 
            tipo_usuario VARCHAR(50), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00
        );""", commit=True)
        query_db("""CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            emisor_id VARCHAR(50), 
            receptor_id VARCHAR(50), 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            referencia VARCHAR(50), 
            estatus VARCHAR(20), 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS configuracion (id INT PRIMARY KEY, p_envio DECIMAL(5,2), p_retiro DECIMAL(5,2), modo_auto BOOLEAN);", commit=True)
        query_db("INSERT INTO configuracion (id, p_envio, p_retiro, modo_auto) VALUES (1, 2.5, 3.0, FALSE) ON CONFLICT DO NOTHING", commit=True)
        session['db_ready'] = True

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        user_input = request.form.get('id', '').strip()
        pin_input = request.form.get('pin', '').strip()
        
        # Busca por Cédula/RIF o Nombre Exacto
        u = query_db("SELECT * FROM usuarios WHERE (cedula_rif=%s OR nombre=%s) AND pin=%s", 
                     (user_input, user_input, pin_input), one=True)
        if u: 
            session['u'] = u['id']
            return redirect('/dashboard')
        flash("Datos de acceso incorrectos.", 'danger')
    return render_template('acceso.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre = request.form.get('nombre').upper()
    cedula_rif = request.form.get('cedula_rif')
    pin = request.form.get('pin')
    tipo = request.form.get('tipo_usuario')
    
    if len(pin) != 6:
        flash("El PIN debe ser de 6 dígitos.", 'warning')
        return redirect('/registro')
        
    u = query_db("INSERT INTO usuarios (nombre, cedula_rif, pin, tipo_usuario) VALUES (%s, %s, %s, %s) RETURNING id", 
                 (nombre, cedula_rif, pin, tipo), one=True, commit=True)
    if u:
        session['u'] = u['id']
        return redirect('/dashboard')
    flash("Error al registrar.", 'danger')
    return redirect('/registro')

# ... (Mantenemos el resto de rutas: dashboard, pagar, config, etc.)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
