from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor

# ESTA LÍNEA ES LA QUE BUSCA EL COMANDO GUNICORN APP:APP
app = Flask(__name__)
app.secret_key = 'willpay_legado_final_2026'

# CONEXIÓN A TU BASE DE DATOS
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(query, args)
    rv = None
    if commit:
        conn.commit()
    else:
        rv = cur.fetchone() if one else cur.fetchall()
    cur.close()
    conn.close()
    return rv

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
    <title>Will-Pay | Emporio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; text-align: center; margin: 0; }
        #splash { position: fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; transition: 0.8s; }
        .oro { color: #D4AF37; }
        .card-w { background: #111; border: 2px solid #D4AF37; border-radius: 25px; padding: 30px; margin: 20px auto; max-width: 400px; box-shadow: 0 0 20px rgba(212,175,55,0.2); }
        .btn-oro { background: #D4AF37; color: #000; font-weight: bold; border: none; border-radius: 12px; padding: 15px; width: 100%; font-size: 1.1rem; }
        input.form-control { background: #1a1a1a !important; color: white !important; border: 1px solid #333 !important; padding: 12px; }
    </style>
</head>
<body>
    <div id="splash">
        <h1 class="oro" style="letter-spacing:10px; font-weight:bold;">WILL-PAY</h1>
        <p class="text-secondary">Tecnología con corazón</p>
    </div>

    <div class="container mt-5 pt-5">
        <h2 class="oro" style="font-weight:bold;">WILL-PAY</h2>
        {% if not u %}
            <div class="card-w">
                <h4 class="mb-4">INICIAR SESIÓN</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono / Usuario" class="form-control mb-2 shadow-none" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control mb-4 shadow-none" required>
                    <button class="btn-oro">ENTRAR AL SISTEMA</button>
                </form>
            </div>
        {% else %}
            <div class="card-w">
                <p class="small text-secondary mb-1">Saldo Disponible</p>
                <h1 class="oro" style="font-size: 3rem;">Bs. {{ "%.2f"|format(u.saldo_bs) }}</h1>
                <hr class="border-secondary my-4">
                <div class="btn-group w-100">
                    <a href="/rol/pasajero" class="btn btn-dark border-warning py-3">PAGAR</a>
                    <a href="/rol/prestador" class="btn btn-dark border-warning py-3">COBRAR</a>
                </div>
                <div class="mt-4">
                    <button class="btn btn-sm btn-outline-secondary" onclick="alert('BANESCO\\n04126602555\\n13.496.133')">Ver datos de recarga</button>
                </div>
                <a href="/logout" class="btn btn-link btn-sm text-danger mt-4" style="text-decoration:none;">Cerrar Sesión</a>
            </div>
        {% endif %}
    </div>

    <script>
        setTimeout(() => { 
            const s = document.getElementById('splash');
            s.style.opacity = '0';
            setTimeout(() => { s.style.display='none'; }, 800);
        }, 2500);
    </script>
</body>
</html>
''', u=u)

@app.route('/login', methods=['POST'])
def login():
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect('/')

@app.route('/rol/<r>')
def rol(r):
    query_db("UPDATE usuarios SET rol=%s WHERE id=%s", (r, session['u']), commit=True)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run()
