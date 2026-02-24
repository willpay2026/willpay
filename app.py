from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026'

# CONFIGURACIÓN DE BASE DE DATOS
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

# --- INTERFAZ PREMIUM ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Emporio Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        :root { --oro: #D4AF37; --negro: #000; }
        body { background: var(--negro); color: white; font-family: 'Segoe UI', sans-serif; }
        .card-will { background: #111; border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin-top: 20px; }
        .oro-text { color: var(--oro); font-weight: bold; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 12px; border: none; padding: 15px; width: 100%; }
        .saldo-display { font-size: 3rem; color: var(--oro); font-weight: bold; }
        .input-will { background: #222 !important; color: white !important; border: 1px solid #444 !important; }
        #ticket { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:9999; padding:20px; }
    </style>
</head>
<body>
    <div class="container text-center py-4">
        <h2 class="oro-text">WILL-PAY</h2>
        <p class="small text-secondary">Tecnología con corazón, pensada para el futuro de Venezuela</p>

        {% if not session.get('u') %}
            <div class="card-will">
                <h4 class="oro-text mb-4">INICIAR SESIÓN</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control mb-2 input-will" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control mb-3 input-will" required>
                    <button class="btn-will">ENTRAR</button>
                </form>
            </div>
        {% else %}
            <div class="card-will">
                <p class="mb-0 text-secondary small">Saldo Disponible</p>
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
                    <label class="small text-secondary">Indique monto y muestre el QR:</label>
                    <input type="number" id="val_pago" class="form-control text-center bg-transparent border-0 oro-text mb-3" style="font-size:2.5rem;" placeholder="0.00" oninput="genQR()">
                    <div class="bg-white p-2 d-inline-block rounded"><img id="q_img" src="" style="width:180px;"></div>
                {% else %}
                    <button class="btn-will py-3" onclick="scan()">📷 ESCANEAR QR</button>
                    <video id="v" style="width:100%; display:none; border-radius:15px; margin-top:10px;"></video>
                {% endif %}
            </div>

            <div id="m_recarga" style="display:none;" class="card-will text-start">
                <h5 class="oro-text">DATOS PAGO MÓVIL</h5>
                <div class="p-3 mb-3" style="background:#222; border-radius:15px;">
                    <p class="mb-1"><b>Banco:</b> Banesco</p>
                    <p class="mb-1"><b>Teléfono:</b> 04126602555</p>
                    <p class="mb-1"><b>Cédula:</b> V-13496133</p>
                </div>
                <form action="/reportar" method="POST">
                    <input name="ref" placeholder="Referencia" class="form-control mb-2 input-will" required>
                    <input name="monto" type="number" step="0.01" placeholder="Monto Bs." class="form-control mb-3 input-will" required>
                    <button class="btn-will">REPORTAR PAGO</button>
                    <button type="button" class="btn btn-link text-secondary w-100" onclick="hideRecarga()">Cancelar</button>
                </form>
            </div>
        {% endif %}
    </div>

    <div id="ticket">
        <div class="card-will text-center mt-5 bg-white text-dark">
            <h4 class="text-success font-weight-bold">¡PAGO EXITOSO!</h4>
            <hr>
            <h2 id="t_monto"></h2>
            <p id="t_ref" class="small"></p>
            <p class="mt-4">Gracias por usar Will-Pay.</p>
            <button class="btn btn-dark w-100" onclick="location.reload()">VOLVER</button>
        </div>
    </div>

    <script>
        const snd = new Audio('https://www.soundjay.com/misc/sounds/cash-register-purchase-1.mp3');
        function showRecarga() { document.getElementById('m_recarga').style.display='block'; }
        function hideRecarga() { document.getElementById('m_recarga').style.display='none'; }
        
        function genQR() {
            const m = document.getElementById('val_pago').value || 0;
            document.getElementById('q_img').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{u.id if u else ''}}|${m}`;
        }

        function scan() {
            const v = document.getElementById('v'); v.style.display='block';
            const reader = new ZXing.BrowserQRCodeReader();
            reader.decodeFromVideoDevice(null, 'v', (res) => {
                if (res) {
                    const d = res.text.split('|');
                    if(confirm(`¿Cobrar ${d[2]} Bs?`)) {
                        fetch(`/do_pago/${d[1]}/${d[2]}`).then(r => r.json()).then(j => {
                            if(j.status == 'ok') {
                                snd.play();
                                document.getElementById('t_monto').innerText = j.monto + " Bs.";
                                document.getElementById('t_ref').innerText = "Ref: " + j.ref;
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

@app.route('/do_pago/<emi>/<mon>')
def do_pago(emi, mon):
    try:
        m = float(mon)
        pas = query_db("SELECT saldo_bs FROM usuarios WHERE id=%s", (emi,), one=True)
        if pas and float(pas['saldo_bs']) >= m:
            com = m * 0.015
            neto = m - com
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (m, emi), commit=True)
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (neto, session['u']), commit=True)
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id='SISTEMA_GANANCIAS'", (com,), commit=True)
            ref = datetime.datetime.now().strftime("%S%M%H")
            return jsonify({"status": "ok", "monto": m, "ref": ref})
        return jsonify({"status": "error", "msg": "Saldo Insuficiente"})
    except: return jsonify({"status": "error", "msg": "Error en proceso"})

@app.route('/rol/<r>')
def rol(r):
    query_db("UPDATE usuarios SET rol=%s WHERE id=%s", (r, session['u']), commit=True)
    return redirect('/')

@app.route('/reportar', methods=['POST'])
def reportar():
    # Aquí se guardaría en una tabla de recargas para que Wilfredo la apruebe
    return "<h1>REPORTE ENVIADO</h1><p>Wilfredo validará tu pago pronto.</p><a href='/'>Volver</a>"

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
