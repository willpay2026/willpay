from flask import Flask, render_template_string, request, redirect, session, jsonify, url_for, send_from_directory
import psycopg2, os, datetime, base64
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# --- CARPETA PARA CAPTURES ---
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
                    <div class="p-3 mb-3 border border-secondary rounded" style="background: #1a1a1a;">
                        <form action="/solicitar_recarga" method="POST" enctype="multipart/form-data">
                            <input type="number" name="monto" step="0.01" class="form-control input-will" placeholder="Monto" required>
                            <input type="text" name="referencia" class="form-control input-will" placeholder="Referencia" required>
                            <input type="file" name="capture" class="form-control input-will" accept="image/*" required>
                            <button type="submit" class="btn-will mt-2" style="padding: 8px;">NOTIFICAR PAGO</button>
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
        {% else %}
            <div class="card-will">
                <h4 class="oro-text">Iniciar Sesión</h4>
                <p>Por favor, ingrese sus credenciales</p>
                <a href="/" class="btn-will d-block text-decoration-none">REINTENTAR ACCESO</a>
            </div>
        {% endif %}
    </div>

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
                    if(data.status === 'ok') { location.reload(); } else { alert(data.msg); }
                }
            } catch (err) { console.error(err); }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    # CAMBIO: Si no hay usuario, no enviamos a /login_page (que no existe), 
    # por ahora lo dejamos en el index con el mensaje de logueo.
    if 'u' not in session: 
        # Simulación: si quieres probar, pon session['u'] = 1 manualmente
        return render_template_string(LAYOUT)
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template_string(LAYOUT, u=u)

@app.route('/solicitar_recarga', methods=['POST'])
def solicitar_recarga():
    if 'u' not in session: return redirect('/')
    monto, ref = request.form.get('monto'), request.form.get('referencia')
    file = request.files['capture']
    if file:
        user_folder = os.path.join(UPLOAD_FOLDER, str(session['u']))
        if not os.path.exists(user_folder): os.makedirs(user_folder)
        filename = secure_filename(f"REF_{ref}_{file.filename}")
        file.save(os.path.join(user_folder, filename))
        # Aquí va la inserción en tu tabla de auditoria_recargas
    return redirect('/')

@app.route('/procesar_pago/<datos_qr>')
def procesar_pago(datos_qr):
    try:
        p = datos_qr.split('|')
        emisor_id, monto = p[1], float(p[2])
        receptor_id = session.get('u')
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (monto, emisor_id), commit=True)
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (monto, receptor_id), commit=True)
        return jsonify({'status': 'ok'})
    except: return jsonify({'status': 'error', 'msg': 'QR Inválido'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
