from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

app = Flask(__name__)
app.secret_key = 'willpay_contable_2026'

# Bases de Datos
DB_USUARIOS = 'db_usuarios_v21.csv'
DB_RECARGAS = 'db_recargas_v21.csv'
DB_HISTORIAL = 'db_historial_v21.csv'

def inicializar_db():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            writer.writerow(["admin", "Administrador", "V-000", "0.0", "prestador", "1234"])
    if not os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID_User", "Referencia", "Monto_Bs", "Status"])
    if not os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Emisor", "Receptor", "Monto", "Concepto"])

def obtener_usuarios():
    data = {}
    if os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader: data[row['ID']] = row
    return data

def registrar_movimiento(emisor, receptor, monto, concepto):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DB_HISTORIAL, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([fecha, emisor, receptor, monto, concepto])

@app.route('/logo')
def logo(): return send_from_directory(os.getcwd(), 'logo will-pay.jpg')

HTML_APP = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background: #000; color: white; text-align: center; font-family: sans-serif; }
        .will-card { 
            background: #111; border: 1px solid #d4af37; border-radius: 30px; 
            padding: 25px; margin: 20px auto; max-width: 400px; 
        }
        .btn-gold { background: #d4af37; color: #000; font-weight: bold; border-radius: 12px; padding: 12px; border: none; width: 100%; text-decoration: none; display: block; }
        .btn-outline-gold { background: transparent; color: #d4af37; border: 1px solid #d4af37; border-radius: 12px; padding: 10px; width: 100%; text-decoration: none; display: block; }
        .monto-display { background: transparent; border: 1px solid #333; border-radius: 15px; color: #d4af37; font-size: 2.5rem; width: 100%; margin: 15px 0; padding: 5px; }
        .historial-item { background: #1a1a1a; border-radius: 10px; padding: 10px; margin-bottom: 5px; text-align: left; border-left: 3px solid #d4af37; }
        .admin-banner { background: #ffc107; color: black; border-radius: 20px; padding: 20px; font-weight: bold; margin-bottom: 20px; font-size: 1.2rem; }
    </style>
</head>
<body>
    <img src="/logo" style="width: 200px; margin: 15px auto; display: block; border-radius: 10px;">
    <div class="container" style="max-width: 450px;">
        {% if vista == 'landing' %}
        <div class="will-card">
            <h2 class="fw-bold mb-4" style="color:#d4af37">WILL-PAY</h2>
            <a href="/login_view" class="btn-gold mb-3">INICIAR SESIÓN</a>
            <a href="/registro_view" class="btn-outline-gold">REGISTRARSE</a>
        </div>
        {% elif vista == 'login' %}
        <div class="will-card">
            <h4 style="color:#d4af37" class="mb-3">ENTRAR</h4>
            <form action="/procesar_login" method="POST">
                <input type="text" name="telefono" class="form-control mb-2 bg-dark text-white" placeholder="Usuario / Teléfono" required>
                <input type="password" name="pin" class="form-control mb-3 bg-dark text-white" placeholder="PIN" required>
                <button type="submit" class="btn-gold">INGRESAR</button>
            </form>
        </div>
        {% elif vista == 'registro' %}
        <div class="will-card">
            <h4 style="color:#d4af37" class="mb-3">REGISTRO</h4>
            <form action="/procesar_registro" method="POST">
                <input type="text" name="nombre" class="form-control mb-2 bg-dark text-white" placeholder="Nombre Completo" required>
                <input type="text" name="telefono" class="form-control mb-2 bg-dark text-white" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control mb-3 bg-dark text-white" placeholder="PIN 4 dígitos" maxlength="4" required>
                <button type="submit" class="btn-gold">CREAR CUENTA</button>
            </form>
        </div>
        {% elif vista == 'main' %}
        <div class="will-card">
            {% if usuario.ID == 'admin' %}<div class="badge bg-danger mb-2">MODO ADMINISTRADOR</div>{% endif %}
            <p class="text-secondary mb-1">Saldo Disponible</p>
            <h2 class="fw-bold" style="color:#d4af37">Bs. {{ "%.2f"|format(usuario.Saldo_Bs|float) }}</h2>
            <div class="d-flex gap-2 mt-3 mb-3">
                <button class="btn btn-sm btn-outline-warning w-100" onclick="document.getElementById('sec_rec').style.display='block'">RECARGAR</button>
                {% if usuario.ID == 'admin' %}<a href="/pantalla_admin" class="btn btn-sm btn-danger w-100">REPORTES</a>{% endif %}
            </div>
            <div id="sec_rec" style="display:none;" class="bg-dark p-2 border border-warning rounded mb-3">
                <form action="/reportar_pago" method="POST">
                    <input type="text" name="ref" class="form-control form-control-sm mb-1" placeholder="Referencia">
                    <input type="number" name="monto" class="form-control form-control-sm mb-1" placeholder="Monto Bs.">
                    <button class="btn btn-success btn-sm w-100">REPORTAR</button>
                </form>
            </div>
            <div class="btn-group w-100 mb-3">
                <a href="/set_rol/pasajero" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'pasajero' else 'btn-outline-secondary' }}">PAGAR</a>
                <a href="/set_rol/prestador" class="btn btn-sm {{ 'btn-warning' if usuario.Rol == 'prestador' else 'btn-outline-secondary' }}">COBRAR</a>
            </div>
            {% if usuario.Rol == 'pasajero' %}
                <div class="monto-display" id="disp">0.00</div>
                <input type="range" class="form-range mb-3" min="0" max="1000" step="1" oninput="actQR(this.value)">
                <div class="bg-white p-2 d-inline-block rounded"><img id="q" src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WILLPAY|{{usuario.ID}}|0"></div>
                <p class="small text-secondary mt-2">Muestra este QR al chofer</p>
            {% else %}
                <video id="v" style="width:100%; display:none; border-radius:15px;"></video>
                <button id="bc" class="btn-gold" onclick="scan()">📷 COBRAR PASAJE</button>
            {% endif %}
            <hr style="border-color: #333;">
            <div style="max-height: 180px; overflow-y: auto;">
                {% for mov in historial %}
                <div class="historial-item">
                    <div class="d-flex justify-content-between">
                        <span>{{ mov.Concepto }}</span>
                        <b class="{{ 'text-success' if mov.Receptor == usuario.ID else 'text-danger' }}">Bs. {{ mov.Monto }}</b>
                    </div>
                    <small class="text-secondary" style="font-size:0.6rem;">{{ mov.Fecha }}</small>
                </div>
                {% endfor %}
            </div>
            <a href="/logout" class="text-danger d-block mt-3 small">Cerrar Sesión</a>
        </div>
        {% elif vista == 'admin' %}
        <div class="will-card" style="border:none;">
            <div class="admin-banner">💰 COMISIONES TOTALES: Bs. 0.00</div>
            <h5 class="text-start">Pagos Pendientes</h5>
            <hr>
            {% for r in recargas %}
            <div class="text-start mb-2 p-2 border-bottom border-secondary d-flex justify-content-between align-items-center">
                <small>User: {{ r.ID_User }} | Bs. {{ r.Monto_Bs }}</small>
                <a href="/aprobar/{{r.ID_User}}/{{r.Monto_Bs}}/{{r.Referencia}}" class="btn btn-success btn-sm">APROBAR</a>
            </div>
            {% endfor %}
            <a href="/" class="btn btn-outline-light w-100 mt-4">Volver</a>
        </div>
        {% endif %}
    </div>
    <script>
        function actQR(v){
            document.getElementById('disp').innerText = parseFloat(v).toFixed(2);
            document.getElementById('q').src=`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WILLPAY|{{usuario.ID}}|${v}`;
        }
        function scan(){
            const cr = new ZXing.BrowserQRCodeReader();
            document.getElementById('v').style.display='block';
            document.getElementById('bc').style.display='none';
            cr.decodeFromVideoDevice(null, 'v', (res) => {
                if(res){
                    const d = res.text.split('|');
                    let p = prompt("PIN del pasajero:");
                    fetch(`/procesar_pago/${d[1]}/${d[2]}/{{usuario.ID}}/${p}`)
                    .then(r=>r.json()).then(j=>{
                        if(j.status=='ok'){ alert("PAGO EXITOSO"); location.reload(); }
                        else alert("ERROR");
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
    if 'user_id' not in session: return render_template_string(HTML_APP, vista='landing')
    u = obtener_usuarios().get(session['user_id'])
    if not u: return redirect('/logout')
    hist = []
    if os.path.exists(DB_HISTORIAL):
        with open(DB_HISTORIAL, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Emisor'] == u['ID'] or row['Receptor'] == u['ID']: hist.append(row)
    return render_template_string(HTML_APP, vista='main', usuario=u, historial=hist[::-1])

@app.route('/login_view')
def login_view(): return render_template_string(HTML_APP, vista='login')
@app.route('/registro_view')
def registro_view(): return render_template_string(HTML_APP, vista='registro')

@app.route('/procesar_login', methods=['POST'])
def procesar_login():
    t, p = request.form.get('telefono'), request.form.get('pin')
    u = obtener_usuarios()
    if t in u and u[t]['PIN'] == p:
        session['user_id'] = t
        return redirect('/')
    return "Error. <a href='/'>Volver</a>"

@app.route('/procesar_registro', methods=['POST'])
def procesar_registro():
    t, n, p = request.form.get('telefono'), request.form.get('nombre'), request.form.get('pin')
    u = obtener_usuarios()
    if t not in u:
        with open(DB_USUARIOS, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([t, n, "V-000", "0.0", "pasajero", p])
    session['user_id'] = t
    return redirect('/')

@app.route('/pantalla_admin')
def pantalla_admin():
    if session.get('user_id') != 'admin': return "No"
    recs = []
    if os.path.exists(DB_RECARGAS):
        with open(DB_RECARGAS, 'r') as f:
            for r in csv.DictReader(f):
                if r['Status'] == 'PENDIENTE': recs.append(r)
    return render_template_string(HTML_APP, vista='admin', recargas=recs, usuario={'ID':'admin'})

@app.route('/aprobar/<uid>/<monto>/<ref>')
def aprobar(uid, monto, ref):
    users = obtener_usuarios()
    if uid in users:
        users[uid]['Saldo_Bs'] = str(float(users[uid]['Saldo_Bs']) + float(monto))
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for u in users.values(): w.writerow(u)
        registrar_movimiento("SISTEMA", uid, monto, "Recarga Aprobada")
    return redirect('/pantalla_admin')

@app.route('/procesar_pago/<emisor>/<monto>/<receptor>/<pin>')
def procesar_pago(emisor, monto, receptor, pin):
    users = obtener_usuarios()
    m = float(monto)
    if emisor in users and users[emisor]['PIN'] == pin and float(users[emisor]['Saldo_Bs']) >= m:
        users[emisor]['Saldo_Bs'] = str(float(users[emisor]['Saldo_Bs']) - m)
        users[receptor]['Saldo_Bs'] = str(float(users[receptor]['Saldo_Bs']) + m)
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN"])
            w.writeheader()
            for u in users.values(): w.writerow(u)
        registrar_movimiento(emisor, receptor, monto, "Pago de Pasaje")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route('/reportar_pago', methods=['POST'])
def reportar_pago():
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
    app.run(host='0.0.0.0', port=8000)
