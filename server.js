const express = require('express');
const app = express();
const path = require('path');
const ejs = require('ejs');

// Configuración de Motores para el Diseño Clásico
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

// --- 3. PANEL MAESTRO CEO (ESTILO CLÁSICO) ---
app.get('/ceo', (req, res) => {
    // Definimos los datos reales para el diseño de tres cuadros
    const u = { 
        id_dna: "CEO-0001-FOUNDER",
        nombre: "WILFREDO DONQUIZ", 
        saldo_bs: 10500.50,   // Datos de ejemplo para que no salga en cero
        saldo_wpc: 25000.00,
        saldo_usd: 150.75,
        ganancia_neta: 3450.20,
        ultimo_id_pendiente: "000025",
        ultimo_monto_pendiente: 7500.00
    };

    // Movimientos de ejemplo para la tabla de abajo
    const movimientos = [
        { correlativo: "000024", telefono: "04121234567", monto_bs: 500.00 },
        { correlativo: "000023", telefono: "04247654321", monto_bs: 1200.00 }
    ];

    // Renderizamos el diseño clásico con los datos traducidos
    res.render('ceo_panel.html', { u: u, m: movimientos });
});

app.get('/boveda', (req, res) => {
    res.redirect('/ceo');
});

// --- 4. LÓGICA DE PROCESOS ---
app.post('/acceso', (req, res) => {
    console.log("Acceso autorizado al Búnker Clásico");
    res.redirect('/ceo'); 
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log('--- SISTEMA WILL-PAY: PANEL CLÁSICO RESTAURADO ---');
});
