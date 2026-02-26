from flask import Flask, render_template_string, request, redirect, session, jsonify, url_for, send_from_directory
import psycopg2, os, datetime, base64
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# --- CARPETA PARA EXPEDIENTES DE AUDITORÍA ---
UPLOAD_FOLDER = 'expedientes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# CONFIGURACIÓN DE BASE DE DATOS
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
        
        #pantalla_recibo { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); z-index:9999; padding-top:40px; }
        .recibo-digital { background: white; color: black; padding: 25px; border-radius: 15px; max-width: 340px; margin: auto; font-family: monospace; box-shadow: 0 0 20px var(--oro); }
    </style>
</head>
<body>
    <div class="container py-3">
        <img src="/logonuevo.png" class="logo-img">
        
        {% if session.get('u') %}
            <div class="card-will">
                <p class="small text-secondary">Bienvenido, {{ u.nombre }}</p>
                <h2 class="oro-text">Bs. {{ "%.2f"|format(u.saldo_bs) }}</h2>
                
                <button class="btn btn-outline-warning btn-sm w-100 mb-3" data-bs-toggle="collapse" data-bs-target="#panelRecarga">
                    ➕ RECARGAR SALDO
                </button>

                <div class="collapse" id="panelRecarga">
                    <div class="p-3 mb-3" style="background: #1a1a1a; border-radius: 15px; border: 1px dashed var(--oro);">
                        <form action="/solicitar_recarga" method="POST" enctype="multipart/form-data">
                            <input type="number" name="monto" step="0.01" class="form-control input-will" placeholder="Monto a recargar" required>
                            <input type="text" name="referencia" class="form-control input-will" placeholder="Referencia Bancaria" required>
                            <label class="small oro-text">Adjuntar Comprobante:</label>
                            <input type="file" name="capture" class="form-control input-will" accept="image/*" required>
                            <button type="submit" class="btn-will mt-2" style="padding: 10px;">NOTIFICAR PAGO</button>
                        </form>
                    </div>
                </div>
                <div class="btn-group w-100 my-3">
                    <a href="/cambiar_rol/pasajero" class="btn {{ 'btn-warning' if u.rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                    <a href="/cambiar_rol/prestador" class="btn {{ 'btn-warning' if u.rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
                </div>

                {% if u.rol == 'pasajero' %}
                    <label class="oro-text small">Indique monto a pagar:</label>
                    <input type="number" id="val_pago" class="form-control input-will border-0 oro-text" style="font-size:2.5rem;" placeholder="0.00" oninput="genQR()">
                    <div class="bg-white p-2 d-inline-block rounded mt-2">
                        <img id="q_img" src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{session.u}}|0" style="width:180px;">
                    </div>
                    <p class="small text-secondary mt-2">Muestra este código al prestador</p>
                {% else %}
                    <button class="btn-will py-3" onclick="scan()">📷 ESCANEAR QR PARA COBRAR</button>
                    <video id="video_camara" style="width:100%; display:none; border-radius:15px; margin-top:15px; border: 2px solid var(--oro);"></video>
                {% endif %}
                
                <hr>
                <a href="/logout" class="text-danger small text-decoration-none">Cerrar Sesión</a>
            </div>
        {% endif %}
    </div>

    <div id="pantalla_recibo">
        <div class="recibo-digital">
            <h4 style="color: #28a745; font-weight: bold;">✔ PAGO EXITOSO</h4>
            <hr style="border-top: 2px dashed #bbb;">
            <div style="text-align: left; line-height: 1.6;">
                <p><b>REF:</b> <span id="r_ref"></span></p>
                <p><b>FECHA:</b> <span id="r_fec"></span></p>
                <p><b>MONTO:</b> <span style="font-size: 1.3rem; color: #d4af37;">Bs. <span id="r_mon"></span></span></p>
                <p><b>DE (Pagador):</b> <br><span id="r_emi" class="text-secondary"></span></p>
                <p><b>PARA (Cobrador):</b> <br><span id="r_rec" class="text-secondary"></span></p>
            </div>
            <hr style="border-top: 2px dashed #bbb;">
            <button class="btn btn-dark w-100 mt-2" onclick="location.href='/'">LISTO / FINALIZAR</button>
        </div>
    </div>

    <audio id="audio_exito" src="https://www.myinstants.com/media/sounds/cash-register-purchase.mp3"></audio>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function genQR() {
            const m = document.getElementById('val_pago').value || 0;
            document.getElementById('q_img').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{session.u}}|${m}`;
        }

        async function scan() {
            const codeReader = new ZXing.BrowserQRCodeReader();
            const video = document.getElementById('video_camara');
            video.style.display = 'block';
            try {
                const result = await codeReader.decodeFromVideoDevice(null, 'video_camara');
                if (result) {
                    codeReader.reset();
                    video.style.display = 'none';
                    const response = await fetch('/procesar_pago/' + result.text);
                    const data = await response.json();
                    if(data.status === 'ok') {
                        document.getElementById('audio_exito').play();
                        document.getElementById('r_ref').innerText = data.ref;
                        document.getElementById('r_fec').innerText = data.fecha;
                        document.getElementById('r_mon').innerText = data.monto;
                        document.getElementById('r_emi').innerText = data.emisor;
                        document.getElementById('r_rec').innerText = data.receptor;
                        document.getElementById('pantalla_recibo').style.display = 'block';
                    } else { alert("ERROR: " + data.msg); location.reload(); }
                }
            } catch (err) { console.error(err); }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' not in session: return redirect('/login_page')
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template_string(LAYOUT, u=u)

# --- RUTA DE RECARGA (MANTIENE LA INTEGRIDAD) ---
@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/')
    monto = request.form.get('monto')
    referencia = request.form.get('referencia')
    file = request.files['capture']
    if file:
        user_folder = os.path.join(UPLOAD_FOLDER, str(session['u']))
        if not os.path.exists(user_folder): os.makedirs(user_folder)
        filename = secure_filename(f"REF_{referencia}_{file.filename}")
        file.save(os.path.join(user_folder, filename))
        # Registro en DB (asegúrate de tener esta tabla de auditoría creada)
        query_db("INSERT INTO auditoria_recargas (usuario_id, monto, referencia, capture, estado) VALUES (%s, %s, %s, %s, 'PENDIENTE')", 
                 (session['u'], monto, referencia, filename), commit=True)
    return redirect('/')

@app.route('/procesar_pago/<datos_qr>')
def procesar_pago(datos_qr):
    try:
        p = datos_qr.split('|')
        emisor_id = p[1]
        monto = float(p[2])
        receptor_id = session.get('u')
        emisor = query_db("SELECT saldo_bs, nombre FROM usuarios WHERE id=%s", (emisor_id,), one=True)
        if not emisor or emisor['saldo_bs'] < monto:
            return jsonify({'status': 'error', 'msg': 'Saldo insuficiente o usuario no existe'})
        
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (monto, emisor_id), commit=True)
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (monto, receptor_id), commit=True)
        
        receptor = query_db("SELECT nombre FROM usuarios WHERE id=%s", (receptor_id,), one=True)
        ref = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return jsonify({
            'status': 'ok', 'ref': ref, 'fecha': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            'monto': f"{monto:.2f}", 'emisor': emisor['nombre'], 'receptor': receptor['nombre']
        })
    except: return jsonify({'status': 'error', 'msg': 'QR Inválido'})

@app.route('/cambiar_rol/<r>')
def cambiar_rol(r):
    query_db("UPDATE usuarios SET rol=%s WHERE id=%s", (r, session['u']), commit=True)
    return redirect('/')

@app.route('/logonuevo.png')
def logo(): return send_from_directory(os.getcwd(), 'logonuevo.png')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
