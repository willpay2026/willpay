const express = require('express');
const app = express();
const path = require('path');

// Configuración de datos y seguridad
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// LIGANDO LA CARPETA STATIC (Donde están tus diseños)
app.use(express.static(path.join(__dirname, 'static')));

// --- 1. RUTA DE BIENVENIDA (EL COHETE 🚀) ---
app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Will-Pay | El Legado</title>
            <style>
                body { background: #000; color: #fff; font-family: sans-serif; text-align: center; padding: 20px; }
                .card { background: #111; border: 1px solid #ffcf40; border-radius: 15px; padding: 20px; margin: 20px auto; max-width: 400px; }
                .btn-gold { background: #ffcf40; color: #000; border: none; padding: 18px; border-radius: 30px; font-weight: bold; width: 100%; cursor: pointer; font-size: 1rem; }
                img { max-width: 180px; margin-bottom: 20px; }
                .footer { color: #555; font-size: 0.8rem; margin-top: 30px; }
            </style>
        </head>
        <body>
            <img src="https://raw.githubusercontent.com/willpay2026/willpay/main/static/logonuevo.jpg" alt="Will-Pay Logo">
            <h1>🚀 Will-Pay Global 2026</h1>
            <p>El legado para <b>Wilyanny Donquiz</b> está en línea.</p>
            
            <div class="card">
                <h3>💰 DATOS DE RECARGA</h3>
                <p><b>Banco:</b> Banesco</p>
                <p><b>Pago Móvil:</b> 04126602555</p>
                <p><b>C.I / RIF:</b> 13496133</p>
                <p style="color: #ffcf40; font-size: 0.85rem;">Recarga y envía el capture. Wilfredo aprobará tu saldo.</p>
            </div>

            <div style="max-width: 400px; margin: auto;">
                <button class="btn-gold" onclick="location.href='/registro'">REGISTRAR MI ADN DIGITAL</button>
                <p><a href="/boveda" style="color: #888; text-decoration: none; display: block; margin-top: 15px;">¿Ya tienes cuenta? Entrar a mi Bóveda</a></p>
            </div>

            <div class="footer">Will-Pay Venezuela - CEO Wilfredo Donquiz</div>
        </body>
        </html>
    `);
});

// --- 2. RUTA DE REGISTRO LEGAL (ADN DIGITAL) ---
app.get('/registro', (req, res) => {
    // Esto busca el archivo físico en tu carpeta 'static'
    res.sendFile(path.join(__dirname, 'static', 'registro.html'));
});

// --- 3. RUTA DE LA BÓVEDA (APP EN SÍ / SALDO) ---
app.get('/boveda', (req, res) => {
    // Aquí es donde ven los Bs. 7.560,00 y el código QR
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// --- 4. MANEJO DE REGISTROS (PARA QUE NO DÉ ERROR AL DARLE AL BOTÓN) ---
app.post('/guardar-registro', (req, res) => {
    console.log("Nuevo ADN Digital recibido");
    res.send("<h1>✅ Registro Exitoso</h1><p>Wilfredo está verificando tus datos. Pronto verás tu saldo disponible.</p><a href='/boveda'>Ir a mi Bóveda</a>");
});

// ARRANCANDO EL MOTOR
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log('--- SISTEMA WILL-PAY ACTIVO EN PUERTO ' + PORT + ' ---');
});
