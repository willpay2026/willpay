from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2, os
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'willpay_emporio_fluido_2026'

# TU BASE DE DATOS (LA RAÍZ SE MANTIENE INTACTA)
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Will-Pay | Emporio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --oro: #D4AF37; --negro: #000; --gris: #111; }
        body { background: var(--negro); color: white; font-family: 'Segoe UI', sans-serif; overflow: hidden; height: 100vh; margin: 0; }
        
        /* SPLASH SCREEN ANIMADO */
        #splash {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: var(--negro); z-index: 100;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .logo-animado {
            width: 160px; height: 160px; border-radius: 50%; border: 3px solid var(--oro);
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.4);
            animation: latido 2s infinite ease-in-out;
        }
        @keyframes latido { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }

        /* CONTENEDORES FLUIDOS */
        .app-container { opacity: 0; transition: opacity 1s ease; padding: 20px; height: 100%; overflow-y: auto; }
        .card-will {
            background: var(--gris); border: 1px solid var(--oro); border-radius: 25px;
            padding: 30px; margin: 20px auto; max-width: 400px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        }

        .btn-oro { 
            background: var(--oro); color: black; font-weight: bold; border: none;
            border-radius: 12px; padding: 14px; width: 100%; transition: 0.3s;
        }
        .btn-oro:active { transform: scale(0.95); }
        
        input.form-control { 
            background: #1a1a1a !important; color: white !important; border: 1px solid #333 !
