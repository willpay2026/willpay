from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'willpay_ultra_key_2026'

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- PLANTILLA ÚNICA (CSS ESTILO WILL-PAY) ---
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay PRO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background-color: #000; color: #fff; font-family: sans-serif; }
        .will-card { background: #111; border: 2px solid #d4af37; border-radius: 20px; padding: 20px; max-width: 400px; margin: 20px auto; text-align: center; }
        .gold-text { color: #d4af37; font-weight: bold; }
        .btn-will { background: #d4af37; color: #000; font-weight: bold; border-radius: 10px; border: none; padding: 10px; width: 100%; }
        .saldo-box { font-size: 2.2rem; color: #d4af37; font-weight: bold; margin: 15px 0; }
        .admin-section { background: #1a1a1a; border: 1px dashed #d4af37; border-radius: 15px; padding: 15px; margin-top: 20px; }
        input { background: #222 !important; color: #fff !important; border: 1px solid #444 !important; }
    </style>
</head>
<body>
    <div class="container text-center mt-3">
        <h2 class="gold-text">WILL-PAY <span class="badge bg-warning text-dark" style="font-size:0.5em">SQL PRO</span></h2>
        {% if session.get('u') %}
            <p class="small text-muted">Hola, {{ u_nom }}</p>
        {% endif %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

# --- RUTAS ---
@app.route('/')
def index():
    if 'u' not in session:
        return render_template_string(BASE_HTML + '''
        {% block content %}
        <div class="will-card mt-5">
            <h4 class="gold-text">Bienvenido</h4>
            <a href="/login_view" class="btn-will d-block mb-3 text-decoration-none">INICIAR SESIÓN</a>
            <a href="/registro_view" class="btn btn-outline-light w-100">CREAR CUENTA</a>
        </div>
        {% endblock %}
        ''')
    
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, nombre, saldo_bs, rol FROM usuarios WHERE id = %s", (session['u'],))
    user = cur.fetchone()
    
    # Obtener comisiones si es admin
    comisiones = 0
    if user[0] == 'admin':
        cur.execute("SELECT saldo_bs FROM usuarios WHERE id = 'SISTEMA_GANANCIAS'")
        res_com = cur.fetchone()
        comisiones = res_com[0] if res_com else 0

    cur.execute("SELECT receptor, monto, fecha FROM historial WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 3", (user[0], user[0]))
    movs = cur.fetchall()
    cur.close(); conn.close()

    return render_template_string(BASE_HTML + '''
    {% block content %}
    <div class="will-card">
        <div class="small">Mi Saldo</div>
        <div class="saldo-box">Bs. {{ "%.2f"|format(user[2]) }}</div>
        
        <div class="btn-group w-100 mb-3">
            <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if user[3] == 'pasajero' else 'btn-dark' }}">PAGAR</a>
            <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if user[3] == 'prestador' else 'btn-dark' }}">COBRAR</a>
        </div>

        {% if user[3] == 'pasajero' %}
            <div class="bg-white p-2 d-inline-block rounded-3 mb-2">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WP|{{user[0]}}|10">
            </div>
            <p class="small text-muted">Muestra este código (10.00 Bs.)</p>
        {% else %}
            <button class="btn-will py-3" onclick="startScan()">📷 ESCANEAR QR</button>
            <video id="video" style="width:100%; display:none; margin-top:10px; border-radius:10px;"></video>
        {% endif %}

        {% if user[0] == 'admin' %}
        <div class="admin-section">
            <p class="gold-text mb-1">💼 ADMIN: Bs. {{ "%.2f"|format(coms) }}</p>
            <form action="/recargar" method="POST">
                <input name="t" placeholder="Teléfono" class="form-control form-control-sm mb-2" required>
                <input name="m" type="number" step="0.01" placeholder="Monto" class="form-control form-control-sm mb-2" required>
                <button class="btn btn-danger btn-sm w-100">EFECTUAR RECARGA</button>
            </form>
        </div>
        {% endif %}

        <div class="mt-4 text-start">
            <p class="small gold-text mb-1">MOVIMIENTOS:</p>
            {% for m in movs %}
                <div style="font-size:0.75rem; border-bottom:1px solid #333; padding:4px 0;">
                    {{ m[0] }} | <span class="text-success">+{{ m[1] }} Bs.</span>
                </div>
            {% endfor %}
        </div>
        
        <a href="/logout" class="text-danger small d-block mt-4 text-decoration-none">Cerrar Sesión</a>
    </div>

    <script>
        function startScan() {
            const v = document.getElementById('video');
            v.style.display = 'block';
            const reader = new ZXing.BrowserQRCodeReader();
            reader.decodeFromVideoDevice(null, 'video', (res) => {
                if (res) {
                    const data = res.text.split('|');
                    if(confirm("¿Cobrar " + data[2] + " Bs a " + data[1] + "?")) {
                        window.location.href = "/ejecutar_pago/" + data[1] + "/" + data[2];
                    }
                }
            });
        }
    </script>
    {% endblock %}
    ''', user=user, coms=comisiones, movs=movs, u_nom=user[1])

@app.route('/recargar', methods=['POST'])
def recargar():
    if session.get('u') != 'admin': return redirect('/')
    t, m = request.form['t'], float(request.form['m'])
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (m, t))
    cur.execute("INSERT INTO historial (emisor, receptor, monto, concepto) VALUES ('ADMIN', %s, %s, 'Recarga')", (t, m, ))
    conn.commit(); cur.close(); conn.close()
    return redirect('/')

@app.route('/ejecutar_pago/<emi>/<mon>')
def ejecutar_pago(emi, mon):
    rec = session.get('u')
    m = float(mon); com = m * 0.015; neto = m - com
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id = %s", (m, emi))
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (neto, rec))
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = 'SISTEMA_GANANCIAS'", (com,))
    cur.execute("INSERT INTO historial (emisor, receptor, monto, concepto) VALUES (%s, %s, %s, 'Pago')", (emi, rec, neto))
    conn.commit(); cur.close(); conn.close()
    return redirect('/')

@app.route('/login_view')
def login_view():
    return render_template_string(BASE_HTML + '''
    {% block content %}
    <div class="will-card">
        <h4 class="gold-text">Entrar</h4>
        <form action="/proc_login" method="POST">
            <input name="t" placeholder="Teléfono" class="form-control mb-2" required>
            <input name="p" type="password" placeholder="PIN" class="form-control mb-3" required>
            <button class="btn-will">ACCEDER</button>
        </form>
    </div>
    {% endblock %}
    ''')

@app.route('/proc_login', methods=['POST'])
def proc_login():
    t, p = request.form['t'], request.form['p']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (t, p))
    if cur.fetchone(): session['u'] = t
    cur.close(); conn.close()
    return redirect('/')

@app.route('/set_rol/<r>')
def set_rol(r):
    if 'u' in session:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (r, session['u']))
        conn.commit(); cur.close(); conn.close()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
