from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

app = Flask(__name__)
app.secret_key = 'willpay_global_gold_2026'

# --- CONFIGURACIÓN DE ARCHIVOS ---
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

# --- TU INTERFAZ COMPLETA (EL CHORIZO DORADO) ---
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
        .form-control, .form-select { background: #111; border: 1px solid #333; color: white; border-radius: 10px; margin-bottom: 12px; }
        .receipt-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:1000; padding-top:10%; }
        #video { width: 100%; border-radius: 15px; border: 2px solid #D4AF37; display: none; margin-bottom: 15px; }
    </style>
</head>
<body>
    <audio id="snd_cash" src="https://www.soundjay.com/misc/sounds/cash-register-purchase-1.mp3"></audio>
    <div class="container py-3">
        <img src="/logo" style="width: 160px; margin-bottom: 10px;">
        {% if vista == 'login' %}
        <div class="will-container">
            <h4 class="gold-text mb-4">INICIAR SESIÓN</h4>
            <form action="/login" method="POST">
                <input type="text" name="id" class="form-control text-center" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control text-center" placeholder="PIN" required>
                <button class="btn btn-will w-100">ENTRAR</button>
            </form>
        </div>
        {% elif vista == 'main' %}
        <div class="will-container">
            <span class="badge mb-2" style="background: rgba(212,175,55,0.2); color: #D4AF37;">{{ usuario.Tipo_Servicio }}</span>
            <p class="mb-1 text-secondary">Saldo Disponible</p>
            <h2 class="gold-text" style="font-size: 2.8rem;">Bs. {{ usuario.Saldo_Bs }}</h2>
            <div class="d-flex gap-2 my-4">
                <button class="btn btn-outline-light w-100 btn-sm" onclick="showRecarga()">RECARGAR</button>
                {% if usuario.ID == 'admin' %}<a href="/panel_control" class="btn btn-will w-100 btn-sm">AUDITORÍA</a>{% endif %}
            </div>
            <div class="btn-group w-100 mb-4">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-will' if usuario.Rol == 'pasajero' else 'btn-outline-secondary text-white' }}">PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-will' if usuario.Rol == 'prestador' else 'btn-outline-secondary text-white' }}">COBRAR</a>
            </div>
            {% if usuario.Rol == 'pasajero' %}
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 20px; border: 1px solid #222;">
                    <input type="number" id="m_val" class="form-control text-center mb-3" style="font-size: 2rem; color: #D4AF37; border:none; background:transparent;" placeholder="0.00" oninput="genQR()">
                    <div style="background:white; padding:10px; display:inline-block; border-radius:15px;"><img id="qr_img" src="" style="width:180px; height:180px;"></div>
                </div>
            {% else %}
                <video id="video" autoplay playsinline></video>
                <button id="b_scan" class="btn btn-will w-100 mt-2" onclick="startScan()">📷 ABRIR ESCÁNER</button>
            {% endif %}
            <a href="/logout" class="text-danger d-block mt-4 small text-decoration-none">Cerrar Sesión</a>
        </div>
        {% endif %}
    </div>

    <div id="modalRecarga" class="receipt-overlay">
        <div class="will-container">
            <h5 class="gold-text">REPORTE DE PAGO</h5>
            <form action="/reportar" method="POST">
                <input type="file" class="form-control" accept="image/*">
                <input type="text" name="ref" class="form-control" placeholder="Referencia" required>
                <input type="number" step="0.01" name="monto" class="form-control" placeholder="Monto Bs." required>
                <button class="btn btn-will w-100">ENVIAR REPORTE</button>
                <button type="button" class="btn text-white w-100 mt-2" onclick="hideRecarga()">Cancelar</button>
            </form>
        </div>
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
                    let pin = prompt("INGRESE PIN DEL PASAJERO:");
                    fetch(`/pago/${d[1]}/${d[2]}/{{ usuario.ID if usuario else '' }}/${pin}`)
                    .then(r => r.json()).then(j => {
                        if(j.status=='ok') {
                            document.getElementById('snd_cash').play();
                            alert("PAGO EXITOSO");
                            location.reload();
                        } else { alert("ERROR DE PAGO"); location.reload(); }
                    });
                }
            });
        }
    </script>
</body>
</html>
'''

# --- LÓGICA DE RUTAS ---
@app.route('/')
def index():
    if 'u' not in session: return render_template_string(HTML_APP, vista='login', usuario=None)
    users = obtener_usuarios()
    u = users.get(session['u'])
    if not u: return redirect('/logout')
    return render_template_string(HTML_APP, vista='main', usuario=u)

@app.route('/login', methods=['POST'])
def login():
    uid, pin = request.form.get('id'), request.form.get('pin')
    users = obtener_usuarios()
    if uid in users and users[uid]['PIN'] == pin: session['u'] = uid
    return redirect('/')

@app.route('/reportar', methods=['POST'])
def reportar():
    with open(DB_RECARGAS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([session.get('u'), request.form.get('ref'), request.form.get('monto'), "PENDIENTE", datetime.datetime.now().strftime("%d/%m %H:%M")])
    return redirect('/')

@app.route('/pago/<emi>/<mon>/<rec>/<pin>')
def pago(emi, mon, rec, pin):
    users = obtener_usuarios()
    try:
        m = float(mon)
        if emi in users and users[emi]['PIN'] == pin and float(users[emi]['Saldo_Bs']) >= m:
            users[emi]['Saldo_Bs'] = f"{float(users[emi]['Saldo_Bs']) - m:.2f}"
            users[rec]['Saldo_Bs'] = f"{float(users[rec]['Saldo_Bs']) + m:.2f}"
            with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
                writer.writeheader()
                for u in users.values(): writer.writerow(u)
            return jsonify({"status": "ok"})
    except: pass
    return jsonify({"status": "error"})

@app.route('/panel_control')
def panel_control():
    if session.get('u') != 'admin': return redirect('/')
    users = obtener_usuarios()
    recs = []
    if os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader: recs.append(row)
    return render_template_string('''<body style="background:#000;color:#D4AF37;padding:20px;"><h2>Panel</h2><p>{{recs}}</p><a href="/">Volver</a></body>''', recs=recs)

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
    # ESTO ES LO MÁS IMPORTANTE PARA LA NUBE:
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))