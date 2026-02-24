from flask import Flask, render_template_string, request, redirect, session
import psycopg2, os
from psycopg2.extras import DictCursor

# CONFIGURACIÓN DEL MOTOR
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

# CREACIÓN AUTOMÁTICA DEL ADMINISTRADOR (WILFREDO)
@app.before_request
def inicializar_sistema():
    query_db("""
        INSERT INTO usuarios (id, nombre, pin, saldo_bs, rol) 
        VALUES (%s, %s, %s, %s, %s) 
        ON CONFLICT (id) DO NOTHING
    """, ('admin', 'Wilfredo Donquiz', '1234', 100.00, 'prestador'), commit=True)

# --- VISTA PRINCIPAL (DISEÑO Y PRESENTACIÓN) ---
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Revolución de Pagos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #fff; font-family: 'Trebuchet MS', sans-serif; margin: 0; overflow: hidden; }
        
        /* PANTALLA DE PRESENTACIÓN (SPLASH) */
        #splash { 
            position: fixed; top:0; left:0; width:100%; height:100%; 
            background: #000; z-index: 10000; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            transition: opacity 1.2s ease-in-out;
        }
        .logo-grande { 
            width: 220px; height: 220px; 
            border-radius: 50%; border: 4px solid #D4AF37;
            box-shadow: 0 0 40px rgba(212, 175, 55, 0.6);
            animation: latido 2.5s infinite;
        }
        @keyframes latido { 
            0% { transform: scale(1); opacity: 0.8; } 
            50% { transform: scale(1.05); opacity: 1; } 
            100% { transform: scale(1); opacity: 0.8; } 
        }
        
        .oro { color: #D4AF37; font-weight: bold; letter-spacing: 6px; margin-top: 25px; text-transform: uppercase; }
        .subtitulo { color: #888; font-size: 0.9rem; margin-top: 5px; }

        /* CONTENIDO PRINCIPAL */
        #main-content { opacity: 0; transition: opacity 1.5s; padding-top: 60px; }
        .card-w { 
            background: #111; border: 1px solid #D4AF37; border-radius: 25px; 
            padding: 35px; max-width: 420px; margin: auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .btn-oro { 
            background: linear-gradient(145deg, #D4AF37, #B8860B); 
            color: #000; font-weight: bold; border-radius: 12px; 
            padding: 15px; width: 100%; border: none; font-size: 1.1rem;
            text-transform: uppercase;
        }
        input.form-control { 
            background: #1a1a1a !important; color: white !important; 
            border: 1px solid #333 !important; padding: 15px; margin-bottom: 15px;
            border-radius: 10px;
        }
    </style>
</head>
<body>

    <div id="splash">
        <img src="/static/logo%20will-pay.jpg" class="logo-grande" alt="Escudo Will-Pay">
        <h1 class="oro">WILL-PAY</h1>
        <p class="subtitulo">Tecnología con corazón, pensada para Venezuela</p>
    </div>

    <div id="main-content" class="container">
        <h2 class="oro text-center mb-4" style="font-size: 1.5rem;">WILL-PAY</h2>
        
        {% if not u %}
            <div class="card-w">
                <h4 class="text-center mb-4" style="color: #eee;">BIENVENIDO</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Usuario / Teléfono" class="form-control shadow-none" required>
                    <input name="p" type="password" placeholder="PIN de Seguridad" class="form-control shadow-none" required>
                    <button class="btn-oro">ENTRAR AL SISTEMA</button>
                </form>
            </div>
        {% else %}
            <div class="card-w text-center">
                <p class="small text-secondary mb-1">Panel de Control</p>
                <h4 class="mb-4">{{ u.nombre }}</h4>
                <p class="text-secondary small mb-0">Saldo Disponible</p>
                <h1 class="oro" style="font-size: 3rem;">Bs. {{ "%.2f"|format(u.saldo_bs) }}</h1>
                
                <div class="d-grid gap-2 mt-4">
                    <button class="btn btn-outline-warning btn-lg py-3" style="border-radius:15px;">PAGAR</button>
                    <button class="btn btn-dark border-warning btn-lg py-3" style="border-radius:15px;">COBRAR</button>
                </div>
                
                <div class="mt-4">
                    <a href="/logout" class="btn btn-link text-danger text-decoration-none">Cerrar Sesión Segura</a>
                </div>
            </div>
        {% endif %}
    </div>

    <script>
        window.onload = function() {
            setTimeout(() => {
                const splash = document.getElementById('splash');
                const content = document.getElementById('main-content');
                splash.style.opacity = '0';
                content.style.opacity = '1';
                document.body.style.overflow = 'auto';
                setTimeout(() => { splash.style.display = 'none'; }, 1200);
            }, 3500); 
        };
    </script>
</body>
</html>
''', u=u)

# --- RUTAS DE CONTROL ---
@app.route('/login', methods=['POST'])
def login():
    usuario_id = request.form['t']
    pin = request.form['p']
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (usuario_id, pin), one=True)
    if res:
        session['u'] = res['id']
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Esto es para pruebas locales, Render usa gunicorn
    app.run()
