from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'
DB_URL = os.environ.get('DATABASE_URL')

# Función de conexión a la Bóveda (Base de Datos)
def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute(query, args)
        if commit:
            conn.commit()
            return None
        return cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()

# --- 1. RUTA DE REINICIO TOTAL (USA ESTO PRIMERO) ---
@app.route('/instalar')
def instalar():
    # Limpiamos todo para que no queden registros corruptos
    query_db("DROP TABLE IF EXISTS usuarios", commit=True)
    query_db("""
        CREATE TABLE usuarios (
            id SERIAL PRIMARY KEY,
            id_dna TEXT UNIQUE,
            nombre TEXT,
            telefono TEXT UNIQUE,
            cedula TEXT UNIQUE,
            pin TEXT,
            actividad TEXT,
            nombre_linea TEXT,
            saldo_bs FLOAT DEFAULT 0,
            saldo_wpc FLOAT DEFAULT 0,
            saldo_usd FLOAT DEFAULT 0,
            es_ceo BOOLEAN DEFAULT FALSE
        )
    """, commit=True)
    return "<h1>🏛️ Bóveda Will-Pay Reiniciada con Éxito</h1><p>Ahora ve a /registro y crea tu cuenta de CEO.</p>"

# --- 2. RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

# --- 3. PROCESO DE REGISTRO KYC ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    # Limpiamos los datos de entrada
    n = request.form.get('nombre').upper().strip()
    t = request.form.get('telefono').strip().replace(" ", "").replace("+58", "")
    c = request.form.get('cedula').strip()
    p = request.form.get('pin').strip()
    act = request.form.get('actividad')
    lin = request.form.get('nombre_linea') or "N/A"
    
    # Lógica de Fundador para Wilfredo
    if "WILFREDO" in n:
        u_id = "CEO-0001-FOUNDER"
        s_bs, s_wpc, s_usd = 100000.0, 100000.0, 1000.0
        es_ceo = True
    else:
        u_id = f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
        s_bs, s_wpc, s_usd = 0.0, 0.0, 0.0
        es_ceo = False

    try:
        query_db("""
            INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad, nombre_linea, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (u_id, n, t, c, p, act, lin, s_bs, s_wpc, s_usd, es_ceo), commit=True)
        return redirect('/acceso')
    except:
        return "<h1>Error: Estos datos ya están registrados.</h1><a href='/registro'>Volver</a>"

# --- 4. ACCESO SEGURO (MÉTODO BLINDADO) ---
@app.route('/login', methods=['POST'])
def login():
    # Solo pedimos Teléfono y PIN para evitar errores de escritura en el nombre
    t_in = request.form.get('telefono_login').strip().replace(" ", "").replace("+58", "")
    p_in = request.form.get('pin_login').strip()
    
    # Buscamos al usuario por su "llave" única (Teléfono + PIN)
    user = query_db("SELECT * FROM usuarios WHERE telefono=%s AND pin=%s", (t_in, p_in), one=True)
    
    if user:
        session['user_id'] = user['id']
        return redirect('/dashboard')
    
    return "<h1>Acceso Denegado</h1><p>Verifica que el teléfono y el PIN sean los mismos del registro.</p><a href='/acceso'>Intentar de nuevo</a>"

# --- 5. PANEL DE CONTROL (EL LEGADO) ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/acceso')
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    
    # Aquí es donde ocurre la magia que Wilfredo diseñó
    return f"""
    <html>
    <body style="background:#000; color:#D4AF37; font-family:sans-serif; text-align:center; padding:50px;">
        <img src="/static/logonuevo.png" width="150">
        <h1>BIENVENIDO, {user['nombre']}</h1>
        <hr border="1" color="#D4AF37">
        <h2>SALDO BS: {user['saldo_bs']}</h2>
        <h2>SALDO USD: {user['saldo_usd']}</h2>
        <p>ID DNA: {user['id_dna']}</p>
        <br>
        <a href="/acceso" style="color:white;">Cerrar Sesión</a>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)
