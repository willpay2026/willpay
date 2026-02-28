from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'willpay_2026_legado_wilyanny'

DB_URL = os.environ.get('DATABASE_URL')

def query_db(query, args=(), one=False, commit=False):
    conn = None
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, args)
        if commit:
            conn.commit()
            rv = None
        else:
            rv = cur.fetchone() if one else cur.fetchall()
        cur.close(); conn.close()
        return rv
    except Exception as e:
        if conn: conn.close()
        print(f"Error DB: {e}"); return None

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    # IMAGEN 1.PNG: El Splash Screen
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    # IMAGEN 2.PNG: El Panel de Entrada
    return render_template('acceso.html')

@app.route('/registro')
def registro():
    # IMAGEN 3.PNG: El Formulario de Registro
    return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = request.form.get('nombre').upper().strip()
    t = request.form.get('telefono').strip()
    c = request.form.get('cedula').strip()
    p = request.form.get('pin').strip()
    
    if "WILFREDO" in n:
        u_id_dna = "CEO-0001-FOUNDER"
        s_bs, s_wpc, s_usd = 100000.00, 100000.00, 1000.00
        soy_ceo = True
    else:
        u_id_dna = f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
        s_bs, s_wpc, s_usd = 0.00, 0.00, 0.00
        soy_ceo = False

    query_db("""
        INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (u_id_dna, n, t, c, p, s_bs, s_wpc, s_usd, soy_ceo), commit=True)
    
    user = query_db("SELECT id FROM usuarios WHERE telefono=%s", (t,), one=True)
    session['u'] = user['id']
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'u' not in session: return redirect('/acceso')
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template('dashboard.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
