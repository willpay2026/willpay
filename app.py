from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import csv, os, datetime

# 1. CONFIGURACIÓN INICIAL (Esto evita el error NameError)
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
            # Admin por defecto
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

# 2. INTERFAZ VISUAL (ADAPTADA A TUS CAPTURAS)
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
            background: #111; border: 2px solid #d4af37; border-radius: 30px; 
            padding: 25px; margin: 20px auto; max-width: 400px; box-shadow: 0 0 20px rgba(212,175,55,0.2);
        }
        .btn-gold { background: #d4af37; color: #000; font-weight: bold; border-radius: 12px; padding: 12px; border: none; width: 100%; text-decoration: none; display: block; }
        .btn-outline-gold { background: transparent; color: #d4af37; border: 1px solid #d4af37; border-radius: 12px; padding: 10px; width: 100%; text-decoration: none; display: block; }
        .monto-box { background: transparent; border: 1px solid #fff; border-radius: 15px; color: #d4af37; font-size: 2.5rem; width: 100
