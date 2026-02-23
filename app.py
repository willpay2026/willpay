from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

app = Flask(__name__)
app.secret_key = 'willpay_global_gold_2026'

DB_USUARIOS = 'db_usuarios_v21.csv'
DB_RECARGAS = 'db_recargas_v21.csv'

def inicializar_db():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
            writer.writerow(["admin", "Admin Central", "0", "3110.00", "admin", "1234", "ACTIVO", "SISTEMA"])
    if not os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID_User", "Referencia", "Monto_Bs", "Status", "Fecha"])

def obtener_usuarios():
    data = {}
    if os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader: data[row['ID']] = row
    return data

@app.route('/logo')
def logo(): 
    if os.path.exists('logo will-pay.jpg'):
        return send_from_directory(os.getcwd(), 'logo will-pay.jpg')
    return "Logo"

HTML_APP = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background: #000; color: white; font-family: 'Segoe UI', sans-serif; text-align: center; }
        .will-container { border: 2px solid #D4AF37; border-radius: 35px; padding: 25px; margin: 15px auto; max-width: 420px; background: #0a0a0a; box-shadow: 0 0 20px rgba(212, 175, 55, 0.2); }
        .gold-text { color: #D4AF37; font-weight: bold; }
        .btn-will { background: #D4AF37; color: #000; font-weight: bold; border-radius: 12px; border: none; padding: 12px; }
        .form-control { background: #111; border: 1px solid #333; color: white; border-radius: 10px; margin-bottom: 12px; }
        .receipt-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:1000; padding-top:10%; }
        #video { width: 100%; border-radius: 15px; border: 2px solid #D4AF37; display: none; margin-bottom: 15px; }
    </style>
</head>
<body>
    <audio id="snd_cash" src="https://www.soundjay.com/misc/sounds/cash-register-purchase-1.mp3"></audio>
    <div class="container py-3">
        <img src="/logo" style="width: 140px; margin-bottom: 10px;">
        
        {% if vista == 'login' %}
        <div class="will-container">
            <h4 class="gold-text mb-4">INICIAR SESIÓN</h4>
            <form action="/login" method="POST">
                <input type="text" name="id" class="form-control text-center" placeholder="Usuario / Teléfono" required>
                <input type="password" name="pin" class="form-control text-center" placeholder="PIN" required>
                <button class="btn btn-will w-100">ENTRAR</button>
            </form>
        </div>

        {% elif vista == 'main' %}
        <div class="will-container">
            <span class="badge mb-2" style="background: rgba(212,175,55,0.2); color: #D4AF37;">{{ usuario.Tipo_Servicio }}</span>
            <p class="mb-1 text-secondary">Saldo Disponible</p>
            <h2 class="gold-text" style="font-size: 2.5rem;">Bs. {{ usuario.Saldo_Bs }}</h2>
            
            <div class="d-flex gap-2 my-4">
                <button class="btn btn-outline-light w-100 btn-sm" onclick="showRecarga()">RECARGAR</button>
                {% if usuario.ID == 'admin' %}
                <a href="/panel_control" class="btn btn-will w-100 btn-sm">ADMINISTRAR</a>
                {% endif %}
            </div>

            <div class="btn-group w-100 mb-4">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-will' if usuario.Rol == 'pasajero' else 'btn-outline-secondary text-white' }}">MODO PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-will' if usuario.Rol == 'prestador' else 'btn-outline-secondary text-white' }}">MODO COBRAR</a>
            </div>

            {% if usuario.Rol == 'pasajero' %}
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 20px; border: 1px solid #222;">
                    <input type="number" id="m_val" class="form-control text-center mb-3" style="font-size: 1.8rem; color: #D4AF37; border:none; background:transparent;" placeholder="Monto 0.00" oninput="genQR()">
                    <div style="background:white; padding:10px; display:inline-block; border-radius:15px;"><img id="qr_img" src="" style="width:180px; height:180px;"></div>
                </div>
            {% else %}
                <video id="video" autoplay playsinline></video>
                <button id="b_scan" class="btn btn-will w-100 mt-2" onclick="startScan()">📷 ABRIR ESCÁNER</button>
            {% endif %}
            <a href="/logout" class="text-danger d-block mt-4 small text-decoration-none">Cerrar Sesión</a>
        </div>

        {% elif vista == 'admin' %}
        <div class="will-container" style="max-width: 500px;">
            <h4 class="gold-text">REGISTRO DE USUARIOS</h4>
            <form action="/crear_usuario" method="POST" class="mt-3">
                <input type="text" name="new_id" class="form-control" placeholder="Teléfono (ID Acceso)" required>
                <input type="text" name="new_nombre" class="form-control" placeholder="Nombre Completo" required>
                <input type="text" name="new_cedula" class="form-control" placeholder="Cédula" required>
                <input type="password" name="new_pin" class="form-control" placeholder="PIN de 4 dígitos" required>
                <select name="new_tipo" class="form-control">
                    <option value="PASAJERO">PASAJERO</option>
                    <option value="CHOFER">CHOFER</option>
                    <option value="COMERCIO">COMERCIO</option>
                </select>
                <button class="btn btn-will w-100 mt-2">REGISTRAR USUARIO</button>
            </form>
            <hr style="border-color: #333;">
            <h5 class="gold-text">USUARIOS ACTIVOS</h5>
            <div style="text-align: left; font-size: 0.8rem; max-height: 200px; overflow-y: auto;">
                {% for u in todos %}
                <div style="border-bottom: 1px solid #222; padding: 5px;">
                    <b>{{ u.Nombre }}</b> ({{ u.ID }}) - Bs. {{ u.Saldo_Bs }}<br>
                    <span class="text-secondary">{{ u.Tipo_Servicio }}</span>
                </div>
                {% endfor %}
            </div>
            <a href="/" class="btn btn-outline-light w-100 mt-3">VOLVER</a>
        </div>
        {% endif %}
    </div>

    <script>
        function genQR() {
            const m = document.getElementById('m_val').value || 0;
            document.getElementById('qr_img').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WILLPAY|{{ usuario.ID if usuario else '' }}|${m}`;
        }
        function showRecarga() { document.getElementById('modalRecarga').style.display='block'; }
        function hideRecarga() { document.getElementById('modalRecarga').style.display='none'; }
        
        const codeReader = new ZXing.BrowserQRCodeReader();
        function startScan() {
            document.getElementById('video').style.display='block';
            document.getElementById('b_scan').style.display='none';
            codeReader.decodeFromVideoDevice(null, 'video', 'video', (result) => {
                if (result) {
                    const d = result.text.split('|');
                    let pin = prompt("INGRESE PIN DEL PASAJERO PARA AUTORIZAR:");
                    fetch(`/pago/${d[1]}/${d[2]}/{{ usuario.ID if usuario else '' }}/${pin}`)
                    .then(r => r.json()).then(j => {
                        if(j.status=='ok') {
                            document.getElementById('snd_cash').play();
                            alert("PAGO EXITOSO");
                            location.reload();
                        } else { alert("ERROR: " + j.message); location.reload(); }
                    });
                }
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(HTML_APP, vista='login', usuario=None)
    users = obtener_usuarios()
    u = users.get(session['u'])
    if not u and session['u'] == 'admin':
        u = {"ID": "admin", "Nombre": "Admin", "Saldo_Bs": "3110.00", "Rol": "admin", "Tipo_Servicio": "SISTEMA"}
    if not u: return redirect('/logout')
    return render_template_string(HTML_APP, vista='main', usuario=u)

@app.route('/login', methods=['POST'])
def login():
    uid, pin = request.form.get('id'), request.form.get('pin')
    if uid == 'admin' and pin == '1234':
        session['u'] = 'admin'
        return redirect('/')
    users = obtener_usuarios()
    if uid in users and users[uid]['PIN'] == pin: 
        session['u'] = uid
    return redirect('/')

@app.route('/panel_control')
def panel_control():
    if session.get('u') != 'admin': return redirect('/')
    users = obtener_usuarios()
    return render_template_string(HTML_APP, vista='admin', usuario={"ID":"admin"}, todos=users.values())

@app.route('/crear_usuario', methods=['POST'])
def crear_usuario():
    if session.get('u') != 'admin': return redirect('/')
    uid = request.form.get('new_id')
    nuevo = [
        uid, 
        request.form.get('new_nombre'), 
        request.form.get('new_cedula'), 
        "0.00", 
        "pasajero", 
        request.form.get('new_pin'), 
        "ACTIVO", 
        request.form.get('new_tipo')
    ]
    with open(DB_USUARIOS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(nuevo)
    return redirect('/panel_control')

@app.route('/pago/<emi>/<mon>/<rec>/<pin>')
def pago(emi, mon, rec, pin):
    users = obtener_usuarios()
    try:
        m = float(mon)
        if emi == 'admin' or (emi in users and users[emi]['PIN'] == pin and float(users[emi]['Saldo_Bs']) >= m):
            if emi != 'admin': users[emi]['Saldo_Bs'] = f"{float(users[emi]['Saldo_Bs']) - m:.2f}"
            if rec in users: users[rec]['Saldo_Bs'] = f"{float(users[rec]['Saldo_Bs']) + m:.2f}"
            with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
                writer.writeheader()
                for u in users.values(): writer.writerow(u)
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "message": "Saldo insuficiente o PIN incorrecto"})
    except: return jsonify({"status": "error", "message": "Error de sistema"})

@app.route('/set_rol/<r>')
def set_rol(r):
    users = obtener_usuarios()
    if session.get('u') in users:
        users[session['u']]['Rol'] = r
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
            writer.writeheader()
            for u in users.values(): writer.writerow(u)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
