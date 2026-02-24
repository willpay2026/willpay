from flask import Flask, render_template_string, request, redirect, session, url_for
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_legado_original'

# TU BASE DE DATOS ORIGINAL
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

@app.route('/')
def index():
    u = None
    if 'u' in session:
        u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay | Emporio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; text-align: center; margin: 0; }
        #splash { 
            position: fixed; top:0; left:0; width:100%; height:100%; 
            background: #000; z-index: 9999; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            transition: opacity 1s;
        }
        .logo-img { width: 180px; border-radius: 50%; border: 3px solid #D4AF37; margin-bottom: 20px; }
        .oro { color: #D4AF37; font-weight: bold; }
        .card-w { background: #111; border: 1px solid #D4AF37; border-radius: 20px; padding: 25px; margin: 20px auto; max-width: 400px; }
        .btn-oro { background: #D4AF37; color: #000; font-weight: bold; border: none; border-radius: 10px; padding: 12px; width: 100%; }
        input.form-control { background: #1a1a1a !important; color: white !important; border: 1px solid #333 !important; }
    </style>
</head>
<body>
    <div id="splash">
        <img src="/static/logo%20will-pay.jpg" class="logo-img" onerror="this.src='https://via.placeholder.com/150/000000/D4AF37?text=WP'">
        <h1 class="oro">WILL-PAY</h1>
        <p class="text-secondary">Tecnología con corazón</p>
    </div>

    <div class="container mt-5 pt-5">
        <h2 class="oro">WILL-PAY</h2>
        {% if not u %}
            <div class="card-w">
                <form action="/login" method="POST">
                    <input name="t" placeholder="Usuario / Teléfono" class="form-control mb-2" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control mb-3" required>
                    <button class="btn-oro">ENTRAR AL SISTEMA</button>
                </form>
            </div>
        {% else %}
            <div class="card-w">
                <p class="small text-secondary">Bienvenido, {{ u.nombre }}</p>
                <h1 class="oro">Bs. {{ "%.2f"|format(u.saldo_bs) }}</h1>
                <hr class="border-secondary">
                <div class="btn-group w-100 mt-2">
                    <button class="btn btn-dark border-warning">PAGAR</button>
                    <button class="btn btn-dark border-warning">COBRAR</button>
                </div>
                <a href="/logout" class="btn btn-link btn-sm text-danger mt-3">Cerrar Sesión</a>
            </div>
        {% endif %}
    </div>

    <script>
        setTimeout(() => {
            const s = document.getElementById('splash');
            s.style.opacity = '0';
            setTimeout(() => { s.style.display='none'; }, 1000);
        }, 3000);
    </script>
</body>
</html>
''', u=u)

@app.route('/login', methods=['POST'])
def login():
    # USAMOS TU LÓGICA DE LOGIN ORIGINAL
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run()
