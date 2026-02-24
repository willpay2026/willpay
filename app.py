from flask import Flask, render_template_string, request, redirect, session
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_legado_wilyanny_2026'

# CONEXIÓN A LA BASE DE DATOS
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(query, args)
    rv = None
    if commit:
        conn.commit()
    else:
        try:
            rv = cur.fetchone() if one else cur.fetchall()
        except:
            rv = None
    cur.close()
    conn.close()
    return rv

# RUTA PRINCIPAL CON PRESENTACIÓN, LOGIN Y REGISTRO
@app.route('/')
def index():
    u = None
    if 'u' in session:
        u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay | El Legado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; text-align: center; }
        #splash { position: fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; transition: 1s; }
        .logo-img { width: 150px; border-radius: 50%; border: 3px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 0 20px #D4AF37; }
        .oro { color: #D4AF37; font-weight: bold; }
        .card-w { background: #111; border: 1px solid #D4AF37; border-radius: 20px; padding: 25px; margin: 20px auto; max-width: 400px; }
        .btn-oro { background: #D4AF37; color: #000; font-weight: bold; border-radius: 10px; padding: 10px; width: 100%; border:none; }
        .legado-texto { font-size: 0.85rem; color: #aaa; font-style: italic; margin-top: 20px; padding: 10px; }
        input.form-control { background: #1a1a1a !important; color: white !important; border: 1px solid #333 !important; }
    </style>
</head>
<body>
    <div id="splash">
        <img src="/static/logo%20will-pay.jpg" class="logo-img" onerror="this.style.display='none'">
        <h1 class="oro">WILL-PAY</h1>
        <p>Tecnología con corazón para Venezuela</p>
    </div>

    <div class="container py-5">
        <h2 class="oro">WILL-PAY</h2>
        <p class="small text-secondary">La revolución del pago simple</p>

        {% if not u %}
            <div class="card-w" id="box-login">
                <h4 class="mb-3">Entrar</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control mb-2" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control mb-3" required>
                    <button class="btn-oro">INICIAR SESIÓN</button>
                </form>
                <button class="btn btn-link text-warning mt-3" onclick="showReg()">¿Eres nuevo? Regístrate aquí</button>
            </div>

            <div class="card-w" id="box-reg" style="display:none;">
                <h4 class="oro mb-3">Crear Cuenta</h4>
                <form action="/registro" method="POST">
                    <input name="id" placeholder="Teléfono" class="form-control mb-2" required>
                    <input name="nom" placeholder="Nombre Completo" class="form-control mb-2" required>
                    <input name="pin" type="password" placeholder="PIN (4 dígitos)" class="form-control mb-3" maxlength="4" required>
                    <button class="btn-oro">REGISTRARME</button>
                </form>
                <button class="btn btn-link text-secondary mt-2" onclick="showLogin()">Volver al inicio</button>
            </div>
            
            <div class="legado-texto">
                "Este sistema nace de una idea simple y un código honesto, <br>
                creado por Wilfredo Donquiz como un legado de progreso <br>
                para su única hija, Wilyanny Donquiz."
            </div>

        {% else %}
            <div class="card-w">
                <p>Bienvenido, <b class="oro">{{ u.nombre }}</b></p>
                <h1 class="oro">Bs. {{ "%.2f"|format(u.saldo_bs) }}</h1>
                <div class="btn-group w-100 mt-4">
                    <button class="btn btn-dark border-warning py-3">PAGAR</button>
                    <button class="btn btn-dark border-warning py-3">COBRAR</button>
                </div>
                <a href="/logout" class="btn btn-link text-danger mt-4 text-decoration-none">Cerrar Sesión</a>
            </div>
        {% endif %}
    </div>

    <script>
        setTimeout(() => { 
            const s = document.getElementById('splash');
            if(s) {
                s.style.opacity='0';
                setTimeout(() => s.style.display='none', 1000);
            }
        }, 3000);

        function showReg() { 
            document.getElementById('box-login').style.display='none';
            document.getElementById('box-reg').style.display='block';
        }
        function showLogin() { 
            document.getElementById('box-login').style.display='block';
            document.getElementById('box-reg').style.display='none';
        }
    </script>
</body>
</html>
''', u=u)

@app.route('/login', methods=['POST'])
def login():
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect('/')

@app.route('/registro', methods=['POST'])
def registro():
    query_db("INSERT INTO usuarios (id, nombre, pin, saldo_bs, rol) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
             (request.form['id'], request.form['nom'], request.form['pin'], 0.00, 'pasajero'), commit=True)
    session['u'] = request.form['id']
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run()
