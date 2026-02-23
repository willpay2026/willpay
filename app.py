from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

# --- CONFIGURACIÓN DE LA APP ---
app = Flask(__name__)
app.secret_key = 'willpay_2026_key_secure'

# Nombres de archivos de base de datos
DB_USUARIOS = 'usuarios_v1.csv'
DB_RECARGAS = 'recargas_v1.csv'
DB_HISTORIAL = 'historial_v1.csv'

def inicializar_db():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            # Usuario administrador inicial
            writer.writerow(["admin", "Admin Will-Pay", "V-000", "0.0", "prestador", "1234"])
    
    if not os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID_User", "Referencia", "Monto_Bs", "Status"])
            
    if not os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Emisor", "Receptor", "Monto", "Concepto"])

def obtener_usuarios():
    usuarios = {}
    if os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                usuarios[row['ID']] = row
    return usuarios

def registrar_movimiento(emisor, receptor, monto, concepto):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DB_HISTORIAL, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([fecha, emisor, receptor, monto, concepto])

# Servir el logo si existe en la carpeta raíz
@app.route('/logo')
def logo():
    return send_from_directory(os.getcwd(), 'logo will-pay.jpg')

# --- INTERFAZ HTML (Diseño Dorado y Negro) ---
HTML_LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background-color: #000; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .will-container { max-width: 450px; margin: 20px auto; padding: 20px; text-align: center; }
        .logo-img { width: 180px; margin-bottom: 20px; border-radius: 10px; }
        .main-card { 
            background: #111; border: 2px solid #d4af37; border-radius: 25px; 
            padding: 30px; box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
        }
        .btn-gold { 
            background-color: #d4af37; color: #000; border: none; font-weight: bold; 
            border-radius: 12px; padding: 12px; width: 100%; transition: 0.3s;
        }
        .btn-gold:hover { background-color: #b8962e; color: #000; }
        .btn-outline-gold { 
            background: transparent; color: #d4af37; border: 1px solid #d4af37; 
            border-radius: 12px; padding: 10px; width: 100%; text-decoration: none; display: block;
        }
        .saldo-display { color: #d4af37; font-size: 2.5rem; font-weight: bold; margin: 10px 0; }
        .monto-selector { background: transparent; border: 1px solid #444; border-radius: 15px; color: #d4af37; font-size: 2rem; padding: 10px; width: 100%; margin: 15px 0; }
        .admin-banner { background: #ffc107; color: #000; font-weight: bold; padding: 15px; border-radius: 15px; margin-bottom: 20px; }
        .historial-item { background: #1a1a1a; border-left: 4px solid #d4af37; padding: 10px; margin-bottom: 10px; border-radius: 8px; text-align: left; }
    </style>
</head>
<body>
    <div class="will-container">
        <img src="/logo" class="logo-img" onerror="this.src='https://via.placeholder.com/180x80/000/d4af37?text=Will-Pay'">
        
        {% if vista == 'landing' %}
        <div class="main-card">
            <h2 style="color: #d4af37; font-weight: bold; letter-spacing: 1px;">WILL-PAY</h2>
            <p class="text-secondary small">Tu Billetera Digital de Confianza</p>
            <div class="mt-4">
                <a href="/login_view" class="btn-gold d-block mb-3 text-decoration-none">INICIAR SESIÓN</a>
                <a href="/registro_view" class="btn-outline-gold">REGISTRARSE</a>
            </div>
        </div>

        {% elif vista == 'login' %}
        <div class="main-card">
            <h4 class="mb-4" style="color: #d4af37;">Ingresar</h4>
            <form action="/procesar_login" method="POST">
                <input type="text" name="telefono" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Teléfono / Usuario" required>
                <input type="password" name="pin" class="form-control bg-dark text-white border-secondary mb-4" placeholder="PIN" required>
                <button type="submit" class="btn-gold">ENTRAR</button>
            </form>
            <a href="/" class="text-secondary small d-block mt-3 text-decoration-none">Volver</a>
        </div>

        {% elif vista == 'main' %}
        <div class="main-card">
            {% if usuario.ID == 'admin' %}
                <div class="badge bg-danger mb-3">MODO ADMINISTRADOR</div>
            {% endif %}
            
            <p class="text-secondary mb-0">Saldo Disponible</p>
            <div class="saldo-display">Bs. {{ "%.2f"|format(usuario.Saldo_Bs|float) }}</div>
            
            <div class="d-flex gap-2 mb-3">
                <button class="btn btn-sm btn-outline-warning w-100" onclick="document.getElementById('div_recarga').style.display='block'">RECARGAR</button>
                {% if usuario.ID == 'admin' %}
                    <a href="/pantalla_admin" class="btn btn-sm btn-danger w-100">REPORTES</a>
                {% endif %}
            </div>

            <div id="div_recarga" style="display:none;" class="bg-dark p-3 rounded border border-warning mb-3">
                <form action="/reportar_pago" method="POST">
                    <input type="text" name="ref" class="form-control form-control-sm mb-2" placeholder="Nro de Referencia" required>
                    <input type="number" name="monto" class="form-control form-control-sm mb-2" placeholder="Monto Bs." required>
                    <button class="btn btn-success btn-sm w-100">Enviar Reporte</button>
                </form>
            </div>

            <div class="btn-group w-100 mb-4">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'pasajero' else 'btn-dark border-secondary' }}">PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'prestador' else 'btn-dark border-secondary' }}">COBRAR</a>
            </div>

            {% if usuario.Rol == 'pasajero' %}
                <div class="monto-selector" id="val_monto">0.00</div>
                <input type="range" class="form-range mb-4" min="0" max="500" step="1" value="0" oninput="actualizarQR(this.value)">
                <div class="bg-white p-3 d-inline-block rounded-4">
                    <img id="img_qr" src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=WILLPAY|{{usuario.ID}}|0">
                </div>
                <p class="text-secondary small mt-3">Desliza para elegir el monto y muestra el QR</p>
            {% else %}
                <div id="scanner_container" style="display:none;">
                    <video id="webcam_video" style="width: 100%; border-radius: 15px; border: 2px solid #d4af37;"></video>
                </div>
                <button id="btn_scan" class="btn-gold py-3" onclick="iniciarEscaneo()">📷 COBRAR PASAJE</button>
            {% endif %}

            <hr class="border-secondary mt-5">
            <h6 class="text-start mb-3" style="color: #d4af37;">Actividad Reciente</h6>
            <div style="max-height: 200px; overflow-y: auto;">
                {% for item in historial %}
                <div class="historial-item">
                    <div class="d-flex justify-content-between">
                        <span class="small">{{ item.Concepto }}</span>
                        <span class="{{ 'text-success' if item.Receptor == usuario.ID else 'text-danger' }} fw-bold">
                            {{ '+' if item.Receptor == usuario.ID else '-' }}Bs. {{ item.Monto }}
                        </span>
                    </div>
                    <div class="text-secondary" style="font-size: 0.65rem;">{{ item.Fecha }}</div>
                </div>
                {% endfor %}
            </div>
            <a href="/logout" class="text-danger small d-block mt-4 text-decoration-none">Cerrar Sesión</a>
        </div>

        {% elif vista == 'admin' %}
        <div class="main-card" style="border-color: #ffc107;">
            <div class="admin-banner">💰 COMISIONES TOTALES: Bs. 0.00</div>
            <h6 class="text-start mb-3">Pagos por Aprobar</h6>
            <div class="list-group">
                {% for r in recargas %}
                <div class="list-group-item bg-dark text-white border-secondary d-flex justify-content-between align-items-center">
                    <div class="text-start">
                        <small class="d-block">Usuario: {{ r.ID_User }}</small>
                        <b class="text-warning">Bs. {{ r.Monto_Bs }}</b>
                    </div>
                    <a href="/aprobar/{{r.ID_User}}/{{r.Monto_Bs}}/{{r.Referencia}}" class="btn btn-success btn-sm">APROBAR</a>
                </div>
                {% endfor %}
            </div>
            <a href="/" class="btn btn-outline-light w-100 mt-4">Volver al Panel</a>
        </div>
        {% endif %}
    </div>

    <script>
        function actualizarQR(val) {
            document.getElementById('val_monto').innerText = parseFloat(val).toFixed(2);
            let qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=WILLPAY|{{usuario.ID}}|${val}`;
            document.getElementById('img_qr').src = qrUrl;
        }

        function iniciarEscaneo() {
            const codeReader = new ZXing.BrowserQRCodeReader();
            document.getElementById('scanner_container').style.display = 'block';
            document.getElementById('btn_scan').style.display = 'none';

            codeReader.decodeFromVideoDevice(null, 'webcam_video', (result, err) => {
                if (result) {
                    const datos = result.text.split('|');
                    if (datos[0] === 'WILLPAY') {
                        let pin = prompt(`Confirmar cobro de Bs. ${datos[2]} al usuario ${datos[1]}\\nIngrese PIN del pasajero:`);
                        if (pin) {
                            fetch(`/procesar_pago/${datos[1]}/${datos[2]}/{{usuario.ID}}/${pin}`)
                            .then(res => res.json())
                            .then(data => {
                                if (data.status === 'ok') {
                                    alert("¡PAGO PROCESADO CON ÉXITO!");
                                    location.reload();
                                } else {
                                    alert("ERROR: PIN incorrecto o saldo insuficiente.");
                                    location.reload();
                                }
                            });
                        }
                    }
                }
            });
        }
    </script>
</body>
</html>
'''

# --- RUTAS ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template_string(HTML_LAYOUT, vista='landing')
    
    usuarios = obtener_usuarios()
    u = usuarios.get(session['user_id'])
    if not u: return redirect('/logout')

    hist = []
    if os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Emisor'] == u['ID'] or row['Receptor'] == u['ID']:
                    hist.append(row)
    
    return render_template_string(HTML_LAYOUT, vista='main', usuario=u, historial=hist[::-1])

@app.route('/login_view')
def login_view():
    return render_template_string(HTML_LAYOUT, vista='login')

@app.route('/registro_view')
def registro_view():
    return "Módulo de registro en mantenimiento. Use admin para pruebas."

@app.route('/procesar_login', methods=['POST'])
def procesar_login():
    t = request.form.get('telefono')
    p = request.form.get('pin')
    usuarios = obtener_usuarios()
    if t in usuarios and usuarios[t]['PIN'] == p:
        session['user_id'] = t
        return redirect('/')
    return "Credenciales incorrectas. <a href='/login_view'>Reintentar</a>"

@app.route('/pantalla_admin')
def pantalla_admin():
    if session.get('user_id') != 'admin': return "No autorizado"
    recargas = []
    if os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'r') as f:
            for r in csv.DictReader(f):
                if r['Status'] == 'PENDIENTE': recargas.append(r)
    return render_template_string(HTML_LAYOUT, vista='admin', recargas=recargas, usuario={'ID':'admin'})

@app.route('/aprobar/<uid>/<monto>/<ref>')
def aprobar(uid, monto, ref):
    if session.get('user_id') != 'admin': return "No autorizado"
    usuarios = obtener_usuarios()
    if uid in usuarios:
        usuarios[uid]['Saldo_Bs'] = str(float(usuarios[uid]['Saldo_Bs']) + float(monto))
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for row in usuarios.values(): w.writerow(row)
        registrar_movimiento("SISTEMA", uid, monto, "Recarga Aprobada")
    return redirect('/pantalla_admin')

@app.route('/procesar_pago/<emisor>/<monto>/<receptor>/<pin>')
def procesar_pago(emisor, monto, receptor, pin):
    usuarios = obtener_usuarios()
    m = float(monto)
    if emisor in usuarios and usuarios[emisor]['PIN'] == pin:
        saldo_e = float(usuarios[emisor]['Saldo_Bs'])
        if saldo_e >= m:
            usuarios[emisor]['Saldo_Bs'] = str(saldo_e - m)
            usuarios[receptor]['Saldo_Bs'] = str(float(usuarios[receptor]['Saldo_Bs']) + m)
            with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
                w.writeheader()
                for row in usuarios.values(): w.writerow(row)
            registrar_movimiento(emisor, receptor, monto, "Pago Pasaje")
            return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route('/reportar_pago', methods=['POST'])
def reportar_pago():
    with open(DB_RECARGAS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([session['user_id'], request.form.get('ref'), request.form.get('monto'), "PENDIENTE"])
    return redirect('/')

@app.route('/set_rol/<r>')
def set_rol(r):
    usuarios = obtener_usuarios()
    if session.get('user_id') in usuarios:
        usuarios[session['user_id']]['Rol'] = r
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for row in usuarios.values(): w.writerow(row)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=8000)
