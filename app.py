from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'willpay_sql_ultra_2026'

# --- CONFIGURACIÓN ---
DATABASE_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"
PORT = int(os.environ.get("PORT", 10000))

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- HTML ---
HTML_LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay PRO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background-color: #000; color: #fff; font-family: sans-serif; padding: 10px; }
        .main-card { background: #111; border: 2px solid #d4af37; border-radius: 20px; padding: 25px; text-align: center; max-width: 400px; margin: auto; }
        .btn-gold { background: #d4af37; color: #000; font-weight: bold; width: 100%; border-radius: 10px; padding: 12px; border: none; }
        .saldo { color: #d4af37; font-size: 2.5rem; font-weight: bold; margin: 15px 0; }
        .user-name { font-size: 0.9rem; color: #888; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h2 class="text-center" style="color:#d4af37">WILL-PAY PRO</h2>
    {% if not session.get('u') %}
        <div class="main-card mt-4">
            <a href="/login_view" class="btn-gold d-block mb-3 text-decoration-none text-center">ENTRAR</a>
            <a href="/registro_view" class="btn btn-outline-light w-100">REGISTRO</a>
        </div>
    {% else %}
        <div class="user-name text-center">Hola, {{ usuario[1] }}</div>
        <div class="main-card">
            <div class="saldo">Bs. {{ "%.2f"|format(usuario[2]|float) }}</div>
            <div class="btn-group w-100 mb-3">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if usuario[3] == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if usuario[3] == 'prestador' else 'btn-dark' }}">COBRAR</a>
            </div>
            {% if usuario[3] == 'pasajero' %}
                <div class="bg-white p-3 d-inline-block rounded-3 mb-3">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WP|{{usuario[0]}}|10">
                </div>
                <p class="small text-muted">Muestra este código (10 Bs.)</p>
            {% else %}
                <button class="btn-gold py-3" onclick="escanear()">📷 ESCANEAR QR</button>
                <div id="vid_cont" style="display:none" class="mt-3">
                    <video id="v" style="width:100%; border-radius:10px; border:1px solid #d4af37;"></video>
                </div>
            {% endif %}
            <a href="/logout" class="text-danger small d-block mt-4">Salir</a>
        </div>
    {% endif %}
    <script>
        function escanear() {
            document.getElementById('vid_cont').style.display='block';
            const reader = new ZXing.BrowserQRCodeReader();
            reader.decodeFromVideoDevice(null, 'v', (res) => {
                if (res) {
                    const p = res.text.split('|');
                    if(confirm("¿Cobrar " + p[2] + " Bs a " + p[1] + "?")) {
                        fetch(`/pagar/${p[1]}/${p[2]}`).then(() => location.reload());
                    }
                }
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(HTML_LAYOUT)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id, nombre, saldo_bs, rol FROM usuarios WHERE id = %s", (session['u'],))
    u = cur.fetchone(); cur.close(); conn.close()
    return render_template_string(HTML_LAYOUT, usuario=u)

@app.route('/registro_view')
def registro_view(): return render_template_string(HTML_LAYOUT) # Simplificado para evitar errores de renderizado

@app.route('/login_view')
def login_view():
    return render_template_string('''
        <body style="background:#000;color:#fff;text-align:center;padding:50px">
            <form action="/procesar_login" method="POST">
                <input name="telefono" placeholder="Teléfono" style="display:block;width:100%;margin-bottom:10px;padding:10px">
                <input name="pin" type="password" placeholder="PIN" style="display:block;width:100%;margin-bottom:10px;padding:10px">
                <button style="background:#d4af37;width:100%;padding:10px">ENTRAR</button>
            </form>
        </body>
    ''')

@app.route('/procesar_login', methods=['POST'])
def procesar_login():
    t, p = request.form['telefono'], request.form['pin']
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (t, p))
    if cur.fetchone(): session['u'] = t
    cur.close(); conn.close()
    return redirect('/')

@app.route('/set_rol/<r>')
def set_rol(r):
    if 'u' in session:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (r, session['u']))
        conn.commit(); cur.close(); conn.close()
    return redirect('/')

@app.route('/pagar/<emi>/<mon>')
def pagar(emi, mon):
    rec = session.get('u')
    m = float(mon); com = m * 0.015; final = m - com
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (m, emi))
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (final, rec))
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id='SISTEMA_GANANCIAS'", (com,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"status": "ok"})

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
