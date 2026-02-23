from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2
from psycopg2.extras import DictCursor
import os, datetime

app = Flask(__name__)
app.secret_key = 'willpay_sql_ultra_2026'

DATABASE_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"
PORCENTAJE_COMISION = 0.015

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def inicializar_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY, nombre TEXT, saldo_bs NUMERIC DEFAULT 0, rol TEXT DEFAULT 'pasajero', pin TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS historial (
            id SERIAL PRIMARY KEY, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            emisor TEXT, receptor TEXT, monto NUMERIC, concepto TEXT
        )''')
        cur.execute("SELECT id FROM usuarios WHERE id = 'admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (id, nombre, saldo_bs, rol, pin) VALUES (%s,%s,%s,%s,%s)",
                        ('admin', 'Admin Will-Pay', 0, 'prestador', '1234'))
            cur.execute("INSERT INTO usuarios (id, nombre, saldo_bs, rol, pin) VALUES (%s,%s,%s,%s,%s)",
                        ('SISTEMA_GANANCIAS', 'Pote Comisiones', 0, 'admin', '9999'))
        conn.commit()
    except Exception as e: print(f"Error DB: {e}")
    finally:
        if 'conn' in locals():
            cur.close(); conn.close()

# --- INTERFAZ HTML CON NOMBRE DE USUARIO ---
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
        body { background-color: #000; color: #fff; font-family: 'Segoe UI', sans-serif; }
        .will-container { max-width: 450px; margin: 20px auto; padding: 20px; text-align: center; }
        .main-card { background: #111; border: 2px solid #d4af37; border-radius: 25px; padding: 30px; }
        .btn-gold { background-color: #d4af37; color: #000; font-weight: bold; border-radius: 12px; width: 100%; border:none; padding: 12px; }
        .saldo-display { color: #d4af37; font-size: 2.2rem; font-weight: bold; margin: 10px 0; word-wrap: break-word; }
        .historial-item { background: #1a1a1a; border-left: 4px solid #d4af37; padding: 10px; margin-bottom: 8px; text-align: left; border-radius: 8px; font-size: 0.85rem; }
        .user-name { color: #aaa; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="will-container">
        <h2 style="color:#d4af37; margin-bottom: 0;">WILL-PAY <span class="badge bg-warning text-dark" style="font-size:10px">SQL PRO</span></h2>
        
        {% if vista == 'landing' %}
            <div class="main-card mt-4">
                <a href="/login_view" class="btn-gold d-block mb-3 text-decoration-none">INICIAR SESIÓN</a>
                <a href="/registro_view" class="btn btn-outline-light w-100">REGISTRARSE</a>
            </div>
        {% elif vista == 'registro' %}
            <div class="main-card mt-4">
                <h4 style="color:#d4af37">Nueva Cuenta</h4>
                <form action="/procesar_registro" method="POST">
                    <input type="text" name="nombre" class="form-control bg-dark text-white mb-2" placeholder="Nombre Completo" required>
                    <input type="text" name="telefono" class="form-control bg-dark text-white mb-2" placeholder="Teléfono" required>
                    <input type="password" name="pin" class="form-control bg-dark text-white mb-3" placeholder="PIN 4 dígitos" required>
                    <button type="submit" class="btn-gold">REGISTRARSE</button>
                </form>
            </div>
        {% elif vista == 'login' %}
            <div class="main-card mt-4">
                <h4 style="color:#d4af37">Ingresar</h4>
                <form action="/procesar_login" method="POST">
                    <input type="text" name="telefono" class="form-control bg-dark text-white mb-2" placeholder="Teléfono" required>
                    <input type="password" name="pin" class="form-control bg-dark text-white mb-3" placeholder="PIN" required>
                    <button type="submit" class="btn-gold">ENTRAR</button>
                </form>
            </div>
        {% elif vista == 'main' %}
            <div class="user-name">Hola, {{ usuario[1] }}</div>
            <div class="main-card">
                {% if usuario[0] == 'admin' %}<div class="badge bg-danger mb-2">ADMIN</div>{% endif %}
                <div class="saldo-display">Bs. {{ "%.2f"|format(usuario[2]|float) }}</div>
                
                <div class="btn-group w-100 my-3">
                    <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if usuario[3] == 'pasajero' else 'btn-dark' }}">MODO PAGAR</a>
                    <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if usuario[3] == 'prestador' else 'btn-dark' }}">MODO COBRAR</a>
                </div>

                {% if usuario[3] == 'pasajero' %}
                    <div class="bg-white p-3 d-inline-block rounded-4 mb-2">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WP|{{usuario[0]}}|10">
                    </div>
                {% else %}
                    <button class="btn-gold py-3" onclick="iniciarEscaneo()">📷 ESCANEAR Y COBRAR</button>
                    <div id="scanner_div" style="display:none" class="mt-3">
                        <video id="v" style="width:100%; border-radius:15px; border: 2px solid #d4af37;"></video>
                    </div>
                {% endif %}

                {% if usuario[0] == 'admin' %}
                <div class="mt-4 p-3 border border-warning rounded bg-black">
                    <form action="/recarga_directa" method="POST">
                        <input type="text" name="target" class="form-control form-control-sm bg-dark text-white mb-1" placeholder="Teléfono">
                        <input type="number" step="0.01" name="monto" class="form-control form-control-sm bg-dark text-white mb-1" placeholder="Monto">
                        <button class="btn btn-warning btn-sm w-100">CARGAR SALDO</button>
                    </form>
                </div>
                {% endif %}

                <div class="mt-4 text-start" style="max-height:150px; overflow-y:auto">
                    {% for h in historial %}
                        <div class="historial-item">
                            <b>{{ h[5] }}</b> | {{ "%.2f"|format(h[4]|float) }} Bs.<br>
                            <small class="text-secondary">{{ h[1].strftime('%H:%M') }}</small>
                        </div>
                    {% endfor %}
                </div>
                <a href="/logout" class="text-danger small mt-3 d-block">Cerrar Sesión</a>
            </div>
        {% endif %}
    </div>
    <audio id="audio_cash" src="https://www.myinstants.com/media/sounds/cash-register-purchase.mp3"></audio>
    <script>
        function iniciarEscaneo() {
            document.getElementById('scanner_div').style.display='block';
            const codeReader = new ZXing.BrowserQRCodeReader();
            codeReader.decodeFromVideoDevice(null, 'v', (res) => {
                if (res) {
                    const parts = res.text.split('|');
                    const emisorId = parts[1];
                    const monto = parts[2] || "10";
                    
                    let pin = prompt("Confirmar cobro de " + monto + " Bs.\\nIngrese PIN del Pasajero:");
                    if(pin) {
                        fetch(`/pagar/${emisorId}/${monto}/${pin}`)
                        .then(r => r.json())
                        .then(data => {
                            if(data.status === 'ok') {
                                document.getElementById('audio_cash').play();
                                alert("¡COBRO EXITOSO!");
                                location.reload();
                            } else {
                                alert("ERROR: " + data.message);
                            }
                        });
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
    inicializar_db()
    if 'u' not in session: return render_template_string(HTML_LAYOUT, vista='landing')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, saldo_bs, rol FROM usuarios WHERE id = %s", (session['u'],))
    u = cur.fetchone()
    cur.execute("SELECT * FROM historial WHERE emisor = %s OR receptor = %s ORDER BY fecha DESC LIMIT 10", (u[0], u[0]))
    h = cur.fetchall()
    cur.close(); conn.close()
    return render_template_string(HTML_LAYOUT, vista='main', usuario=u, historial=h)

@app.route('/registro_view')
def registro_view(): return render_template_string(HTML_LAYOUT, vista='registro')

@app.route('/login_view')
def login_view(): return render_template_string(HTML_LAYOUT, vista='login')

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    t, n, p = request.form['telefono'], request.form['nombre'], request.form['pin']
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (id, nombre, saldo_bs, rol, pin) VALUES (%s,%s,0,'pasajero',%s)", (t, n, p))
        conn.commit()
        session['u'] = t
    except: pass
    finally: cur.close(); conn.close()
    return redirect('/')

@app.route('/procesar_login', methods=['POST'])
def procesar_login():
    t, p = request.form['telefono'], request.form['pin']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (t, p))
    user = cur.fetchone()
    cur.close(); conn.close()
    if user: session['u'] = t
    return redirect('/')

@app.route('/recarga_directa', methods=['POST'])
def recarga_directa():
    if session.get('u') != 'admin': return redirect('/')
    t, m = request.form['target'], float(request.form['monto'])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id = %s", (m, t))
    cur.execute("INSERT INTO historial (emisor, receptor, monto, concepto) VALUES (%s,%s,%s,%s)", ('ADMIN', t, m, 'Recarga'))
    conn.commit()
    cur.close(); conn.close()
    return redirect('/')

@app.route('/set_rol/<r>')
def set_rol(r):
    if 'u' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (r, session['u']))
        conn.commit()
        cur.close(); conn.close()
    return redirect('/')

@app.route('/pagar/<emi>/<mon>/<pin>')
def pagar(emi, mon, pin):
    rec = session.get('u')
    try:
        m = float(mon)
        com = round(m * PORCENTAJE_COMISION, 2)
        final = m - com
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT saldo_bs FROM usuarios WHERE id=%s", (emi,))
        res = cur.fetchone()
        
        if res and float(res[0]) >= m:
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (m, emi))
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (final, rec))
            cur.execute("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (com, 'SISTEMA_GANANCIAS'))
            cur.execute("INSERT INTO historial (emisor, receptor, monto, concepto) VALUES (%s,%s,%s,%s)", (emi, rec, final, 'Pasaje'))
            conn.commit()
            status = "ok"
        else: status = "error"; msg = "Saldo insuficiente"
        
        cur.close(); conn.close()
        return jsonify({"status": status, "message": msg if status=="error" else ""})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
