from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

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
        print(f"Error: {e}")
        return None

@app.before_request
def inicializar_sistema():
    if not session.get('db_ready'):
        # Tablas base
        query_db("CREATE TABLE IF NOT EXISTS usuarios (id VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100), cedula VARCHAR(20), actividad VARCHAR(100), saldo_bs DECIMAL(15, 2) DEFAULT 0.00);", commit=True)
        query_db("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS cedula VARCHAR(20);", commit=True)
        query_db("CREATE TABLE IF NOT EXISTS transacciones (id SERIAL PRIMARY KEY, usuario_id VARCHAR(50), tipo VARCHAR(20), monto DECIMAL(15, 2), referencia VARCHAR(50), estatus VARCHAR(20), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", commit=True)
        
        # TABLA DE CONFIGURACIÓN (EL CEREBRO DEL CEO)
        query_db("""CREATE TABLE IF NOT EXISTS configuracion (
            id INT PRIMARY KEY, 
            p_envio DECIMAL(5,2), 
            p_retiro DECIMAL(5,2), 
            modo_auto BOOLEAN
        );""", commit=True)
        
        # Valores iniciales si no existen
        query_db("INSERT INTO configuracion (id, p_envio, p_retiro, modo_auto) VALUES (1, 2.5, 3.0, FALSE) ON CONFLICT DO NOTHING", commit=True)
        session['db_ready'] = True

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    
    es_ceo = "CEO" in str(u['id'])
    pendientes = query_db("SELECT * FROM transacciones WHERE estatus='PENDIENTE' ORDER BY fecha DESC") if es_ceo else []
    
    # Ganancias totales
    res = query_db("SELECT SUM(monto * (%s/100)) as total FROM transacciones WHERE tipo='ENVIO' AND estatus='COMPLETADA'", (conf['p_envio'],), one=True)
    ganancias = res['total'] if res and res['total'] else 0

    return render_template('dashboard.html', user=u, conf=conf, es_ceo=es_ceo, pendientes=pendientes, ganancias_willpay=ganancias)

@app.route('/actualizar_config', methods=['POST'])
def actualizar_config():
    p_envio = request.form.get('p_envio')
    p_retiro = request.form.get('p_retiro')
    modo_auto = 'modo_auto' in request.form
    query_db("UPDATE configuracion SET p_envio=%s, p_retiro=%s, modo_auto=%s WHERE id=1", (p_envio, p_retiro, modo_auto), commit=True)
    return redirect('/dashboard')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    nombre, cedula, actividad = request.form.get('nombre'), request.form.get('cedula'), request.form.get('actividad')
    correlativo = "CEO-0001-FOUNDER" if "WILFREDO" in nombre.upper() else f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    saldo = 5000.00 if "CEO" in correlativo else 0.00
    query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, saldo_bs) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET cedula=EXCLUDED.cedula", (correlativo, nombre, cedula, actividad, saldo), commit=True)
    session['u'] = correlativo
    return redirect('/ticket_bienvenida')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
