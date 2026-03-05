const express = require('express');
const app = express();
const path = require('path');
const ejs = require('ejs');

// Configuración de Motores para el Tablero Dorado
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

// --- 2. RUTAS DE NAVEGACIÓN ---
app.get('/acceso', (req, res) => res.sendFile(path.join(__dirname, 'static', 'acceso.html')));
app.get('/registro', (req, res) => res.sendFile(path.join(__dirname, 'static', 'registro.html')));

// --- 3. PANEL MAESTRO CEO (EL BÚNKER) ---
app.get('/ceo', (req, res) => {
    // Definimos los datos reales para que no salgan códigos raros en pantalla
    const u = { 
        nombre: "WILFREDO DONQUIZ", 
        capital_total: 0.00, 
        ganancia_neta: 0.00,
        total_depositado: 0.00,
        porc: "0.0%",  // Para las casillas de comisión
        auto_recargas: false,
        auto_retiros: false
    };

    // 'm' es la lista de actividad; la enviamos vacía por ahora
    res.render('ceo_panel.html', { u: u, m: [] });
});

app.get('/boveda', (req, res) => {
    res.redirect('/ceo');
});

// --- 4. LÓGICA DE PROCESOS ---
app.post('/acceso', (req, res) => {
    console.log("Acceso autorizado al Búnker Dorado");
    res.redirect('/ceo'); 
});

// Ruta para la recarga directa desde el panel
app.post('/admin_recarga', (req, res) => {
    const { telefono, monto } = req.body;
    console.log(`Recargando Bs. ${monto} al teléfono ${telefono}`);
    res.redirect('/ceo');
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log('--- SISTEMA WILL-PAY: TABLERO DEFINITIVO ACTIVADO ---');
});
