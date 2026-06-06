// Carga de una cotización existente en quotation.html.
//
// Si Django entrega `odoo_name` al template (ruta /sales/generate-quote/<name>/),
// dispara GET /sales/odoo/quotations/<name>/ y rellena:
//   - Cliente (#inputCliente + data-codigosn + data-rut)
//   - Referencia (#referencia) y Observaciones (#Observaciones-1)
//   - #numero_cotizacion → nombre Odoo (ej. S00004)
//   - Por cada línea: agregarProducto(name, lineNum, sku, ...)
//
// También:
//   - Habilita el botón "Acciones" (.btn-primary.dropdown-toggle del toolbar)
//     sólo cuando #numero_cotizacion tiene contenido.

$(document).ready(function () {

    // El template inyecta window.INOX_ODOO_NAME cuando carga una cotización existente.
    const odooName = (window.INOX_ODOO_NAME || '').trim();

    function toggleAccionesDropdown() {
        const numero = ($('#numero_cotizacion').text() || '').trim();
        const btn = document.getElementById('btn-acciones-toolbar');
        if (!btn) return;
        btn.hidden = !numero;
    }

    // Aseguramos el estado inicial (sin número → escondido)
    toggleAccionesDropdown();

    if (!odooName) return;

    showLoadingOverlay();

    $.ajax({
        url: `/sales/odoo/quotations/${encodeURIComponent(odooName)}/`,
        method: 'GET',
        headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
    })
        .done(function (resp) {
            try {
                const order = resp.order || {};
                const lines = resp.lines || [];

                pintarCabecera(order);
                cargarCliente(order);
                pintarLineas(order, lines);
                toggleAccionesDropdown();
            } catch (e) {
                console.error('Error rellenando la cotización Odoo:', e);
                Swal.fire('Error', 'No se pudo renderizar la cotización: ' + e.message, 'error');
            }
        })
        .fail(function (xhr) {
            const body = xhr.responseJSON;
            const msg = (body && body.error) || xhr.statusText || 'Error desconocido';
            Swal.fire('Error al cargar cotización', msg, 'error');
        })
        .always(function () { hideLoadingOverlay(); });

    function pintarCabecera(order) {
        const name = order.name || '';
        const $numero = $('#numero_cotizacion');
        $numero.text(name).attr('data-docEntry', order.id || '');

        if (order.client_order_ref) $('#referencia').val(order.client_order_ref);
        if (order.note) $('#Observaciones-1').val(order.note);
        if (order.validity_date) {
            $('#docDueDate').text(order.validity_date).attr('data-docDueDate', order.validity_date);
        }
    }

    function cargarCliente(order) {
        const pair = order.partner_id;
        const partnerId = Array.isArray(pair) ? pair[0] : null;
        const partnerName = Array.isArray(pair) ? (pair[1] || '') : '';

        // Mostramos algo aunque la llamada full no responda
        $('#inputCliente')
            .val(partnerName)
            .attr('data-codigosn', partnerId || '');

        if (!partnerId) return;

        // Reusa el endpoint que ya levanta cliente + dirección + contacto.
        $.ajax({
            url: '/sales/odoo/partners/' + partnerId + '/',
            method: 'GET',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
        }).done(function (resp) {
            const customer = resp.customer || {};
            const display = (customer.name || partnerName)
                + (customer.vat ? ' - ' + customer.vat : '');
            $('#inputCliente')
                .val(display)
                .attr('data-codigosn', customer.id || partnerId)
                .attr('data-rut', customer.vat || '');
        });
    }

    function pintarLineas(order, lines) {
        const odooDocName = order.name || odooName; // valor a usar como data-docentryLinea

        lines.forEach((ln, idx) => {
            const sku = ln.product_default_code || '';
            const nombre = ln.product_name || '';
            const imagen = ln.product_image
                ? `data:image/png;base64,${ln.product_image}`
                : '';
            const precioVenta = Number(ln.price_unit) || 0;
            const precioLista = Number(ln.product_list_price) || precioVenta;
            const descuentoAplicado = Number(ln.discount) || 0;
            const cantidad = Number(ln.product_uom_qty) || 1;
            const comentario = ln.name || '';

            // Firma de agregarProducto:
            //   (docEntry_linea, linea_documento, productoCodigo, nombre, imagen,
            //    precioVenta, stockTotal, precioLista, precioDescuento, cantidad,
            //    sucursal, comentario, cuponDescuento, descuentoAplcado)
            agregarProducto(
                odooDocName,         // docEntry_linea  ← S00004
                idx + 1,             // linea_documento
                sku,                 // productoCodigo
                nombre,              // nombre
                imagen,              // imagen
                precioVenta,         // precioVenta
                0,                   // stockTotal (lo recalcula obtenerStock)
                precioLista,         // precioLista
                100,                 // precioDescuento (tope visual %)
                cantidad,            // cantidad
                'LO',                // sucursal por defecto
                comentario,          // comentario
                0,                   // cuponDescuento
                descuentoAplicado    // descuentoAplcado
            );
        });
    }
});
