from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'willpay_2026_legado_wilyanny')

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    conn = None
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        rv = (cur.fetchone() if one else cur.fetchall()) if not commit else None
        cur.close()
        conn.close()
        return rv
    except Exception as e:
        print(f"Error: {e}")
        if conn: conn.close()
        return None

def preparar_sistema():
    # 1. Creamos las tablas con las mejoras (WPC, Puntos de Minería y USD)
    query_db("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id VARCHAR(50) PRIMARY KEY, 
            nombre VARCHAR(100), 
            cedula VARCHAR(20), 
            actividad VARCHAR(100), 
            saldo_bs DECIMAL(15, 2) DEFAULT 0.00,
            saldo_wpc DECIMAL(15, 2) DEFAULT 0.00,
            saldo_usd DECIMAL(15, 2) DEFAULT 0.00,
            puntos_mineria INT DEFAULT 0
        );""", commit=True)
    
    query_db("""
        CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY, 
            usuario_id VARCHAR(50), 
            tipo VARCHAR(20), 
            monto DECIMAL(15, 2), 
            moneda VARCHAR(10) DEFAULT 'BS',
            referencia VARCHAR(50), 
            estatus VARCHAR(20), 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""", commit=True)

    query_db("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id INT PRIMARY KEY, 
            p_envio DECIMAL(5,2), 
            p_retiro DECIMAL(5,2), 
            tasa_wpc DECIMAL(15,2) DEFAULT 15.50,
            modo_auto BOOLEAN
        );""", commit=True)
    
    query_db("INSERT INTO configuracion (id, p_envio, p_retiro, tasa_wpc, modo_auto) VALUES (1, 2.5, 3.0, 15.50, FALSE) ON CONFLICT DO NOTHING", commit=True)

preparar_sistema()

# --- RUTAS DE LA APP ---

@app.route('/')
def splash(): return render_template('splash.html')

@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        cedula = request.form.get('id', '').strip()
        u = query_db("SELECT * FROM usuarios WHERE cedula=%s", (cedula,), one=True)
        if u: 
            session['u'] = u['id']
            return redirect(url_for('dashboard'))
        flash("Usuario no registrado.")
    return render_template('acceso.html')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect(url_for('acceso'))
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    conf = query_db("SELECT * FROM configuracion WHERE id=1", one=True)
    es_ceo = "CEO" in str(u['id'])
    
    auditoria = query_db("SELECT * FROM transacciones ORDER BY fecha DESC LIMIT 20") if es_ceo else []
    
    return render_template('dashboard.html', user=u, conf=conf, es_ceo=es_ceo, auditoria=auditoria)

# --- MEJORA: MINERÍA SOCIAL (₩) ---
@app.route('/minar', methods=['POST'])
def minar():
    if 'u' not in session: return redirect(url_for('acceso'))
    # Sumamos 10 puntos por actividad
    query_db("UPDATE usuarios SET puntos_mineria = puntos_mineria + 10 WHERE id = %s", (session['u'],), commit=True)
    
    # Verificamos si ya puede canjear por 1 WPC (₩)
    u = query_db("SELECT puntos_mineria FROM usuarios WHERE id=%s", (session['u'],), one=True)
    if u['puntos_mineria'] >= 100:
        query_db("UPDATE usuarios SET saldo_wpc = saldo_wpc + 1, puntos_mineria = 0 WHERE id = %s", (session['u'],), commit=True)
        flash("¡BRUTAL! Has minado 1 Will-Pay Coin (₩)")
    
    return redirect(url_for('dashboard'))

# --- MEJORA: EXCHANGE (CONVERSIÓN) ---
@app.route('/convertir', methods=['POST'])
def convertir():
    monto_usd = float(request.form.get('monto_usd', 0))
    conf = query_db("SELECT tasa_wpc FROM configuracion WHERE id=1", one=True)
    u = query_db("SELECT saldo_usd FROM usuarios WHERE id=%s", (session['u'],), one=True)

    if u['saldo_usd'] >= monto_usd and monto_usd > 0:
        wpc_final = monto_usd * float(conf['tasa_wpc'])
        query_db("UPDATE usuarios SET saldo_usd = saldo_usd - %s, saldo_wpc = saldo_wpc + %s WHERE id = %s", 
                 (monto_usd, wpc_final, session['u']), commit=True)
        flash(f"Cambio Exitoso: +{wpc_final} ₩")
    else:
        flash("Saldo insuficiente en USD.")
    return redirect(url_for('dashboard'))

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n, c, a = request.form.get('nombre'), request.form.get('cedula'), request.form.get('actividad')
    if "WILFREDO" in n.upper():
        corr, s_bs, s_wpc, s_usd = "CEO-0001-FOUNDER", 10000.0, 100.0, 50.0
    else:
        corr, s_bs, s_wpc, s_usd = f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}", 0.0, 0.0, 0.0
    
    query_db("INSERT INTO usuarios (id, nombre, cedula, actividad, saldo_bs, saldo_wpc, saldo_usd) VALUES (%s,%s,%s,%s,%s,%s,%s)", 
             (corr, n, c, a, s_bs, s_wpc, s_usd), commit=True)
    session['u'] = corr
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('splash'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
