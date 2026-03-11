from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'willpay_2026_legacy'

# --- PUENTES A TUS PIEZAS (TEMPLATES) ---

@app.route('/')
def splash():
    return render_template('splash.html') # La entrada (1.PNG)

@app.route('/acceso')
def acceso():
    return render_template('acceso.html') # Login (2.PNG)

@app.route('/registro')
def registro():
    return render_template('registro.html') # Registro de ADN

@app.route('/dashboard')
def dashboard():
    # Aquí es donde el usuario verá su saldo (1.jpeg)
    return render_template('dashboard.html')

@app.route('/boveda')
def boveda():
    return render_template('boveda.html') # Sección de recarga (2.jpeg)

@app.route('/panel_ceo')
def panel_ceo():
    return render_template('panel_ceo.html') # Tu tablero de control

# --- ENLAZADOR DE ACCIONES (PAGOS Y TICKETS) ---

@app.route('/recibo')
def recibo():
    return render_template('recibo.html') # El ticket final (4.png)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
