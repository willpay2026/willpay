from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# --- CONFIGURACIÓN DE BASE DE DATOS (NO SE TOCA) ---
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

# --- RUTAS DE NAVEGACIÓN (BLOQUE 1) ---

@app.route('/')
def splash():
    # Pantalla de 4 segundos con el logo
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    # Fachada principal de entrada
    return render_template('acceso.html')

@app.route('/registro_kyc')
def registro_kyc():
    # Próximo paso: Formulario nivel banco
    return render_template('registro.html')

@app.route('/login_manual', methods=['POST'])
def login_manual():
    uid = request.form.get('user_id')
    user = query_db("SELECT id FROM usuarios WHERE id=%s", (uid,), one=True)
    if user:
        session['u'] = uid
        return redirect('/dashboard')
    return redirect('/acceso') # Si no existe, lo devuelve al acceso

@app.route('/dashboard')
def dashboard():
    if 'u' not in session:
        return redirect('/acceso')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    # Por ahora usaremos un render provisional hasta que hagamos el Bloque 3
    return f"<h1>Bienvenido {u['nombre']}</h1><p>Saldo: Bs. {u['saldo_bs']}</p><a href='/logout'>Cerrar</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/acceso')

# --- SERVIR LOGO DESDE STATIC ---
@app.route('/logonuevo.png')
def logo():
    return send_from_directory('static', 'logonuevo.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
