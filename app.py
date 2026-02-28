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

# --- RUTA DE AUTO-INSTALACIÓN (Dale clic a esto primero) ---
@app.route('/instalar')
def instalar():
    query_db("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            id_dna TEXT UNIQUE,
            nombre TEXT,
            telefono TEXT UNIQUE,
            cedula TEXT UNIQUE,
            saldo_bs FLOAT DEFAULT 0,
            saldo_wpc FLOAT DEFAULT 0,
            saldo_usd FLOAT DEFAULT 0,
            es_ceo BOOLEAN DEFAULT FALSE,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """, commit=True)
    return "Bóveda instalada con éxito. Ya puedes registrarte."

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/acceso')
def acceso(): return render_template('acceso.html')

@app.route('/registro')
def registro(): return render_template('registro.html')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    # El código ahora reconoce "WILFREDO DONQUIZ" como el CEO
    n = request.form.get('nombre').upper().strip()
    t = request.form.get('telefono').strip()
    c = request.form.get('cedula').strip()
    
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
            INSERT INTO usuarios (id_dna, nombre, telefono, cedula, saldo_bs, saldo_wpc, saldo_usd, es_ceo) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (u_id, n, t, c, s_bs, s_wpc, s_usd, es_ceo), commit=True)
        return f"¡Felicidades {n}! Tu legado ha comenzado. ID: {u_id}"
    except Exception as e:
        return f"Error: Ya existe un registro con esos datos."

if __name__ == '__main__':
    app.run(debug=True)
