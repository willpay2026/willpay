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

@app.route('/instalar')
def instalar():
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
    return "<h1>🏛️ Bóveda Will-Pay Reiniciada con Éxito</h1>"

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    n = request.form.get('nombre').upper().strip()
    t = request.form.get('telefono').strip().replace(" ", "").replace("+58", "")
    c = request.form.get('cedula').strip()
    p = request.form.get('pin').strip()
    act = request.form.get('actividad')
    lin = request.form.get('nombre_linea') or "RUTA PRINCIPAL"
    
    if "WILFREDO" in n:
        u_id, s_bs, s_wpc, s_usd, es_ceo = "CEO-0001-FOUNDER", 100000.0, 100000.0, 1000.0, True
    else:
        u_id, s_bs, s_wpc, s_usd, es_ceo = f"US-{datetime.datetime.now().strftime('%y%m%d%H%M')}", 0.0, 0.0, 0.0, False

    try:
        query_db("""
            INSERT INTO usuarios (id_dna, nombre, telefono, cedula, pin, actividad, nombre_linea, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (u_id, n, t, c, p, act, lin, s_bs, s_wpc, s_usd, es_ceo), commit=True)
        return redirect('/acceso')
    except:
        return "<h1>Error de Datos</h1>"

@app.route('/login', methods=['POST'])
def login():
    t_in = request.form.get('telefono_login').strip().replace(" ", "").replace("+58", "")
    p_in = request.form.get('pin_login').strip()
    user = query_db("SELECT * FROM usuarios WHERE telefono=%s AND pin=%s", (t_in, p_in), one=True)
    if user:
        session['user_id'] = user['id']
        return redirect('/dashboard')
    return "<h1>Denegado</h1>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/acceso')
    user = query_db("SELECT * FROM usuarios WHERE id=%s", (session['user_id'],), one=True)
    # Pasamos el objeto 'u' completo al template detallado
    return render_template('dashboard.html', u=user)

if __name__ == '__main__':
    app.run(debug=True)
