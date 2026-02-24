from flask import Flask, render_template_string, request, redirect, session
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_legado_wilyanny_2026'

DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(query, args)
    rv = None
    if commit:
        conn.commit()
    else:
        try: rv = cur.fetchone() if one else cur.fetchall()
        except: rv = None
    cur.close()
    conn.close()
    return rv

@app.route('/')
def index():
    u = None
    if 'u' in session:
        u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay | El Legado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; text-align: center; }
        #splash { position: fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; transition: 1s; }
        .logo-img { width: 150px; border-radius: 50%; border: 3px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 0 20px #D4AF37; }
        .oro { color: #D4AF37; font-weight: bold; }
        .card-w { background: #111; border: 1px solid #D4AF37; border-radius: 20px; padding: 25px; margin: 20px auto; max-width: 400px; }
        .btn-oro { background: #D4AF37; color: #000; font-weight: bold; border-radius: 10px; padding: 10px; width: 100%; border:none; }
        .legado-texto { font-size: 0.8rem; color: #888; font-style: italic; margin-top: 15px; }
    </style>
</head>
<body>
    <div id="splash">
        <img src="/static/logo%20will-pay.jpg" class="logo-img" onerror="this.style.display='none'">
        <h1 class="oro">WILL-PAY</h1>
        <p>Revolucionando el pago en nuestra región</p>
    </div>

    <div class="container py-5">
        <h2 class="oro">WILL-PAY</h2>
        <p class="small">Un código simple, una idea grande.</p>

        {% if not u %}
            <div class="card-w">
                <h4 class="mb-3">Entrar</h4>
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control mb-2 bg-dark text-white border-secondary">
                    <input name="p" type="password" placeholder="PIN" class="form-control mb-3 bg-dark text-white border-secondary">
                    <button class="btn-oro">INICIAR SESIÓN</button>
                </form>
                <hr class="border-secondary">
                <p class="small">¿Eres nuevo?</p>
                <button class="btn btn-outline-warning btn-sm" onclick="document.getElementById('reg').style.display='block'">CREAR CUENTA</button>
            </div>

            <div id="reg" class="card-w" style="display:none;">
                <h4 class="oro mb-3">REGISTRO</h4>
                <form action="/registro" method="POST">
                    <input name="id" placeholder="Teléfono (Será tu ID)" class="form-control mb-2 bg-dark text-white border-secondary" required>
                    <input name="nom" placeholder="Nombre Completo" class="form-control mb-2 bg-dark text-white border-secondary" required>
                    <input name="pin" type="password" placeholder="Crea tu PIN (4 dígitos)" class="form-control mb-3 bg-dark text-white border-secondary" required>
                    <button class="btn-oro">REGISTRARME</button>
                </form>
            </div>
            
            <p class="legado-texto">Este sistema es el legado para Wilyanny Donquiz, nacido del esfuerzo y la visión de Wilfredo Donquiz para su pueblo.</p>

        {% else %}
            <div class="card-w">
                <p>Bienvenido, <b class="oro">{{
