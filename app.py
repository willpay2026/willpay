from flask import Flask, render_template_string, request, redirect, session, jsonify, url_for, send_from_directory
import psycopg2, os, datetime, base64
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# CONFIGURACIÓN DE BASE DE DATOS (LA TUYA, SIN TOCAR)
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

# --- INTERFAZ ORIGINAL CON EL AGREGADO DEL RECIBO ---
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
        body { background: var(--negro); color: white; font-family: 'Segoe UI', sans-serif; text-align: center; }
        .card-will { background: #111; border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin: 20px auto; max-width: 450px; }
        .oro-text { color: var(--oro); font-weight: bold; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 12px; border: none; padding: 15px; width: 100%; }
        .logo-img { width: 250px; border-radius: 15px; margin: 15px 0; }
        .input-will { background: #222 !important; color: white !important; border: 1px solid #444 !important; margin-bottom: 10px; text-align: center; }
        
        /* VENTANA DE RECIBO EXITOSO */
        #pantalla_exito { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:9999; padding-top:50px; }
        .recibo { background: white; color: black; padding: 20px; border-radius: 15px; max-width: 320px; margin: auto; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container py-3">
        <img src="/logonuevo.png" class="logo-img">
        
        {% if not session.get('u') %}
            <div class="card-will">
                <h4 class="oro-text mb-4">INICIAR SESIÓN</h4>
                <form action="/auth_login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control input-will" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control input-will" required>
                    <button class="btn-will">ENTRAR</button>
                </form>
            </div>
        {% else %}
            <div class="card-will">
                <p class="mb-0 text-secondary small">Bienvenido | {{ u.servicio }}</p>
                <h4 class="oro-text">{{ u.nombre }}</h4>
                <div style="font-size: 2.5rem; color: var(--oro); font-weight: bold;">Bs. {{ "%.2f"|format(u.saldo_bs) }}</div>
                
                <div class="btn-group w-100 my-3">
                    <a href="/cambiar_rol/pasajero" class="btn {{ 'btn-warning' if u.rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                    <a href="/cambiar_rol/prestador" class="btn {{ 'btn-warning' if u.rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
                </div>

                {% if u.rol == 'pasajero' %}
                    <input type="number" id="val_pago" class="form-control input-will border-0 oro-text" style="font-size:2.5rem;" placeholder="0.00" oninput="genQR()">
                    <div class="bg-white p-2 d-inline-block rounded mt-2">
                        <img id="q_img" src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{session.u}}|0" style="width:180px;">
                    </div>
                {% else %}
                    <button class="btn-will" onclick="scan()">📷 ESCANEAR QR</button>
                    <video id="v" style="width:100%; display:none; border-radius:15px; margin-top:10px;"></video>
                {% endif %}
            </div>
        {% endif %}
    </div>

    <div id="pantalla_exito">
        <div class="recibo">
            <h3 style="color: green;">✔ PAGO EXITOSO</h3>
            <hr>
            <p style="text-align: left;">
                <b>REF:</b> <span id="r_ref"></span><br>
                <b>FECHA:</b> <span id="r_fec"></span><br>
                <b>MONTO:</b> <span style="font-size: 1.2rem;">Bs. <span id="r_mon"></span></span><br>
                <b>DE:</b> <span id="r_emi"></span><br>
                <b>PARA:</b> <span id="r_rec"></span>
            </p>
            <button class="btn btn-dark w-100" onclick="location.href='/'">FINALIZAR</button>
        </div>
    </div>

    <audio id="sonido_pago" src="https://www.myinstants.com/media/sounds/cash-register-purchase.mp3"></audio>

    <script>
        function genQR() {
            const m = document.getElementById('val_pago').value || 0;
            document.getElementById('q_img').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{session.u}}|${m}`;
        }

        function scan() {
            const codeReader = new ZXing.BrowserQRCodeReader();
            const v = document.getElementById('v');
            v.style.display = 'block';
            codeReader.decodeFromVideoDevice(null, 'v', async (result, err) => {
                if (result) {
                    codeReader.reset();
                    v.style.display = 'none';
                    // Llamamos a la lógica de pago
                    const response = await fetch('/procesar_pago/' + result.text);
                    const data = await response.json();
                    
                    if(data.status === 'ok') {
                        document.getElementById('sonido_pago').play();
                        document.getElementById('r_ref').innerText = data.ref;
                        document.getElementById('r_fec').innerText = data.fecha;
                        document.getElementById('r_mon').innerText = data.monto;
                        document.getElementById('r_emi').innerText = data.emisor;
                        document.getElementById('r_rec').innerText = data.receptor;
                        document.getElementById('pantalla_exito').style.display = 'block';
                    } else {
                        alert("Error: " + data.msg);
                        location.href = '/';
                    }
                }
            });
        }
    </script>
</body>
</html>
'''

# --- LÓGICA DE BACKEND (SIN TOCAR LO QUE FUNCIONA) ---

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(LAYOUT, u=None)
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template_string(LAYOUT, u=u)

@app.route('/procesar_pago/<datos_qr>')
def procesar_pago(datos_qr):
    try:
        # WP|Telefono|Monto
        p = datos_qr.split('|')
        emisor_id = p[1]
        monto = float(p[2])
        receptor_id = session['u']

        # Verificamos emisor
        emisor = query_db("SELECT saldo_bs, nombre FROM usuarios WHERE id=%s", (emisor_id,), one=True)
        if emisor['saldo_bs'] < monto:
            return jsonify({'status': 'error', 'msg': 'Saldo insuficiente'})

        # Movimiento de dinero
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (monto, emisor_id), commit=True)
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (monto, receptor_id), commit=True)

        receptor = query_db("SELECT nombre FROM usuarios WHERE id=%s", (receptor_id,), one=True)
        ref = datetime.datetime.now().strftime("%H%M%S%d%m") # Correlativo: HoraMinSegDiaMes

        return jsonify({
            'status': 'ok',
            'ref': ref,
            'fecha': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            'monto': f"{monto:.2f}",
            'emisor': emisor['nombre'],
            'receptor': receptor['nombre']
        })
    except:
        return jsonify({'status': 'error', 'msg': 'QR Inválido'})

@app.route('/logonuevo.png')
def logo(): return send_from_directory(os.getcwd(), 'logonuevo.png')

@app.route('/auth_login', methods=['POST'])
def auth_login():
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect('/')

@app.route('/cambiar_rol/<r>')
def cambiar_rol(r):
    query_db("UPDATE usuarios SET rol=%s WHERE id=%s", (r, session['u']), commit=True)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
