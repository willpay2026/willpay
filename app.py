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
        .card-will { background: #111; border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin-top: 20px; position: relative; }
        .oro-text { color: var(--oro); font-weight: bold; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 12px; border: none; padding: 15px; width: 100%; }
        .saldo-display { font-size: 2.5rem; color: var(--oro); font-weight: bold; }
        .input-will { background: #222 !important; color: white !important; border: 1px solid #444 !important; margin-bottom: 10px; }
        #ticket { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:9999; padding:20px; overflow-y: auto; }
        .recibo-papel { background: white; color: black; padding: 25px; border-radius: 5px; font-family: monospace; text-align: left; max-width: 400px; margin: auto; border-top: 8px solid var(--oro); }
        .logo-container { margin-bottom: 15px; }
        .logo-img { width: 80px; height: auto; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container text-center py-4">
        <div class="logo-container">
            <img src="TU_URL_DE_LOGO_AQUI" alt="Will-Pay Logo" class="logo-img" onerror="this.style.display='none'">
            <h2 class="oro-text mb-0">WILL-PAY</h2>
            <p class="small text-secondary">Tecnología con corazón para Venezuela</p>
        </div>

        {% if not session.get('u') %}
            <div class="card-will" id="login_form">
                <h4 class="oro-text mb-4">INICIAR SESIÓN</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono / ID" class="form-control input-will" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control input-will" required>
                    <button class="btn-will">ENTRAR</button>
                </form>
                <button class="btn btn-link text-warning mt-3" onclick="showReg()">¿Eres nuevo? Regístrate aquí</button>
            </div>

            <div class="card-will" id="reg_form" style="display:none;">
                <h4 class="oro-text mb-4">CREAR CUENTA COMERCIAL</h4>
                <form action="/registro" method="POST">
                    <input name="n" placeholder="Nombre Completo o Razón Social" class="form-control input-will" required>
                    <input name="t" placeholder="Teléfono (Será su ID)" class="form-control input-will" required>
                    <input name="p" type="password" placeholder="PIN Secreto" class="form-control input-will" required>
                    
                    <select name="servicio" class="form-control input-will" required>
                        <option value="" disabled selected>Seleccione su Actividad</option>
                        <option value="PASAJERO">Pasajero / Cliente General</option>
                        <option value="CONDUCTOR INDEPENDIENTE">Conductor Independiente</option>
                        <option value="CARRITO PIRATA">Carrito Pirata</option>
                        <option value="TAXISTA">Taxista</option>
                        <option value="REPOSTERO">Repostero</option>
                        <option value="COMIDA RAPIDA">Comida Rápida</option>
                        <option value="ECONOMÍA INFORMAL">Economía Informal</option>
                        <option value="DELIVERY">Delivery</option>
                        <option value="LINEA URBANA">Línea Urbana</option>
                        <option value="LINEA EXTRA URBANA">Línea Extra Urbana</option>
                        <option value="VIAJES LARGOS">Viajes Largos</option>
                        <option value="EXPRESOS">Expresos</option>
                        <option value="ENCOMIENDAS">Encomiendas</option>
                        <option value="REPARACIONES DOMICILIO">Reparaciones a Domicilio</option>
                        <option value="ALBAÑIL">Albañil</option>
                        <option value="CLASES DIRIGIDAS">Clases Dirigidas</option>
                        <option value="COLEGIO PUBLICO">Colegio Público</option>
                        <option value="COLEGIO PRIVADO">Colegio Privado</option>
                        <option value="PANADERIA">Panadería</option>
                        <option value="FERRETERIA">Ferretería</option>
                        <option value="OTROS">Otros Servicios</option>
                    </select>

                    <button class="btn-will">REGISTRAR EN EL EMPORIO</button>
                </form>
                <button class="btn btn-link text-secondary mt-3" onclick="showLogin()">Volver al Inicio</button>
            </div>
        {% else %}
            <div class="card-will">
                <p class="mb-0 text-secondary small">Bienvenido | {{ u.servicio }}</p>
                <h4 class="oro-text">{{ u.nombre }}</h4>
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
                    <label class="small text-secondary">Monto a transferir:</label>
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
                    <input name="ref" placeholder="Referencia Bancaria" class="form-control input-will" required>
                    <input name="monto" type="number" step="0.01" placeholder="Monto Bs." class="form-control input-will" required>
                    <button class="btn-will">REPORTAR PAGO</button>
                    <button type="button" class="btn btn-link text-secondary w-100" onclick="hideRecarga()">Cancelar</button>
                </form>
            </div>
        {% endif %}
    </div>

    <div id="ticket">
        <div class="recibo-papel mt-4">
            <div class="text-center">
                <img src="TU_URL_DE_LOGO_AQUI" style="width:50px; filter: grayscale(1);">
                <h5 class="mb-0">WILL-PAY</h5>
                <p class="small">Comprobante de Servicio</p>
            </div>
            <hr>
            <p id="t_correlativo" style="font-weight:bold;"></p>
            <p id="t_fecha"></p>
            <hr>
            <p><strong>DE (Pagador):</strong><br><span id="t_emisor"></span></p>
            <p><strong>A (Beneficiario):</strong><br><span id="t_receptor"></span></p>
            <p><strong>SERVICIO:</strong><br><span id="t_servicio_detalle" style="color:#D4AF37; font-weight:bold;"></span></p>
            <hr>
            <h3 class="text-center" id="t_monto_total"></h3>
            <p class="text-center small">Ref. Digital: <span id="t_ref_banc"></span></p>
            <hr>
            <p class="text-center small" style="font-size:0.6rem;">Este recibo es un registro digital de la transacción para fines de auditoría interna en el sistema Will-Pay.</p>
            <button class="btn btn-dark w-100 mt-3" onclick="location.reload()">FINALIZAR</button>
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
                                document.getElementById('t_correlativo').innerText = j.correlativo;
                                document.getElementById('t_fecha').innerText = "FECHA: " + j.fecha_hora;
                                document.getElementById('t_emisor').innerText = j.emisor_nom + " (" + j.emisor_id + ")";
                                document.getElementById('t_receptor').innerText = j.receptor_nom + " (" + j.receptor_id + ")";
                                document.getElementById('t_servicio_detalle').innerText = j.receptor_servicio;
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
    # Registro con campo Servicio
    query_db("INSERT INTO usuarios (id, pin, nombre, saldo_bs, rol, servicio) VALUES (%s, %s, %s, 0, 'pasajero', %s)", 
             (request.form['t'], request.form['p'], request.form['n'], request.form['servicio']), commit=True)
    session['u'] = request.form['t']
    return redirect('/')

@app.route('/do_pago/<emi>/<mon>')
def do_pago(emi, mon):
    try:
        m = float(mon)
        pas = query_db("SELECT nombre, saldo_bs FROM usuarios WHERE id=%s", (emi,), one=True)
        rec = query_db("SELECT nombre, servicio FROM usuarios WHERE id=%s", (session['u'],), one=True)
        
        if pas and float(pas['saldo_bs']) >= m:
            com = m * 0.015
            neto = m - com
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (m, emi), commit=True)
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (neto, session['u']), commit=True)
            query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id='SISTEMA_GANANCIAS'", (com,), commit=True)
            
            ahora = datetime.datetime.now()
            query_db("INSERT INTO pagos (emisor_id, receptor_id, monto, fecha) VALUES (%s, %s, %s, %s)", 
                     (emi, session['u'], m, ahora), commit=True)
            
            last = query_db("SELECT id FROM pagos ORDER BY id DESC LIMIT 1", one=True)
            
            return jsonify({
                "status": "ok", "monto": m, 
                "correlativo": f"RECIBO N° WP-{last['id']:06d}",
                "fecha_hora": ahora.strftime("%d/%m/%Y %H:%M:%S"),
                "emisor_nom": pas['nombre'], "emisor_id": emi,
                "receptor_nom": rec['nombre'], "receptor_id": session['u'],
                "receptor_servicio": rec['servicio'],
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
    return f"<h2>Panel Admin Will-Pay</h2>" + "".join([f"Ref: {r['referencia']} - {r['monto']} Bs <a href='/aprobar/{r['id']}'>APROBAR</a><br>" for r in pendientes])

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
