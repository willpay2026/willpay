from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2, os, datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

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

# --- INTERFAZ PREMIUM ACTUALIZADA CON SUBIDA DE CAPTURAS ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay | Una manera más sencilla de pagar</title>
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
        .logo-img { width: 320px; height: auto; margin-bottom: 5px; filter: drop-shadow(0px 0px 15px #D4AF37); border-radius: 20px; }
        .vision-text { font-size: 1.1rem; color: var(--oro); font-weight: bold; text-transform: uppercase; }
        #ticket { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); z-index:9999; padding:20px; overflow-y: auto; }
        .recibo-papel { background: white; color: black; padding: 25px; border-radius: 5px; font-family: monospace; max-width: 400px; margin: auto; border-top: 8px solid var(--oro); }
    </style>
</head>
<body>
    <div class="container text-center py-4">
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/willpay2026/willpay/main/logo%20will-pay.jpg" class="logo-img">
            <h2 class="oro-text mb-0">WILL-PAY</h2>
            <p class="vision-text">UNA MANERA MÁS SENCILLA DE PAGAR</p>
        </div>

        {% if not session.get('u') %}
            <div class="card-will" id="login_form">
                <h4 class="oro-text mb-4">INICIAR SESIÓN</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control input-will" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control input-will" required>
                    <button class="btn-will">ENTRAR</button>
                </form>
                <button class="btn btn-link text-warning mt-3" onclick="showReg()">¿Eres nuevo? Regístrate aquí</button>
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
                    <input type="number" id="val_pago" class="form-control text-center bg-transparent border-0 oro-text mb-3" style="font-size:2.5rem;" placeholder="0.00" oninput="genQR()">
                    <div class="bg-white p-2 d-inline-block rounded"><img id="q_img" src="" style="width:180px;"></div>
                {% else %}
                    <button class="btn-will py-3" onclick="scan()">📷 ESCANEAR QR</button>
                    <video id="v" style="width:100%; display:none; border-radius:15px; margin-top:10px;"></video>
                {% endif %}
                
                {% if session['u'] == '04126602555' %}
                    <hr><a href="/admin_panel" class="btn btn-sm btn-info w-100">PANEL ADMINISTRADOR / AUDITORÍA</a>
                {% endif %}
            </div>

            <div id="m_recarga" style="display:none;" class="card-will text-start">
                <h5 class="oro-text text-center">REPORTAR PAGO MÓVIL</h5>
                <p class="small text-center">Banesco | 04126602555 | V-13496133</p>
                <form action="/reportar" method="POST" enctype="multipart/form-data">
                    <input name="ref" placeholder="Referencia" class="form-control input-will" required>
                    <input name="monto" type="number" step="0.01" placeholder="Monto Bs." class="form-control input-will" required>
                    <label class="small oro-text">Adjuntar Captura:</label>
                    <input type="file" name="foto" class="form-control input-will" accept="image/*" required>
                    <button class="btn-will mt-2">ENVIAR PARA AUDITORÍA</button>
                    <button type="button" class="btn btn-link text-secondary w-100" onclick="hideRecarga()">Cancelar</button>
                </form>
            </div>
        {% endif %}
    </div>
    <script>
        function showReg() { document.getElementById('login_form').style.display='none'; document.getElementById('reg_form').style.display='block'; }
        function showRecarga() { document.getElementById('m_recarga').style.display='block'; }
        function hideRecarga() { document.getElementById('m_recarga').style.display='none'; }
        function genQR() {
            const m = document.getElementById('val_pago').value || 0;
            document.getElementById('q_img').src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=WP|{{session.u}}|${m}`;
        }
        function scan() { /* ... lógica de scan igual ... */ }
    </script>
</body>
</html>
'''

# --- LÓGICA DE AUDITORÍA ---
import base64

@app.route('/reportar', methods=['POST'])
def reportar():
    foto = request.files['foto']
    # Convertimos la foto a texto para guardarla en la BD
    foto_codificada = base64.b64encode(foto.read()).decode('utf-8')
    
    # Verificamos si la referencia ya existe (Anti-Trampa nivel 1)
    existe = query_db("SELECT id FROM recargas WHERE referencia=%s", (request.form['ref'],), one=True)
    if existe:
        return "<h1>ERROR: Esta referencia ya fue reportada.</h1><a href='/'>Volver</a>"

    query_db("INSERT INTO recargas (usuario_id, monto, referencia, estado, captura_base64) VALUES (%s, %s, %s, 'pendiente', %s)",
             (session['u'], request.form['monto'], request.form['ref'], foto_codificada), commit=True)
    return "<h1>REPORTE ENVIADO. El administrador verificará la captura.</h1><a href='/'>Volver</a>"

@app.route('/admin_panel')
def admin_panel():
    if session.get('u') != '04126602555': return "No autorizado"
    ganancias = query_db("SELECT saldo_bs FROM usuarios WHERE id='SISTEMA_GANANCIAS'", one=True)
    bolsa = ganancias['saldo_bs'] if ganancias else 0
    pendientes = query_db("SELECT * FROM recargas WHERE estado='pendiente'")
    
    html = f"<div style='background:black; color:white; padding:20px; font-family:sans-serif;'>"
    html += f"<h2 style='color:gold;'>Panel de Auditoría Will-Pay</h2>"
    html += f"<div style='background:#111; padding:15px; border-radius:15px; margin-bottom:20px;'><b>Bolsa de Comisiones:</b> Bs. {bolsa:,.2f}</div>"
    
    for r in pendientes:
        html += f"""
        <div style='border:1px solid gold; padding:15px; margin-bottom:15px; border-radius:15px; background:#111;'>
            <b>Usuario:</b> {r['usuario_id']} | <b>Monto:</b> {r['monto']} Bs | <b>Ref:</b> {r['referencia']} <br><br>
            <details>
                <summary style='color:gold; cursor:pointer;'>VER CAPTURA ADJUNTA</summary>
                <img src="data:image/png;base64,{r['captura_base64']}" style="width:100%; max-width:300px; margin-top:10px; border-radius:10px;">
            </details>
            <br>
            <a href='/aprobar/{r['id']}' style='background:lime; color:black; padding:10px; text-decoration:none; border-radius:5px; font-weight:bold;'>APROBAR</a>
            <a href='/rechazar/{r['id']}' style='background:red; color:white; padding:10px; text-decoration:none; border-radius:5px; font-weight:bold; margin-left:10px;'>RECHAZAR</a>
        </div>
        """
    html += "<br><a href='/' style='color:gold;'>← Volver</a></div>"
    return html

# --- RESTO DE RUTAS (login, registro, do_pago, aprobar, etc.) ---
# ... (Mantén todas tus rutas de index, login, registro, do_pago, aprobar, rol, logout) ...

@app.route('/actualizar_db_secreta')
def actualizar_db():
    if session.get('u') != '04126602555': return "No autorizado"
    # Añadimos la columna para la foto si no existe
    try: query_db("ALTER TABLE recargas ADD COLUMN captura_base64 TEXT;", commit=True)
    except: pass
    return "<h1>SISTEMA DE AUDITORÍA ACTIVADO</h1><a href='/'>Ir a la App</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
