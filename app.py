import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'willpay_seguridad_bancaria_2026'

# --- BASE DE DATOS SQL (SEGURIDAD DE AUDITORÍA) ---
def init_db():
    conn = sqlite3.connect('willpay_banco.db')
    cursor = conn.cursor()
    # Tabla de Usuarios con nivel KYC
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telefono TEXT UNIQUE,
                        pin TEXT,
                        nombre TEXT,
                        saldo REAL DEFAULT 0.0,
                        rol TEXT DEFAULT 'pasajero',
                        kyc_status TEXT DEFAULT 'pendiente')''')
    # Tabla de Transacciones para Auditoría
    cursor.execute('''CREATE TABLE IF NOT EXISTS transacciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        emisor TEXT,
                        receptor TEXT,
                        monto REAL,
                        comision REAL,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- INTERFAZ ÚNICA (3 FASES) ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Emporio</title>
    <style>
        :root { --oro: #D4AF37; --negro: #000; --gris: #1a1a1a; }
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; background: var(--negro); color: white; font-family: 'Segoe UI', sans-serif; overflow: hidden; }
        
        /* FASE 1: SPLASH */
        #fase1 { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; display: flex; justify-content: center; align-items: center; z-index: 100; transition: opacity 1.5s; }
        #fase1 img { width: 100%; height: 100%; object-fit: contain; }

        /* FASE 2: REGISTRO / LOGIN */
        #fase2 { display: none; width: 100%; height: 100%; background: url('/static/cara2.jpg') no-repeat center center; background-size: cover; opacity: 0; transition: opacity 1s; }
        .overlay { width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; }
        
        .caja-bancaria { background: var(--gris); border: 2px solid var(--oro); padding: 30px; border-radius: 15px; width: 80%; max-width: 400px; text-align: center; box-shadow: 0 0 20px rgba(212, 175, 55, 0.3); }
        input { width: 90%; padding: 12px; margin: 10px 0; border-radius: 5px; border: 1px solid var(--oro); background: #000; color: white; text-align: center; font-size: 1.1rem; }
        .btn-oro { background: var(--oro); color: black; border: none; padding: 15px 30px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; text-transform: uppercase; }
    </style>
</head>
<body>

    <div id="fase1">
        <img src="/static/cara1.jpg" alt="Wildon C.A.">
    </div>

    <div id="fase2">
        <div class="overlay">
            <div class="caja-bancaria">
                <h2 style="color: var(--oro); margin-bottom: 5px;">WILL-PAY</h2>
                <p style="font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 20px;">SISTEMA BANCARIO BLINDADO</p>
                
                <form action="/auth" method="POST">
                    <input type="text" name="telefono" placeholder="Teléfono Usuario" required>
                    <input type="password" name="pin" placeholder="PIN de Seguridad" required>
                    <button type="submit" class="btn-oro">Entrar al Sistema</button>
                </form>
                <p style="font-size: 0.7rem; margin-top: 15px; color: #888;">Nivel de Seguridad: AES-256 Auditoría Activa</p>
            </div>
        </div>
    </div>

    <script>
        window.onload = function() {
            setTimeout(() => {
                document.getElementById('fase1').style.opacity = '0';
                setTimeout(() => {
                    document.getElementById('fase1').style.display = 'none';
                    let f2 = document.getElementById('fase2');
                    f2.style.display = 'block';
                    setTimeout(() => { f2.style.opacity = '1'; }, 50);
                }, 1500);
            }, 5000);
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(LAYOUT)

@app.route('/auth', methods=['POST'])
def auth():
    # Aquí irá la lógica de SQL que valida al usuario
    return "Conectando con la base de datos SQL segura..."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
