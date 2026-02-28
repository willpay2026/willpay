from flask import Flask, render_template, request, redirect, session, url_for
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

# --- 🔑 EL MOTOR DE ENTRADA (Para que entres como CEO) ---
@app.route('/login', methods=['POST'])
def login():
    nombre_ingresado = request.form.get('nombre_login').upper().strip()
    # Buscamos en la bóveda si existe Wilfredo
    user = query_db("SELECT * FROM usuarios WHERE nombre LIKE %s", ('%' + nombre_ingresado + '%',), one=True)
    
    if user:
        session['user_id'] = user['id']
        return redirect('/dashboard')
    else:
        return "<h1>Acceso Denegado</h1><p>Nombre no encontrado en el emporio.</p><a href='/acceso'>Volver</a>"

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = request.form.get('nombre').upper().strip()
    t = request.form.get('telefono').strip()
    c = request.form.get('cedula').strip()
    
    u_id = "CEO-0001-FOUNDER" if "WILFREDO" in n else f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
    s_bs, s_wpc, s_usd = (100000.0, 100000.0, 1000.0) if "WILFREDO" in n else (0.0, 0.0, 0.0)
    es_ceo = True if "WILFREDO" in n else False

    try:
        query_db("""
            INSERT INTO usuarios (id_dna, nombre, telefono, cedula, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (u_id, n, t, c, s_bs, s_wpc, s_usd, es_ceo), commit=True)
        return redirect('/acceso')
    except:
        # Si ya existe, simplemente mándalo a loguearse
        return redirect('/acceso')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/acceso')
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    return render_template('dashboard.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
