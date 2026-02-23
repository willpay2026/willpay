from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import csv, os, datetime

# --- CONFIGURACIÓN ---
app = Flask(__name__)
app.secret_key = 'willpay_2026_modular_final'

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

        {% elif vista == 'registro' %}
        <div class="main-card">
            <h4 style="color: #d4af37;">Crear Cuenta</h4>
            <form action="/procesar_registro" method="POST">
                <input type="text" name="nombre" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Nombre Completo" required>
                <input type="text" name="telefono" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control bg-dark text-white border-secondary mb-4" placeholder="PIN de 4 dígitos" required>
                <button type="submit" class="btn-gold">REGISTRARME</button>
            </form>
            <a href="/" class="text-white small d-block mt-3">Volver</a>
        </div>

        {% elif vista == 'login' %}
        <div class="main-card">
            <h4 style="color: #d4af37;">Ingresar</h4>
            <form action="/procesar_login" method="POST">
                <input type="text" name="telefono" class="form-control bg-dark text-white border-secondary mb-3" placeholder="Teléfono" required>
                <input type="password" name="pin" class="form-control bg-dark text-white border-secondary mb-4" placeholder="PIN" required>
                <button type="submit" class="btn-gold">ENTRAR</button>
            </form>
            <a href="/" class="text-white small d-block mt-3">Volver</a>
        </div>

        {% elif vista == 'main' %}
        <div class="main-card">
            {% if usuario.ID == 'admin' %}<div class="badge bg-danger mb-2">MODO ADMINISTR
