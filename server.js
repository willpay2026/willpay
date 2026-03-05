const express = require('express');
const app = express();
const path = require('path');
const ejs = require('ejs'); // Motor para las plantillas doradas

// Configuración de Motores
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// --- 1. RUTA PRINCIPAL ---
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// --- 2. RUTAS DE NAVEGACIÓN (CONECTADAS AL ADN) ---
app.get('/acceso', (req, res) => res.sendFile(path.join(__dirname, 'static', 'acceso.html')));
app.get('/registro', (req, res) => res.sendFile(path.join(__dirname, 'static', 'registro.html')));

// ESTAS RUTAS AHORA BUSCAN EN TEMPLATES (EL TABLERO DEFINITIVO)
app.get('/ceo', (req, res) => {
    // Esto activa el diseño de la barra roja y los datos del CEO
    const datosSimulados = { 
        nombre: "WILFREDO DONQUIZ", 
        capital_total: 0.00, 
        ganancia_neta: 0.00,
        total_depositado: 0.00
    };
    res.render('ceo_panel.html', { u: datosSimulados, m: [] });
});

app.get('/boveda', (req, res) => {
    // Redirigimos a la oficina principal del CEO
    res.redirect('/ceo');
});

// --- 3. LÓGICA DE PROCESOS ---
app.post('/acceso', (req, res) => {
    console.log("Entrando al Búnker Dorado...");
    res.redirect('/ceo'); 
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log('--- SISTEMA WILL-PAY: TABLERO DEFINITIVO ACTIVADO EN PUERTO ' + PORT + ' ---');
});
