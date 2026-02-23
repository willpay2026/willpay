from flask import Flask, render_template_string, request, redirect, session, jsonify, send_from_directory
import csv, os

app = Flask(__name__)
app.secret_key = 'willpay_ultra_fix_2026'

# CAMBIAMOS EL NOMBRE AQUÍ PARA QUE EL SISTEMA CREE UNA BASE DE DATOS LIMPIA
DB_USUARIOS = 'db_usuarios_final.csv' 

def inicializar_db():
    # Si el archivo no existe, lo crea con los títulos correctos
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cedula", "Saldo_Bs", "Rol", "PIN", "Status_KYC", "Tipo_Servicio"])
            writer.writerow(["admin", "Admin Central", "0", "3110.00", "admin", "1234", "ACTIVO", "SISTEMA"])

def obtener_usuarios():
    data = {}
    if not os.path.exists(DB_USUARIOS):
        inicializar_db()
    try:
        with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('ID'): # Solo si existe la columna ID
                    data[row['ID']] = row
    except Exception as e:
        print(f"Error leyendo DB: {e}")
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
        .btn-will { background: #D4AF37; color: #000; font-weight: bold; border-radius: 12px; border: none; padding: 12px; width: 100%; text-decoration: none; display: inline-block; }
        .form-control { background: #111; border: 1px solid #333; color: white; margin-bottom: 15px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container py-5">
        <img src="/logo" style="width: 140px; margin-bottom: 20px;">
        {% if vista == 'login' %}
        <div class="will-container">
            <h4 class="gold mb-4">INICIAR SESIÓN</h4>
            <form action="/login" method="POST">
                <input type="text" name="id" class="form-control text-center" placeholder="Usuario" required>
                <input type="password" name="pin" class="form-control text-center" placeholder="PIN" required>
                <button class="btn-will">ENTRAR</button>
            </form>
        </div>
        {% elif vista == 'main' %}
        <div class="will-container">
            <span class="badge border border-warning text-warning mb-2">{{ usuario.Tipo_Servicio }}</span>
            <p class="mb-1 small text-secondary">Saldo Disponible</p>
            <h2 class="gold" style="font-size: 2.5rem;">Bs. {{ usuario.Saldo_Bs }}</h2>
            <div class="my-4">
                {% if usuario.ID == 'admin' %}
                <a href="/panel" class="btn-will">REGISTRAR USUARIO</a>
                {% endif %}
            </div>
            <a href="/logout" class="text-danger small text-decoration-none">Cerrar Sesión</a>
        </div>
        {% elif vista == 'admin' %}
        <div class="will-container">
            <h4 class="gold mb-4">NUEVO USUARIO</h4>
            <form action="/crear" method="POST">
                <input type="text" name="new_id" class="form-control" placeholder="Teléfono / ID" required>
                <input type="text" name="new_nom" class="form-control" placeholder="Nombre Completo" required>
                <input type="password" name="new_pin" class="form-control" placeholder="PIN de 4 dígitos" required>
                <button class="btn-will">GUARDAR USUARIO</button>
            </form>
            <a href="/" class="text-white small d-block mt-3">Volver</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(HTML_APP, vista='login', usuario=None)
    users = obtener_usuarios()
    u = users.get(session['u'])
    if not u and session['u'] == 'admin':
        u = {"ID":"admin", "Nombre":"Admin", "Saldo_Bs":"3110.00", "Tipo_Servicio":"SISTEMA"}
    return render_template_string(HTML_APP, vista='main', usuario=u) if u else redirect('/logout')

@app.route('/login', methods=['POST'])
def login():
    uid, pin = request.form.get('id'), request.form.get('pin')
    if uid == 'admin' and pin == '1234':
        session['u'] = 'admin'
    else:
        users = obtener_usuarios()
        if uid in users and users[uid]['PIN'] == pin: session['u'] = uid
    return redirect('/')

@app.route('/panel')
def panel():
    if session.get('u') != 'admin': return redirect('/')
    return render_template_string(HTML_APP, vista='admin', usuario={"ID":"admin"})

@app.route('/crear', methods=['POST'])
def crear():
    if session.get('u') == 'admin':
        uid, nom, pin = request.form.get('new_id'), request.form.get('new_nom'), request.form.get('new_pin')
        with open(DB_USUARIOS, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([uid, nom, "0", "0.00", "pasajero", pin, "ACTIVO", "CLIENTE"])
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
