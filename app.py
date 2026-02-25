from flask import Flask, render_template_string, request, redirect, session, jsonify, url_for
import psycopg2, os, datetime, base64
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

# --- INTERFAZ PREMIUM CON LOGO GRANDE Y SLOGAN ---
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
        .card-will { background: #111; border: 2px solid var(--oro); border-radius: 25px; padding: 25px; margin-top: 20px; }
        .oro-text { color: var(--oro); font-weight: bold; }
        .btn-will { background: var(--oro); color: black; font-weight: bold; border-radius: 12px; border: none; padding: 15px; width: 100%; }
        .logo-img { width: 320px; height: auto; margin-bottom: 5px; filter: drop-shadow(0px 0px 15px #D4AF37); border-radius: 20px; }
        .vision-text { font-size: 1.1rem; color: var(--oro); font-weight: bold; text-transform: uppercase; }
        .input-will { background: #222 !important; color: white !important; border: 1px solid #444 !important; margin-bottom: 10px; }
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
                
                <div class="d-flex gap-2 my-4">
                    <button class="btn btn-outline-warning w-100" onclick="document.getElementById('m_recarga').style.display='block'">RECARGAR</button>
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Salir</a>
                </div>

                {% if session['u'] == '04126602555' %}
                    <hr><a href="/admin_panel" class="btn btn-sm btn-info w-100">AUDITORÍA Y COMISIONES</a>
                {% endif %}
            </div>

            <div id="m_recarga" style="display:none;" class="card-will text-start mt-3">
                <h5 class="oro-text text-center">REPORTAR PAGO MÓVIL</h5>
                <form action="/reportar" method="POST" enctype="multipart/form-data">
                    <input name="ref" placeholder="Referencia" class="form-control input-will" required>
                    <input name="monto" type="number" step="0.01" placeholder="Monto Bs." class="form-control input-will" required>
                    <label class="small oro-text">Subir Captura (PNG/JPG):</label>
                    <input type="file" name="foto" class="form-control input-will" accept="image/*" required>
                    <button class="btn-will mt-2">ENVIAR A REVISIÓN</button>
                    <button type="button" class="btn btn-link text-secondary w-100" onclick="this.parentElement.parentElement.style.display='none'">Cancelar</button>
                </form>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''

# --- RUTAS DE REDIRECCIÓN Y LÓGICA ---

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(LAYOUT, u=None)
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    return render_template_string(LAYOUT, u=u)

# PARCHE DE ELEGANCIA: Si entran a /login, los manda al inicio
@app.route('/login')
def login_redirect():
    return redirect(url_for('index'))

@app.route('/auth_login', methods=['POST'])
def auth_login():
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect(url_for('index'))

@app.route('/reportar', methods=['POST'])
def reportar():
    foto = request.files['foto']
    foto_cod = base64.b64encode(foto.read()).decode('utf-8')
    # Evitar referencias repetidas (Anti-fraude)
    existe = query_db("SELECT id FROM recargas WHERE referencia=%s", (request.form['ref'],), one=True)
    if existe: return "<h1>Error: Referencia ya usada</h1><a href='/'>Volver</a>"
    
    query_db("INSERT INTO recargas (usuario_id, monto, referencia, estado, captura_base64) VALUES (%s, %s, %s, 'pendiente', %s)",
             (session['u'], request.form['monto'], request.form['ref'], foto_cod), commit=True)
    return "<h1>Recarga en proceso de auditoría</h1><a href='/'>Volver</a>"

@app.route('/admin_panel')
def admin_panel():
    if session.get('u') != '04126602555': return "Acceso Denegado"
    ganancias = query_db("SELECT saldo_bs FROM usuarios WHERE id='SISTEMA_GANANCIAS'", one=True)
    bolsa = ganancias['saldo_bs'] if ganancias else 0
    pendientes = query_db("SELECT * FROM recargas WHERE estado='pendiente'")
    
    html = f"<div style='background:black; color:white; padding:20px; min-height:100vh;'>"
    html += f"<h2 style='color:gold;'>Panel de Auditoría de Capturas</h2>"
    html += f"<p>Comisiones: <b>Bs. {bolsa:,.2f}</b></p><hr>"
    
    for r in pendientes:
        html += f"""
        <div style='border:2px solid gold; padding:15px; margin-bottom:15px; border-radius:15px;'>
            <b>Usuario:</b> {r['usuario_id']} | <b>Monto:</b> {r['monto']} Bs | <b>Ref:</b> {r['referencia']} <br><br>
            <img src="data:image/png;base64,{r['captura_base64']}" style="width:100%; max-width:350px; border-radius:10px;">
            <br><br>
            <a href='/aprobar/{r['id']}' style='background:lime; color:black; padding:12px; text-decoration:none; border-radius:8px; font-weight:bold;'>APROBAR PAGO</a>
        </div>
        """
    return html + "<br><a href='/' style='color:gold;'>← Regresar</a></div>"

@app.route('/aprobar/<rid>')
def aprobar(rid):
    if session.get('u') != '04126602555': return "Error"
    r = query_db("SELECT * FROM recargas WHERE id=%s", (rid,), one=True)
    if r:
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (r['monto'], r['usuario_id']), commit=True)
        query_db("UPDATE recargas SET estado='aprobado' WHERE id=%s", (rid,), commit=True)
    return redirect('/admin_panel')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
