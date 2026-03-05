const express = require('express');
const app = express();
const path = require('path');
const ejs = require('ejs');

app.set('views', path.join(__dirname, 'templates'));
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));

// --- RUTA DEL CEO (TU PANEL) ---
app.get('/ceo', (req, res) => {
    const u = { 
        id_dna: "CEO-0001-FOUNDER",
        nombre: "WILFREDO DONQUIZ", 
        saldo_bs: 0.00,
        ultimo_id_pendiente: "000000",
        ultimo_monto_pendiente: 0.00
    };
    res.render('ceo_panel.html', { u: u, m: [] });
});

// --- RUTA DEL SOCIO (LA BÓVEDA) ---
app.get('/boveda', (req, res) => {
    const usuario = {
        nombre: "Socio Will-Pay",
        id_adn: "WP-ADN-321",
        saldo_disponible: 7560.00, // Basado en tus capturas
        qr_data: "WILL-PAY-VENEZUELA-ADN-321"
    };
    const movimientos = [
        { fecha: "2026-02-20 01:52:25", tipo: "Recarga Aprobada", monto: 7560.00 }
    ];
    res.render('boveda.html', { u: usuario, m: movimientos });
});

// --- LÓGICA DE INYECCIÓN ---
app.post('/admin_recarga', (req, res) => {
    console.log(`Inyectando capital a: ${req.body.telefono}`);
    res.redirect('/ceo');
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log('--- BÚNKER WILL-PAY: SISTEMA COMPLETO ACTIVADO ---');
});
