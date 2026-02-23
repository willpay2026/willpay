from flask import Flask, render_template_string, request, redirect, session, jsonify
import psycopg2
from psycopg2.extras import DictCursor
import os

app = Flask(__name__)
app.secret_key = 'willpay_2026_safe'

# Configuración directa de Base de Datos
DB_URL = "postgresql://willpay_db_user:746J7SWXHVCv07Ttl6AE5dIk68Ex6jWN@dpg-d6ea0e5m5p6s73dhh1a0-a/willpay_db"

def query_db(query, args=(), one=False, commit=False):
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(query, args)
    rv = None
    if commit:
        conn.commit()
    else:
        rv = cur.fetchone() if one else cur.fetchall()
    cur.close()
    conn.close()
    return rv

# --- HTML UNIFICADO ---
LAYOUT = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Will-Pay</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@zxing/library@latest"></script>
    <style>
        body { background:#000; color:#fff; font-family:sans-serif; }
        .card-wp { background:#111; border:2px solid #d4af37; border-radius:15px; padding:20px; max-width:400px; margin:20px auto; }
        .oro { color:#d4af37; font-weight:bold; }
        .btn-oro { background:#d4af37; color:#000; font-weight:bold; width:100%; border:none; padding:10px; border-radius:10px; }
        .saldo { font-size:2.5rem; color:#d4af37; font-weight:bold; margin:10px 0; }
        input { background:#222 !important; color:#fff !important; border:1px solid #444 !important; margin-bottom:10px; }
    </style>
</head>
<body>
    <div class="container text-center">
        <h2 class="oro mt-3">WILL-PAY PRO</h2>
        {% if session.get('u') %}
            <div class="card-wp">
                <p class="small text-muted">Hola, {{ u.nombre }}</p>
                <div class="saldo">Bs. {{ "%.2f"|format(u.saldo_bs) }}</div>
                
                <div class="btn-group w-100 mb-3">
                    <a href="/rol/pasajero" class="btn btn-sm {{ 'btn-warning' if u.rol == 'pasajero' else 'btn-dark' }}">PAGAR</a>
                    <a href="/rol/prestador" class="btn btn-sm {{ 'btn-warning' if u.rol == 'prestador' else 'btn-dark' }}">COBRAR</a>
                </div>

                {% if u.rol == 'pasajero' %}
                    <div class="bg-white p-2 d-inline-block rounded mb-2">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=WP|{{u.id}}|10">
                    </div>
                {% else %}
                    <button class="btn-oro py-3" onclick="scan()">📷 COBRAR QR</button>
                    <video id="v" style="width:100%; display:none; margin-top:10px; border-radius:10px;"></video>
                {% endif %}

                {% if u.id == 'admin' %}
                <div class="mt-4 p-3 border border-warning rounded">
                    <h6 class="oro">RECARGAS ADMIN</h6>
                    <form action="/recargar" method="POST">
                        <input name="t" placeholder="Teléfono" class="form-control form-control-sm" required>
                        <input name="m" type="number" step="0.01" placeholder="Monto" class="form-control form-control-sm" required>
                        <button class="btn btn-danger btn-sm w-100">RECARGAR</button>
                    </form>
                </div>
                {% endif %}

                <div class="mt-4 text-start">
                    <p class="small oro mb-1">MOVIMIENTOS:</p>
                    {% for m in h %}
                        <div style="font-size:0.7rem; border-bottom:1px solid #333; padding:3px 0;">
                            {{ m.fecha.strftime('%H:%M') }} | {{ m.receptor }} | +{{ m.monto }} Bs.
                        </div>
                    {% endfor %}
                </div>
                <a href="/logout" class="text-danger small d-block mt-4">Salir</a>
            </div>
        {% else %}
            <div class="card-wp mt-5">
                <form action="/login" method="POST">
                    <input name="t" placeholder="Teléfono" class="form-control" required>
                    <input name="p" type="password" placeholder="PIN" class="form-control" required>
                    <button class="btn-oro">ENTRAR</button>
                </form>
            </div>
        {% endif %}
    </div>
    <script>
        function scan() {
            const v = document.getElementById('v'); v.style.display='block';
            const reader = new ZXing.BrowserQRCodeReader();
            reader.decodeFromVideoDevice(null, 'v', (res) => {
                if (res) {
                    const d = res.text.split('|');
                    if(confirm("¿Cobrar " + d[2] + " Bs?")) window.location.href = "/do_pago/"+d[1]+"/"+d[2];
                }
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'u' not in session: return render_template_string(LAYOUT)
    u = query_db("SELECT * FROM usuarios WHERE id=%s", (session['u'],), one=True)
    h = query_db("SELECT * FROM historial WHERE emisor=%s OR receptor=%s ORDER BY fecha DESC LIMIT 4", (session['u'], session['u']))
    return render_template_string(LAYOUT, u=u, h=h)

@app.route('/login', methods=['POST'])
def login():
    res = query_db("SELECT id FROM usuarios WHERE id=%s AND pin=%s", (request.form['t'], request.form['p']), one=True)
    if res: session['u'] = res['id']
    return redirect('/')

@app.route('/recargar', methods=['POST'])
def recargar():
    if session.get('u') == 'admin':
        query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (request.form['m'], request.form['t']), commit=True)
        query_db("INSERT INTO historial (emisor, receptor, monto, concepto) VALUES ('ADMIN', %s, %s, 'Recarga')", (request.form['t'], request.form['m']), commit=True)
    return redirect('/')

@app.route('/do_pago/<emi>/<mon>')
def do_pago(emi, mon):
    m = float(mon); com = m * 0.015; neto = m - com
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs - %s WHERE id=%s", (m, emi), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id=%s", (neto, session['u']), commit=True)
    query_db("UPDATE usuarios SET saldo_bs = saldo_bs + %s WHERE id='SISTEMA_GANANCIAS'", (com,), commit=True)
    query_db("INSERT INTO historial (emisor, receptor, monto, concepto) VALUES (%s, %s, %s, 'Pago')", (emi, session['u'], neto), commit=True)
    return redirect('/')

@app.route('/rol/<r>')
def rol(r):
    query_db("UPDATE usuarios SET rol=%s WHERE id=%s", (r, session['u']), commit=True)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
