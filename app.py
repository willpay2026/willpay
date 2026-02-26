from flask import Flask, render_template_string, request, redirect, session, jsonify, url_for, send_from_directory
import psycopg2, os, datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# --- CARPETA PARA EXPEDIENTES ---
UPLOAD_FOLDER = 'expedientes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# CONFIGURACIÓN DE BASE DE DATOS
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

LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay | Tu Billetera Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --oro: #D4AF37; --negro: #000; }
        body { background: var(--negro); color: white; font-family: 'Segoe UI', sans-serif; text-align: center; }
        .card-will { background: #111; border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin: 20px auto; max-width: 450px; }
        .oro-text { color: var(--oro); font-weight: bold; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 12px; border: none; padding: 15px; width: 100%; text-decoration: none; display: inline-block; }
        .logo-img { width: 250px; border-radius: 15px; margin: 15px 0; }
        .input-will { background: #222 !important; color: white !important; border: 1px solid #444 !important; margin-bottom: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="container py-3">
        <img src="/logonuevo.png" class="logo-img">
        
        {% if u %}
            <div class="card-will">
                <p class="small text-secondary">Bienvenido, {{ u.nombre }}</p>
                <h2 class="oro-text">Bs. {{ "%.2f"|format(u.saldo_bs) }}</h2>
                
                <button class="btn btn-outline-warning btn-sm w-100 mb-3" data-bs-toggle="collapse" data-bs-target="#panelRecarga">
                    ➕ SOLICITAR RECARGA
                </button>

                <div class="collapse" id="panelRecarga">
                    <div class="p-3 mb-3 border border-secondary rounded" style="background: #1a1a1a;">
                        <form action="/solicitar_recarga" method="POST" enctype="multipart/form-data">
                            <input type="number" name="monto" step="0.01" class="form-control input-will" placeholder="Monto Bs." required>
                            <input type="text" name="referencia" class="form-control input-will" placeholder="Referencia" required>
                            <input type="file" name="capture" class="form-control input-will" accept="image/*" required>
                            <button type="submit" class="btn-will mt-2" style="padding: 8px;">NOTIFICAR PAGO</button>
                        </form>
                    </div>
                </div>

                <div class="btn-group w-100 my-3">
                    <a href="/cambiar_rol/pasajero" class="btn {{ 'btn-warning' if u.rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                    <a href="/cambiar_rol/prestador" class="btn {{ 'btn-warning' if u.rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
                </div>
                <hr><a href="/logout" class="text-danger small text-decoration-none">Cerrar Sesión</a>
            </div>
        {% else %}
            <div class="card-will">
                <h3 class="oro-text">Acceso Will-Pay</h3>
                <form action="/login_manual" method="POST">
                    <input type="text" name="user_id" class="form-control input-will" placeholder="Tu ID de Usuario" required>
                    <button type="submit" class="btn-will">ENTRAR AL PANEL</button>
                </form>
                <hr>
                <p class="small">¿Eres nuevo?</p>
                <button class="btn btn-outline-light w-100" data-bs-toggle="collapse" data-bs-target="#panelRegistro">CREAR CUENTA</button>
                
                <div class="collapse mt-3" id="panelRegistro">
                    <form action="/registrar" method="POST">
                        <input type="text" name="nombre" class="form-control input-will" placeholder="Nombre Completo" required>
                        <button type="submit" class="btn-will">REGISTRARME</button>
                    </form>
                </div>
            </div>
        {% endif %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

@app.route('/')
def index():
    u = None
    if 'u' in session:
        u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template_string(LAYOUT, u=u)

@app.route('/login_manual', methods=['POST'])
def login_manual():
    user_id = request.form.get('user_id')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (user_id,), one=True)
    if u:
        session['u'] = user_id
    return redirect('/')

@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form.get('nombre')
    query_db("INSERT INTO usuarios (nombre, saldo_bs, rol) VALUES (%s, 0, 'pasajero')", (nombre,), commit=True)
    return redirect('/')

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' in session:
        monto = request.form.get('monto')
        ref = request.form.get('referencia')
        file = request.files['capture']
        if file:
            user_folder = os.path.join(UPLOAD_FOLDER, str(session['u']))
            if not os.path.exists(user_folder): os.makedirs(user_folder)
            filename = secure_filename(f"REF_{ref}_{file.filename}")
            file.save(os.path.join(user_folder, filename))
    return redirect('/')

@app.route('/logonuevo.png')
def logo(): return send_from_directory(os.getcwd(), 'logonuevo.png')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
