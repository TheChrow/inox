$(document).ready(function () {

    function isEmpresa() {
        return $('input[name="grupoSN"]:checked').val() === '100';
    }

    // Toggle de visibilidad por tipo de cliente.
    // Usamos d-none (no jQuery.toggle()) para no romper el display:flex de Bootstrap .row
    function toggleByTipo() {
        const empresa = isEmpresa();
        $('#seccionContacto, #seccionContactoFila1, #seccionContactoFila2').toggleClass('d-none', !empresa);
        $('#filaApellido').toggleClass('d-none', empresa);
        $('#nombreLabel').text(empresa ? 'Razón Social' : 'Nombre');
    }
    $('input[name="grupoSN"]').on('change', toggleByTipo);
    toggleByTipo();

    $('#grabar-btn').on('click', function () {
        const payload = buildPayload();
        if (!validate(payload)) return;

        const $btn = $(this);
        const originalText = $btn.text();
        $btn.prop('disabled', true).text('Grabando...');

        $.ajax({
            url: '/sales/odoo/partners/',
            method: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
            data: JSON.stringify(payload),
            success: function (data) {
                const verbo = data.existing ? 'actualizado' : 'creado';
                Swal.fire('Éxito', `Cliente ${verbo} (id ${data.customer_id})`, 'success');

                bootstrap.Modal.getInstance(document.getElementById('clienteModal')).hide();

                const display = `${payload.customer.name}${payload.customer.vat ? ' - ' + payload.customer.vat : ''}`;
                $('#inputCliente')
                    .val(display)
                    .attr('data-codigosn', data.customer_id)
                    .attr('data-rut', payload.customer.vat || '');
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
                Swal.fire('Error', msg, 'error');
            },
            complete: function () {
                $btn.prop('disabled', false).text(originalText);
            },
        });
    });

    function buildPayload() {
        const empresa = isEmpresa();
        const nombre = ($('#nombreSN').val() || '').trim();
        const apellido = ($('#apellidoSN').val() || '').trim();
        const fullName = empresa
            ? nombre
            : [nombre, apellido].filter(Boolean).join(' ');

        const customer = { name: fullName, is_company: empresa, country_id: 46 };
        addIfPresent(customer, 'vat', $('#rutSN').val());
        addIfPresent(customer, 'phone', $('#telefonoSN').val());
        addIfPresent(customer, 'email', $('#emailSN').val());
        addIfPresent(customer, 'comment', $('#giroSN').val());

        const contacts = [];
        if (empresa) {
            const cnNombre = ($('#contactoNombre').val() || '').trim();
            if (cnNombre) {
                const c = { name: cnNombre };
                addIfPresent(c, 'function', $('#contactoCargo').val());
                addIfPresent(c, 'email', $('#contactoEmail').val());
                addIfPresent(c, 'phone', $('#contactoTelefono').val());
                contacts.push(c);
            }
        }

        const addresses = [];
        const desp = buildAddress('desp', 'delivery');
        if (desp) addresses.push(desp);
        const fact = buildAddress('fact', 'invoice');
        if (fact) addresses.push(fact);

        return { customer, contacts, addresses };
    }

    function buildAddress(prefix, type) {
        const calle = ($(`#${prefix}Calle`).val() || '').trim();
        const numero = ($(`#${prefix}Numero`).val() || '').trim();
        const street = [calle, numero].filter(Boolean).join(' ');
        if (!street) return null;

        const a = { type, street, country_id: 46 };
        addIfPresent(a, 'name', $(`#${prefix}Nombre`).val());
        addIfPresent(a, 'city', $(`#${prefix}Comuna`).val());
        addIfPresent(a, 'zip', $(`#${prefix}Zip`).val());
        addIfPresent(a, 'phone', $(`#${prefix}Telefono`).val());
        addIfPresent(a, 'region', $(`#${prefix}Region`).val());
        return a;
    }

    function addIfPresent(obj, key, raw) {
        const v = (raw || '').trim();
        if (v) obj[key] = v;
    }

    function validate(payload) {
        const empresa = isEmpresa();
        const errores = [];

        if (!($('#nombreSN').val() || '').trim()) {
            errores.push(empresa ? 'Razón Social es obligatoria.' : 'Nombre es obligatorio.');
        }
        if (!empresa && !($('#apellidoSN').val() || '').trim()) {
            errores.push('Apellido es obligatorio para personas naturales.');
        }
        if (!payload.customer.vat) {
            errores.push('RUT es obligatorio.');
        }
        if (!payload.customer.email) {
            errores.push('Email es obligatorio.');
        }
        if (!payload.customer.phone) {
            errores.push('Teléfono es obligatorio.');
        }

        if (errores.length > 0) {
            Swal.fire('Faltan datos', errores.join('<br>'), 'warning');
            return false;
        }
        return true;
    }
});
