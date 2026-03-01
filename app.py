from flask import Flask, render_template, request, redirect, session
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_2026_legado_wilyanny'
DB_URL = os.environ.get('DATABASE_URL')

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

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

# --- REGISTRO BLINDADO ---
@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = (request.form.get('nombre') or "").upper().strip()
    t = (request.form.get('telefono') or "").strip()
    c = (request.form.get('cedula') or "").strip()
    p = (request.form.get('pin') or "123456").strip() # Si no hay PIN, ponemos 123456 por defecto
    
    u_id = "CEO-0001-FOUNDER" if "WILFREDO" in n else f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    s_bs, s_wpc, s_usd = (100000.0, 100000.0, 1000.0) if "WILFREDO" in n else (0.0, 0.0, 0.0)
    es_ceo = True if "WILFREDO" in n else False

    try:
        query_db("""
            INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (u_id, n, t, c, p, s_bs, s_wpc, s_usd, es_ceo), commit=True)
    except:
        pass # Si ya existe, no hacemos nada y lo mandamos al login
    return redirect('/acceso')

# --- LOGIN SINCRONIZADO CON TU CAPTURA ---
@app.route('/login', methods=['POST'])
def login():
    # Usamos los nombres de los campos que pusimos en el HTML abajo
    n_in = (request.form.get('nombre_login') or "").upper().strip()
    p_in = (request.form.get('pin_login') or "").strip()
    
    user = query_db("SELECT * FROM usuarios WHERE nombre LIKE %s AND pin=%s", 
                    ('%'+n_in+'%', p_in), one=True)
    
    if user:
        session['user_id'] = user['id']
        return redirect('/dashboard')
    return "<h1>Acceso Denegado</h1><p>Verifica tu Nombre y PIN.</p><a href='/acceso'>Volver</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/acceso')
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    return render_template('dashboard.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
