from flask import Flask, render_template_string, request, redirect, session, send_from_directory
import csv, os

app = Flask(__name__)
app.secret_key = 'willpay_power_2026'

DB_USUARIOS = 'db_usuarios_final.csv' 

def inicializar_db():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
            writer.writerow(["admin", "Admin Central", "0", "3110.00", "admin", "1234", "ACTIVO", "SISTEMA"])

def obtener_usuarios():
    data = {}
    if not os.path.exists(DB_USUARIOS): inicializar_db()
    try:
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('ID'): data[row['ID']] = row
    except: pass
    return data

@app.route('/logo')
def logo(): 
    return send_from_directory(os.getcwd(), 'logo will-pay.jpg') if os.path.exists('logo will-pay.jpg') else "Logo"

HTML_APP = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: white; text-align: center; font-family: sans-serif; }
        .will-container { border: 2px solid #D4AF37; border-radius: 30px; padding: 25px; margin: 20px auto; max-width: 400px; background: #0a0a0a; box-shadow: 0 0 15px rgba(212, 175, 55, 0.2); }
        .gold { color: #D4AF37; font-weight: bold; }
        .btn-will { background: #D4AF37; color: #000; font-weight: bold; border-radius: 12px; border: none; padding: 12px; width: 100%; text-decoration: none; display: inline-block; margin-top: 10px; }
        .btn-outline-will { background: transparent; color: #D4AF37; font-weight: bold; border-radius: 12px; border: 2px solid #D4AF37; padding: 12px; width: 100%; text-decoration: none; display: inline-block; margin-top: 10px; }
        .form-control { background: #111; border: 1px solid #333; color: white; margin-bottom: 15px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container py-5">
        <img src="/logo" style="width: 140px; margin-bottom: 20px;">
        
        {% if vista == 'inicio' %}
        <div class="will-container">
            <h3 class="gold mb-4">BIENVENIDO</h3>
            <p class="small mb-4 text-secondary">La nueva forma de pagar tu transporte</p>
            <a href="/vista_login" class="btn-will">INICIAR SESIÓN</a>
            <a href="/vista_registro" class="btn-outline-will">CREAR CUENTA NUEVA</a>
        </div>

        {% elif vista == 'login' %}
        <div class="will-container">
            <h4 class="gold mb-4">ENTRAR</h4>
            <form action="/login" method="POST">
                <input type="text" name="id" class="form-control text-center" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control text-center" placeholder="PIN" required>
                <button class="btn-will">INGRESAR</button>
            </form>
            <a href="/" class="text-white small d-block mt-3">Volver</a>
        </div>

        {% elif vista == 'registro' %}
        <div class="will-container">
            <h4 class="gold mb-4">REGISTRO</h4>
            <form action="/crear_auto" method="POST">
                <input type="text" name="new_id" class="form-control" placeholder="Teléfono" required>
                <input type="text" name="new_nom" class="form-control" placeholder="Nombre Completo" required>
                <input type="password" name="new_pin" class="form-control" placeholder="Crea tu PIN (4 dígitos)" required>
                <button class="btn-will">CONFIRMAR REGISTRO</button>
            </form>
            <a href="/" class="text-white small d-block mt-3">Ya tengo cuenta</a>
        </div>

        {% elif vista == 'main' %}
        <div class="will-container">
            <span class="badge border border-warning text-warning mb-2">{{ usuario.Tipo_Servicio }}</span>
            <p class="mb-1 small text-secondary">Saldo Disponible</p>
            <h2 class="gold" style="font-size: 2.5rem;">Bs. {{ usuario.Saldo_Bs }}</h2>
            <div class="my-4">
                {% if usuario.ID == 'admin' %}
                <a href="/panel_control" class="btn-will">ADMINISTRAR SISTEMA</a>
                {% else %}
                <p class="small text-secondary">Escanea el QR del transporte para pagar</p>
                {% endif %}
            </div>
            <a href="/logout" class="text-danger small text-decoration-none">Cerrar Sesión</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' in session:
        users = obtener_usuarios()
        u = users.get(session['u'])
        if u: return render_template_string(HTML_APP, vista='main', usuario=u)
    return render_template_string(HTML_APP, vista='inicio')

@app.route('/vista_login')
def vista_login(): return render_template_string(HTML_APP, vista='login')

@app.route('/vista_registro')
def vista_registro(): return render_template_string(HTML_APP, vista='registro')

@app.route('/login', methods=['POST'])
def login():
    uid, pin = request.form.get('id'), request.form.get('pin')
    users = obtener_usuarios()
    if uid in users and users[uid]['PIN'] == pin:
        session['u'] = uid
        return redirect('/')
    return redirect('/vista_login')

@app.route('/crear_auto', methods=['POST'])
def crear_auto():
    uid, nom, pin = request.form.get('new_id'), request.form.get('new_nom'), request.form.get('new_pin')
    users = obtener_usuarios()
    if uid not in users:
        with open(DB_USUARIOS, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([uid, nom, "0", "0.00", "pasajero", pin, "ACTIVO", "CLIENTE"])
        session['u'] = uid # Loguear automáticamente al registrarse
    return redirect('/')

@app.route('/panel_control')
def panel_control():
    if session.get('u') != 'admin': return redirect('/')
    return render_template_string(HTML_APP, vista='registro', usuario={"ID":"admin"})

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    inicializar_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
