// Descarga el PDF de la cotización forzando "Guardar como…" (no abre tab).
// Requiere que la cotización ya esté guardada en Odoo (su `name` está en
// #numero_cotizacion). Si no hay name, no hace nada y avisa.

$(document).ready(function () {
    const btn = document.getElementById('generarPDF');
    if (!btn) return;

    btn.addEventListener('click', function (e) {
        e.preventDefault();

        const name = ($('#numero_cotizacion').text() || '').trim();
        if (!name) {
            Swal.fire(
                'Guardá la cotización primero',
                'Para imprimir necesitamos el número Odoo. Hacé clic en Guardar y volvé a intentarlo.',
                'info'
            );
            return;
        }

        showLoadingOverlay();
        const url = `/sales/odoo/quotations/${encodeURIComponent(name)}/pdf/`;

        fetch(url, {
            method: 'GET',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
            credentials: 'same-origin',
        })
            .then(async function (resp) {
                if (!resp.ok) {
                    // El backend devuelve JSON {ok:false, error:...} en caso de error.
                    let msg;
                    try {
                        const body = await resp.json();
                        msg = (body && body.error) || resp.statusText;
                    } catch (_) {
                        msg = resp.statusText || 'Error desconocido';
                    }
                    throw new Error(msg);
                }
                return resp.blob();
            })
            .then(function (blob) {
                const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = blobUrl;
                a.download = `cotizacion_${name}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(blobUrl);
            })
            .catch(function (err) {
                Swal.fire('Error al generar PDF', err.message, 'error');
            })
            .finally(function () {
                hideLoadingOverlay();
            });
    });
});
