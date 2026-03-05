const express = require('express');
const app = express();
const path = require('path');
const ejs = require('ejs');

// 1. CONFIGURACIÓN DE MOTORES (Buscando en /templates)
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');

// 2. MIDDLEWARES
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// --- 3. RUTA DEL CEO (TU PANEL MAESTRO) ---
app.get('/ceo', (req, res) => {
    const u = { 
        id_dna: "CEO-0001-FOUNDER",
        nombre: "WILFREDO DONQUIZ", 
        saldo_bs: 0.00,
        total_depositado: 0.00,      // Corregido: Variable para image_225568.png
        ganancia_neta: 0.00,        // Corregido: Variable para image_225568.png
        ultimo_id_pendiente: "000000",
        ultimo_monto_pendiente: 0.00
    };
    // Enviamos 'u' y una lista de movimientos 'm' vacía para la tabla
    res.render('ceo_panel.html', { u: u, m: [] });
});

// --- 4. RUTA DEL SOCIO (LA BÓVEDA EN TEMPLATES) ---
app.get('/boveda', (req, res) => {
    const usuario = {
        nombre: "Socio Will-Pay",
        id_adn: "WP-ADN-321",
        saldo_disponible: 7560.00, // Basado en tu captura ultimos movimientos.jpeg
        qr_data: "WILL-PAY-VENEZUELA-ADN-321"
    };
    
    const movimientos = [
        { 
            fecha: "2026-02-20 01:52:25", 
            tipo: "Recarga Aprobada", 
            monto: 7560.00 
        }
    ];

    // IMPORTANTE: boveda.html debe estar dentro de la carpeta /templates
    res.render('boveda.html', { u: usuario, m: movimientos });
});

// --- 5. LÓGICA DE INYECCIÓN DE CAPITAL ---
app.post('/admin_recarga', (req, res) => {
    const { telefono, monto } = req.body;
    console.log(`--- SISTEMA: Inyectando ${monto} Bs. al socio ${telefono} ---`);
    // Por ahora, refresca el panel. En el futuro, sumará a la base de datos.
    res.redirect('/ceo');
});

// --- 6. ARRANQUE DEL BÚNKER ---
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log('--- BÚNKER WILL-PAY: SISTEMA COMPLETO Y CORREGIDO ---');
});
