from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'willpay_emporio_final_2026_legado_wilyanny'

# Para que el servidor encuentre tu logo
@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def splash():
    # Esta es la pantalla de 4 segundos
    return render_template('splash.html')

@app.route('/acceso')
def acceso():
    # Aquí es donde el usuario decide si entrar o registrarse
    return render_template('acceso.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
