from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

# --- CONFIGURACIÓN ---
app = Flask(__name__)
app.secret_key = 'willpay_2026_modular_v4'

DB_USUARIOS = 'usuarios_v1.csv'
DB_RECARGAS = 'recargas_v1.csv'
DB_HISTORIAL = 'historial_v1.csv'
PORCENTAJE_COMISION = 0.015  # 1.5%

def inicializar_db():
    if not os.path.exists(DB_USUARIOS) or os.stat(DB_USUARIOS).st_size == 0:
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            writer.writerow(["admin", "Admin Will-Pay", "V-000", "0.0", "prestador", "1234"])
            writer.writerow(["SISTEMA_GANANCIAS", "Pote de Comisiones", "999", "0.0", "admin", "9999"])
    
    for db in [DB_RECARGAS, DB_HISTORIAL]:
        if not os.path.exists(db):
            with open(db, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if db == DB_RECARGAS: writer.writerow(["ID_User", "Referencia", "Monto_Bs", "Status"])
                else: writer.writerow(["Fecha", "Emisor", "Receptor", "Monto", "Concepto"])

def obtener_usuarios():
    usuarios = {}
    if os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader: usuarios[row['ID']] = row
    return usuarios

def registrar_movimiento(emisor, receptor, monto, concepto):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DB_HISTORIAL, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([fecha, emisor, receptor, monto, concepto])

# --- INTERFAZ HTML ---
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
        body { background-color: #000; color: #fff; font-family: 'Segoe UI', sans-serif; }
        .will-container { max-width: 450px; margin: 20px auto; padding: 20px; text-align: center; }
        .main-card { background: #111; border: 2px solid #d4af37; border-radius: 25px; padding: 30px; box-shadow: 0 0 15px rgba(212,175,55,0.2); }
        .btn-gold { background-color: #d4af37; color: #000; font-weight: bold; border-radius: 12px; width: 100%; border:none; padding: 12px; }
        .saldo-display { color: #d4af37; font-size: 2.5rem; font-weight: bold; }
        .historial-item { background: #1a1a1a; border-left: 4px solid #d4af37; padding: 8px; margin-bottom: 5px; text-align: left; border-radius: 8px; }
        .modulo-admin { border: 1px solid #444; padding: 15px; border-radius: 15px; margin-top: 15px; background: #0a0a0a; }
    </style>
</head>
<body>
    <div class="will-container">
        <img src="https://via.placeholder.com/180x80/000/d4af37?text=Will-Pay" style="width:180px; margin-bottom:20px;">
        
        {% if vista == 'landing' %}
        <div class="main-card">
            <h2 style="color: #d4af37; font-weight: bold;">WILL-PAY</h2>
            <div class="mt-4">
                <a href="/login_view" class="btn-gold d-block mb-3 text-decoration-none">INICIAR SESIÓN</a>
                <a href="/registro_view" class="btn btn-outline-light w-100">REGISTRARSE</a>
            </div>
        </div>

        {% elif vista == 'login' %}
        <div class="main-card">
            <h4 style="color: #d4af37;">Ingresar</h4>
            <form action="/procesar_login" method="POST">
                <input type="text" name="telefono" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control bg-dark text-white border-secondary mb-4" placeholder="PIN" required>
                <button type="submit" class="btn-gold">ENTRAR</button>
            </form>
        </div>

        {% elif vista == 'main' %}
        <div class="main-card">
            {% if usuario.ID == 'admin' %}<div class="badge bg-danger mb-2">MODO ADMINISTRADOR</div>{% endif %}
            <div class="saldo-display">Bs. {{ "%.2f"|format(usuario.Saldo_Bs|float) }}</div>
            
            <div class="d-flex gap-2 my-3">
                <button class="btn btn-sm btn-outline-warning w-100" onclick="document.getElementById('div_recarga_user').style.display='block'">RECARGAR</button>
                {% if usuario.ID == 'admin' %}<a href="/pantalla_admin" class="btn btn-sm btn-danger w-100">REPORTES</a>{% endif %}
            </div>

            <div id="div_recarga_user" style="display:none;" class="bg-dark p-3 rounded border border-warning mb-3">
                <small class="text-warning d-block mb-2">Reportar Pago Móvil al Admin</small>
                <form action="/reportar_pago" method="POST">
                    <input type="text" name="ref" class="form-control form-control-sm mb-2 bg-dark text-white" placeholder="Nro de Referencia" required>
                    <input type="number" name="monto" class="form-control form-control-sm mb-2 bg-dark text-white" placeholder="Monto Bs." required>
                    <button class="btn btn-success btn-sm w-100">Enviar Reporte</button>
                </form>
            </div>

            {% if usuario.ID == 'admin' %}
            <div class="modulo-admin">
                <h6 class="text-warning small mb-3">CENTRO DE CARGA DIRECTA</h6>
                <form action="/recarga_directa_admin" method="POST">
                    <input type="text" name="target_user" class="form-control form-control-sm mb-2 bg-dark text-white border-warning" placeholder="Teléfono del Usuario" required>
                    <input type="number" step="0.01" name="monto" class="form-control form-control-sm mb-2 bg-dark text-white border-warning" placeholder="Monto a Cargar Bs." required>
                    <input type="text" name="ref" class="form-control form-control-sm mb-3 bg-dark text-white border-warning" placeholder="Referencia Interna" required>
                    <button class="btn btn-warning btn-sm w-100" style="font-weight:bold;">EJECUTAR RECARGA</button>
                </form>
            </div>
            {% endif %}

            <div class="btn-group w-100 my-4">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
            </div>

            {% if usuario.Rol == 'pasajero' %}
                <div class="bg-white p-3 d-inline-block rounded-4">
                    <img id="img_qr" src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=WILLPAY|{{usuario.ID}}|10">
                </div>
                <p class="mt-2 small text-secondary">Escanea para pagar 10.00 Bs.</p>
            {% else %}
                <div id="scanner_container" style="display:none;"><video id="webcam_video" style="width: 100%; border-radius: 15px; border: 2px solid #d4af37;"></video></div>
                <button id="btn_scan" class="btn-gold py-3" onclick="iniciarEscaneo()">📷 COBRAR PASAJE</button>
            {% endif %}

            <div class="mt-4" style="max-height: 150px; overflow-y: auto;">
                {% for item in historial %}
                <div class="historial-item small">
                    <div class="d-flex justify-content-between">
                        <span>{{ item.Concepto }}</span>
                        <b class="{{ 'text-success' if item.Receptor == usuario.ID else 'text-danger' }}">
                            {{ '+' if item.Receptor == usuario.ID else '-' }}{{ item.Monto }} Bs.
                        </b>
                    </div>
                </div>
                {% endfor %}
            </div>
            <a href="/logout" class="text-danger small d-block mt-3 text-decoration-none">Cerrar Sesión</a>
        </div>

        {% elif vista == 'admin' %}
        <div class="main-card">
            <h6 class="text-warning mb-3">Solicitudes Pendientes</h6>
            {% for r in recargas %}
            <div class="bg-dark p-2 mb-2 rounded d-flex justify-content-between align-items-center border border-secondary">
                <div class="text-start small">
                    <b>{{ r.ID_User }}</b><br>Bs. {{ r.Monto_Bs }}
                </div>
                <a href="/aprobar/{{r.ID_User}}/{{r.Monto_Bs}}/{{r.Referencia}}" class="btn btn-success btn-sm">APROBAR</a>
            </div>
            {% endfor %}
            <a href="/" class="btn btn-outline-light w-100 mt-3">Volver al Panel</a>
        </div>
        {% endif %}
    </div>

    <audio id="audio_pago" src="https://www.myinstants.com/media/sounds/cash-register-purchase.mp3"></audio>

    <script>
        function iniciarEscaneo() {
            const codeReader = new ZXing.BrowserQRCodeReader();
            document.getElementById('scanner_container').style.display = 'block';
            document.getElementById('btn_scan').style.display = 'none';
            codeReader.decodeFromVideoDevice(null, 'webcam_video', (result) => {
                if (result) {
                    const datos = result.text.split('|');
                    let pin = prompt(`Cobrar a ${datos[1]}\\nIngrese PIN del Pasajero:`);
                    if (pin) {
                        fetch(`/procesar_pago/${datos[1]}/${datos[2]}/{{usuario.ID if usuario else ''}}/${pin}`)
                        .then(res => res.json()).then(data => {
                            if(data.status === 'ok') {
                                document.getElementById('audio_pago').play();
                                setTimeout(() => { alert("¡PAGO EXITOSO!"); location.reload(); }, 500);
                            } else { alert("ERROR: Saldo o PIN incorrecto"); location.reload(); }
                        });
                    }
                }
            });
        }
    </script>
</body>
</html>
'''

# --- MÓDULO NUEVO: RECARGA DIRECTA ADMIN (INDEPENDIENTE) ---
@app.route('/recarga_directa_admin', methods=['POST'])
def recarga_directa_admin():
    if session.get('user_id') != 'admin': return "No autorizado"
    
    target = request.form.get('target_user')
    monto = request.form.get('monto')
    referencia = request.form.get('ref')
    
    u = obtener_usuarios()
    if target in u:
        # Sumar saldo al usuario destino
        u[target]['Saldo_Bs'] = str(round(float(u[target]['Saldo_Bs']) + float(monto), 2))
        
        # Guardar en CSV de usuarios
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for row in u.values(): w.writerow(row)
        
        # Registrar en el historial
        registrar_movimiento("ADMIN", target, monto, f"Recarga Directa (Ref: {referencia})")
        return redirect('/')
    else:
        return "El usuario no existe. <a href='/'>Volver</a>"

# --- RESTO DE RUTAS (SE MANTIENEN IGUAL) ---
@app.route('/')
def index():
    if 'user_id' not in session: return render_template_string(HTML_LAYOUT, vista='landing', usuario=None)
    usuarios = obtener_usuarios()
    u = usuarios.get(session['user_id'])
    if not u: return redirect('/logout')
    hist = []
    if os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Emisor'] == u['ID'] or row['Receptor'] == u['ID']: hist.append(row)
    return render_template_string(HTML_LAYOUT, vista='main', usuario=u, historial=hist[::-1])

@app.route('/procesar_pago/<emisor>/<monto>/<receptor>/<pin>')
def procesar_pago(emisor, monto, receptor, pin):
    u = obtener_usuarios()
    m = float(monto)
    if emisor in u and u[emisor]['PIN'] == pin and float(u[emisor]['Saldo_Bs']) >= m:
        comision = round(m * PORCENTAJE_COMISION, 2)
        monto_final = round(m - comision, 2)
        u[emisor]['Saldo_Bs'] = str(round(float(u[emisor]['Saldo_Bs']) - m, 2))
        u[receptor]['Saldo_Bs'] = str(round(float(u[receptor]['Saldo_Bs']) + monto_final, 2))
        u['SISTEMA_GANANCIAS']['Saldo_Bs'] = str(round(float(u['SISTEMA_GANANCIAS']['Saldo_Bs']) + comision, 2))
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for row in u.values(): w.writerow(row)
        registrar_movimiento(emisor, receptor, monto_final, "Pago Pasaje")
        registrar_movimiento(emisor, "SISTEMA", comision, "Comisión Will-Pay (1.5%)")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    t, n, p = request.form.get('telefono'), request.form.get('nombre'), request.form.get('pin')
    inicializar_db()
    u = obtener_usuarios()
    if t not in u:
        with open(DB_USUARIOS, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([t, n, "V-000", "0.0", "pasajero", p])
    session['user_id'] = t
    return redirect('/')

@app.route('/procesar_login', methods=['POST'])
def procesar_login():
    t, p = request.form.get('telefono'), request.form.get('pin')
    u = obtener_usuarios()
    if t in u and u[t]['PIN'] == p:
        session['user_id'] = t
        return redirect('/')
    return "Error. <a href='/login_view'>Reintentar</a>"

@app.route('/pantalla_admin')
def pantalla_admin():
    if session.get('user_id') != 'admin': return "No"
    recs = []
    if os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['Status'] == 'PENDIENTE': recs.append(r)
    return render_template_string(HTML_LAYOUT, vista='admin', recargas=recs, usuario={'ID':'admin'})

@app.route('/aprobar/<uid>/<monto>/<ref>')
def aprobar(uid, monto, ref):
    if session.get('user_id') != 'admin': return "No"
    users = obtener_usuarios()
    if uid in users:
        users[uid]['Saldo_Bs'] = str(round(float(users[uid]['Saldo_Bs']) + float(monto), 2))
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for row in users.values(): w.writerow(row)
        registrar_movimiento("SISTEMA", uid, monto, "Recarga Aprobada")
    return redirect('/pantalla_admin')

@app.route('/reportar_pago', methods=['POST'])
def reportar_pago():
    if 'user_id' in session:
        with open(DB_RECARGAS, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([session['user_id'], request.form.get('ref'), request.form.get('monto'), "PENDIENTE"])
    return redirect('/')

@app.route('/set_rol/<r>')
def set_rol(r):
    u = obtener_usuarios()
    if session.get('user_id') in u:
        u[session['user_id']]['Rol'] = r
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for row in u.values(): w.writerow(row)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=10000)
