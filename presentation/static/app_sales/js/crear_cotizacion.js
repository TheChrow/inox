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
        // #numero_cotizacion vacío → crear; con texto (ej. S00003) → actualizar.
        const existingName = ($('#numero_cotizacion').text() || '').trim();
        const isUpdate = existingName.length > 0;

        let payload;
        try {
            payload = buildPayload();
        } catch (e) {
            Swal.fire('Faltan datos', e.message, 'warning');
            return;
        }

        showLoadingOverlay();

        const ajaxConfig = isUpdate
            ? { url: `/sales/odoo/quotations/${encodeURIComponent(existingName)}/`, method: 'PUT' }
            : { url: '/sales/odoo/quotations/', method: 'POST' };

        $.ajax({
            url: ajaxConfig.url,
            method: ajaxConfig.method,
            contentType: 'application/json',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
            data: JSON.stringify(payload),
            success: function (data) {
                const title = isUpdate ? 'Cotización actualizada' : 'Cotización creada';
                Swal.fire(
                    title,
                    `Odoo: <b>${data.name || ''}</b> (id ${data.order_id})`,
                    'success'
                ).then(() => {
                    if (data && data.name) {
                        window.location.href = `/sales/generate-quote/${encodeURIComponent(data.name)}/`;
                    }
                });
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
                const title = isUpdate ? 'Error al actualizar cotización' : 'Error al crear cotización';
                Swal.fire(title, msg, 'error');
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

        // x_studio_vendedor: código del vendedor logueado
        const codeVen = ($('#vendedor_data').attr('data-codeven') || '').trim();
        if (codeVen) payload.salesperson_code = codeVen;

        return payload;
    }
});
