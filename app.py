from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# CONFIGURACIÓN DE BASE DE DATOS (Asegúrate de tener las tablas creadas)
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

# --- INTERFAZ PREMIUM ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay | Emporio Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        :root { --oro: #D4AF37; --negro: #000; }
        body { background: var(--negro); color: white; font-family: 'Segoe UI', sans-serif; }
        .card-will { background: #111; border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin-top: 20px; }
        .oro-text { color: var(--oro); font-weight: bold; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 12px; border: none; padding: 15px; width: 100%; }
        .saldo-display { font-size: 2.5rem; color: var(--oro); font-weight: bold; }
        .input-will { background: #222 !important; color: white !important; border: 1px solid #444 !important; }
        #ticket { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:9999; padding:20px; overflow-y: auto; }
        .recibo-papel { background: white; color: black; padding: 20px; border-radius: 5px; font-family: monospace; text-align: left; max-width: 400px; margin: auto; }
    </style>
</head>
<body>
    <div class="container text-center py-4">
        <h2 class="oro-text">WILL-PAY</h2>
        <p class="small text-secondary">El legado de Wilfredo Donquiz para Venezuela</p>

        {% if not session.get('u') %}
            <div class="card-will" id="login_form">
                <h4 class="oro-text mb-4">INICIAR SESIÓN</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control mb-2 input-will" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control mb-3 input-will" required>
                    <button class="btn-will">ENTRAR</button>
                </form>
                <button class="btn btn-link text-warning mt-3" onclick="showReg()">¿No tienes cuenta? Regístrate</button>
            </div>

            <div class="card-will" id="reg_form" style="display:none;">
                <h4 class="oro-text mb-4">NUEVA CUENTA</h4>
                <form action="/registro" method="POST">
                    <input name="n" placeholder="Nombre Completo" class="form-control mb-2 input-will" required>
                    <input name="t" placeholder="Teléfono" class="form-control mb-2 input-will" required>
                    <input name="p" type="password" placeholder="PIN (4-6 dígitos)" class="form-control mb-3 input-will" required>
                    <button class="btn-will">CREAR CUENTA</button>
                </form>
                <button class="btn btn-link text-secondary mt-3" onclick="showLogin()">Volver</button>
            </div>
        {% else %}
            <div class="card-will">
                <p class="mb-0 text-secondary small">Bienvenido, {{ u.nombre }}</p>
                <div class="saldo-display">Bs. {{ "%.2f"|format(u.saldo_bs) }}</div>
                
                <div class="d-flex gap-2 my-4">
                    <button class="btn btn-outline-warning w-100" onclick="showRecarga()">RECARGAR</button>
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
                </div>

                <div class="btn-group w-100 mb-4">
                    <a href="/rol/pasajero" class="btn {{ 'btn-warning' if u.rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                    <a href="/rol/prestador" class="btn {{ 'btn-warning' if u.rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
                </div>

                {% if u.rol == 'pasajero' %}
                    <label class="small text-secondary">Monto a pagar:</label>
                    <input type="number" id="val_pago" class="form-control text-center bg-transparent border-0 oro-text mb-3" style="font-size:2.5rem;" placeholder="0.00" oninput="genQR()">
                    <div class="bg-white p-2 d-inline-block rounded"><img id="q_img" src="" style="width:180px;"></div>
                {% else %}
                    <button class="btn-will py-3" onclick="scan()">📷 ESCANEAR QR</button>
                    <video id="v" style="width:100%; display:none; border-radius:15px; margin-top:10px;"></video>
                {% endif %}
                
                {% if session['u'] == '04126602555' %}
                    <hr><a href="/admin_panel" class="btn btn-sm btn-info w-100">PANEL ADMINISTRADOR</a>
                {% endif %}
            </div>

            <div id="m_recarga" style="display:none;" class="card-will text-start">
                <h5 class="oro-text text-center">DATOS PAGO MÓVIL</h5>
                <div class="p-3 mb-3" style="background:#222; border-radius:15px; font-size:0.9rem;">
                    <p class="mb-1"><b>Banco:</b> Banesco</p>
                    <p class="mb-1"><b>Teléfono:</b> 04126602555</p>
                    <p class="mb-1"><b>Cédula:</b> V-13496133</p>
                </div>
                <form action="/reportar" method="POST">
                    <input name="ref" placeholder="Referencia Bancaria" class="form-control mb-2 input-will" required>
                    <input name="monto" type="number" step="0.01" placeholder="Monto Bs." class="form-control mb-3 input-will" required>
                    <button class="btn-will">REPORTAR PAGO</button>
                    <button type="button" class="btn btn-link text-secondary w-100" onclick="hideRecarga()">Cancelar</button>
                </form>
            </div>
        {% endif %}
    </div>

    <div id="ticket">
        <div class="recibo-papel mt-4">
            <h5 class="text-center">WILL-PAY</h5>
            <p class="text-center small">Comprobante Electrónico</p>
            <hr>
            <p id="t_correlativo"></p>
            <p id="t_fecha"></p>
            <hr>
            <p><strong>PAGADOR:</strong> <span id="t_emisor"></span></p>
            <p><strong>RECEPTOR:</strong> <span id="t_receptor"></span></p>
            <hr>
            <h3 class="text-center" id="t_monto_total"></h3>
            <p class="text-center small">Ref: <span id="t_ref_banc"></span></p>
            <p class="text-center mt-4 small">¡Gracias por usar tecnología con corazón!</p>
            <button class="btn btn-dark w-100 mt-3" onclick="location.reload()">CERRAR</button>
        </div>
    </div>

    <script>
        const snd = new Audio('https://www.soundjay.com/misc/sounds/cash-register-purchase-1.mp3');
        function showReg() { document.getElementById('login_form').style.display='none'; document.getElementById('reg_form').style.display='block'; }
        function showLogin() { document.getElementById('login_form').style.display='block'; document.getElementById('reg_form').style.display='none'; }
        function showRecarga() { document.getElementById('m_recarga').style.display='block'; }
        function hideRecarga() { document.getElementById('m_recarga').style.display='none'; }
        
        function genQR() {
            const m = document.getElementById('val_pago').value || 0;
            document.getElementById('q_img').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{session.u}}|${m}`;
        }

        function scan() {
            const v = document.getElementById('v'); v.style.display='block';
            const reader = new ZXing.BrowserQRCodeReader();
            reader.decodeFromVideoDevice(null, 'v', (res) => {
                if (res) {
                    const d = res.text.split('|');
                    if(confirm(`¿Confirmar cobro de ${d[2]} Bs?`)) {
                        fetch(`/do_pago/${d[1]}/${d[2]}`).then(r => r.json()).then(j => {
                            if(j.status == 'ok') {
                                snd.play();
                                document.getElementById('t_correlativo').innerText = "CORRELATIVO: " + j.correlativo;
                                document.getElementById('t_fecha').innerText = "FECHA: " + j.fecha_hora;
                                document.getElementById('t_emisor').innerText = j.emisor_nom + " (" + j.emisor_id + ")";
                                document.getElementById('t_receptor').innerText = j.receptor_nom + " (" + j.receptor_id + ")";
                                document.getElementById('t_monto_total').innerText = j.monto + " Bs.";
                                document.getElementById('t_ref_banc').innerText = j.ref;
                                document.getElementById('ticket').style.display = 'block';
                            } else { alert(j.msg); }
                        });
                    }
                }
            });
        }
    </script>
</body>
</html>
'''

# --- RUTAS DE LÓGICA ---

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(LAYOUT, u=None)
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template_string(LAYOUT, u=u)

@app.route('/login', methods=['POST'])
def login():
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect('/')

@app.route('/registro', methods=['POST'])
def registro():
    query_db("INSERT INTO usuarios (id, pin, nombre, saldo_bs, rol) VALUES (%s, %s, %s, 0, 'pasajero')", 
             (request.form['t'], request.form['p'], request.form['n']), commit=True)
    session['u'] = request.form['t']
    return redirect('/')

@app.route('/do_pago/<emi>/<mon>')
def do_pago(emi, mon):
    try:
        m = float(mon)
        pas = query_db("SELECT nombre, saldo_bs FROM usuarios WHERE id=%s", (emi,), one=True)
        rec = query_db("SELECT nombre FROM usuarios WHERE id=%s", (session['u'],), one=True)
        
        if pas and float(pas['saldo_bs']) >= m:
            com = m * 0.015
            neto = m - com
            # Transacciones de Saldo
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (m, emi), commit=True)
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (neto, session['u']), commit=True)
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id='SISTEMA_GANANCIAS'", (com,), commit=True)
            
            # Registro en Tabla Pagos para Correlativo
            ahora = datetime.datetime.now()
            query_db("INSERT INTO pagos (emisor_id, receptor_id, monto, fecha) VALUES (%s, %s, %s, %s)", 
                     (emi, session['u'], m, ahora), commit=True)
            
            last = query_db("SELECT id FROM pagos ORDER BY id DESC LIMIT 1", one=True)
            
            return jsonify({
                "status": "ok", "monto": m, 
                "correlativo": f"WP-{last['id']:06d}",
                "fecha_hora": ahora.strftime("%d/%m/%Y %H:%M:%S"),
                "emisor_nom": pas['nombre'], "emisor_id": emi,
                "receptor_nom": rec['nombre'], "receptor_id": session['u'],
                "ref": ahora.strftime("%H%M%S")
            })
        return jsonify({"status": "error", "msg": "Saldo Insuficiente"})
    except: return jsonify({"status": "error", "msg": "Error en proceso"})

@app.route('/reportar', methods=['POST'])
def reportar():
    query_db("INSERT INTO recargas (usuario_id, monto, referencia, estado) VALUES (%s, %s, %s, 'pendiente')",
             (session['u'], request.form['monto'], request.form['ref']), commit=True)
    return "<h1>REPORTE ENVIADO</h1><p>Wilfredo validará tu pago pronto.</p><a href='/'>Volver</a>"

@app.route('/admin_panel')
def admin_panel():
    if session.get('u') != '04126602555': return "No autorizado"
    pendientes = query_db("SELECT * FROM recargas WHERE estado='pendiente'")
    return f"<h2>Panel Admin</h2>" + "".join([f"Ref: {r['referencia']} - {r['monto']} Bs <a href='/aprobar/{r['id']}'>APROBAR</a><br>" for r in pendientes])

@app.route('/aprobar/<rid>')
def aprobar(rid):
    if session.get('u') != '04126602555': return "Error"
    r = query_db("SELECT * FROM recargas WHERE id=%s", (rid,), one=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (r['monto'], r['usuario_id']), commit=True)
    query_db("UPDATE recargas SET estado='aprobado' WHERE id=%s", (rid,), commit=True)
    return redirect('/admin_panel')

@app.route('/rol/<r>')
def rol(r):
    query_db("UPDATE usuarios SET rol=%s WHERE id=%s", (r, session['u']), commit=True)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
