// Wirea los botones Guardar de la cotización al endpoint POST /sales/odoo/quotations/.
// Reemplaza al viejo quotations_insert.js (formato SAP) por el flujo Odoo nuevo.

$(document).ready(function () {

    function bindSave(id) {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', submitQuotation);
    }
    bindSave('saveButton');
    bindSave('saveButton2');

    function submitQuotation() {
        let payload;
        try {
            payload = buildPayload();
        } catch (e) {
            Swal.fire('Faltan datos', e.message, 'warning');
            return;
        }

        showLoadingOverlay();

        $.ajax({
            url: '/sales/odoo/quotations/',
            method: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
            data: JSON.stringify(payload),
            success: function (data) {
                Swal.fire(
                    'Cotización creada',
                    `Odoo: <b>${data.name || ''}</b> (id ${data.order_id})`,
                    'success'
                );
            },
            error: function (xhr) {
                const body = xhr.responseJSON;
                let msg;
                if (body && body.error) {
                    msg = body.error;
                } else if (body) {
                    msg = JSON.stringify(body);
                } else {
                    msg = xhr.statusText || 'Error desconocido';
                }
                Swal.fire('Error al crear cotización', msg, 'error');
            },
            complete: function () {
                hideLoadingOverlay();
            },
        });
    }

    function buildPayload() {
        const partnerIdRaw = $('#inputCliente').attr('data-codigosn');
        const partnerId = parseInt(partnerIdRaw, 10);
        if (!partnerId) {
            throw new Error('Seleccioná o creá un cliente antes de guardar la cotización.');
        }

        const lines = [];
        document.querySelectorAll('tbody.product-row').forEach(row => {
            const sku = (row.getAttribute('data-itemcode') || '').trim();
            if (!sku) return;

            const qty = parseFloat(row.querySelector('#calcular_cantidad').value) || 0;
            if (qty <= 0) return;

            const priceUnit = parseFloat(
                row.querySelector('[name="precio_venta"]').getAttribute('data-precioUnitario')
            ) || 0;
            const discount = parseFloat(row.querySelector('#agg_descuento').value) || 0;

            const comentario = (row.querySelector('#comentarios-1').value || '').trim();
            const nombre = (row.querySelector('[name="nombre_producto"]').textContent || '').trim();

            const line = {
                default_code: sku,
                quantity: qty,
                price_unit: priceUnit,
            };
            if (discount > 0) line.discount = discount;
            if (comentario || nombre) line.description = comentario || nombre;

            lines.push(line);
        });

        if (lines.length === 0) {
            throw new Error('Agregá al menos un producto antes de guardar la cotización.');
        }

        const payload = { partner_id: partnerId, lines };

        const validityRaw = $('#docDueDate').attr('data-docDueDate');
        if (validityRaw) payload.validity_date = validityRaw;

        const ref = ($('#referencia').val() || '').trim();
        if (ref) payload.client_order_ref = ref;

        const note = ($('#Observaciones-1').val() || '').trim();
        if (note) payload.note = note;

        return payload;
    }
});
