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

    // ─── Autocompletar en #inputCliente ───────────────────────────────────────
    const $inputCliente = $('#inputCliente');
    const $sugerencias = $('#resultadosClientes');

    let searchTimer = null;
    $inputCliente.on('input', function () {
        const q = ($(this).val() || '').trim();
        clearTimeout(searchTimer);
        if (q.length < 2) {
            $sugerencias.empty();
            return;
        }
        searchTimer = setTimeout(function () { buscarClientes(q); }, 250);
    });

    // Cierra sugerencias al hacer click fuera
    $(document).on('click', function (e) {
        if (!$(e.target).closest('#inputCliente, #resultadosClientes').length) {
            $sugerencias.empty();
        }
    });

    function buscarClientes(query) {
        $.ajax({
            url: '/sales/odoo/partners/search/',
            method: 'GET',
            data: { q: query, limit: 10 },
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
        })
            .done(function (resp) {
                renderSugerencias(resp.records || []);
            })
            .fail(function () {
                $sugerencias.empty();
            });
    }

    function renderSugerencias(records) {
        $sugerencias.empty();
        if (!records.length) return;
        const $list = $('<div class="list-group" style="position:absolute; z-index:1050; width:auto; max-width:480px; box-shadow:0 4px 12px rgba(0,0,0,.15);"></div>');
        records.forEach(function (r) {
            const subtitulo = [r.vat, r.email].filter(Boolean).join(' · ');
            const $item = $(
                '<button type="button" class="list-group-item list-group-item-action" style="font-size:12px;">' +
                '<strong></strong><br><span class="text-muted" style="font-size:11px;"></span>' +
                '</button>'
            );
            $item.find('strong').text(r.name || '(sin nombre)');
            $item.find('span').text(subtitulo);
            $item.on('click', function () {
                cargarCliente(r.id);
                $sugerencias.empty();
            });
            $list.append($item);
        });
        $sugerencias.append($list);
    }

    // ─── Cargar cliente y poblar el modal ─────────────────────────────────────
    function cargarCliente(customerId) {
        showLoadingOverlay();
        $.ajax({
            url: '/sales/odoo/partners/' + customerId + '/',
            method: 'GET',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
        })
            .done(function (resp) {
                rellenarModal(resp.customer, resp.contact, resp.address);
                $inputCliente
                    .val(buildDisplay(resp.customer))
                    .attr('data-codigosn', resp.customer.id)
                    .attr('data-rut', resp.customer.vat || '');
            })
            .fail(function (xhr) {
                const body = xhr.responseJSON;
                Swal.fire('Error', (body && body.error) || 'No se pudo cargar el cliente', 'error');
            })
            .always(function () { hideLoadingOverlay(); });
    }

    function buildDisplay(customer) {
        return (customer.name || '') + (customer.vat ? ' - ' + customer.vat : '');
    }

    function rellenarModal(customer, contact, address) {
        const empresa = !!customer.is_company;
        $('input[name="grupoSN"]').filter('[value="' + (empresa ? '100' : '105') + '"]').prop('checked', true);
        toggleByTipo();

        if (empresa) {
            $('#nombreSN').val(customer.name || '');
            $('#apellidoSN').val('');
        } else {
            // Para personas naturales partimos por el primer espacio: name=primer token, last_name=resto.
            const partes = (customer.name || '').trim().split(/\s+/);
            const primer = partes.shift() || '';
            $('#nombreSN').val(primer);
            $('#apellidoSN').val(partes.join(' '));
        }
        $('#rutSN').val(customer.vat || '');
        $('#telefonoSN').val(customer.phone || '+56');
        $('#emailSN').val(customer.email || '');
        $('#giroSN').val(customer.comment || '');

        // Contacto: solo si es empresa y existe
        if (empresa && contact) {
            $('#contactoNombre').val(contact.name || '');
            $('#contactoCargo').val(contact.function || '');
            $('#contactoEmail').val(contact.email || '');
            $('#contactoTelefono').val(contact.phone || '');
        } else {
            $('#contactoNombre, #contactoCargo, #contactoEmail, #contactoTelefono').val('');
        }

        // Dirección: usamos street completo en dirCalle, dirNumero queda vacío
        // para no parsear incorrectamente. El usuario puede editar si necesita.
        if (address) {
            $('#dirNombre').val(address.name || '');
            $('#dirCalle').val(address.street || '');
            $('#dirNumero').val('');
            $('#dirComuna').val(address.city || '');
            $('#dirZip').val(address.zip || '');
            $('#dirTelefono').val(address.phone || '');
            // state_id viene como [id, nombre] desde Odoo
            const region = Array.isArray(address.state_id) ? address.state_id[1] : '';
            $('#dirRegion').val(region || '');
        } else {
            $('#dirNombre, #dirCalle, #dirNumero, #dirComuna, #dirZip, #dirTelefono, #dirRegion').val('');
        }

        // Abrir el modal automáticamente
        const modalEl = document.getElementById('clienteModal');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    // ─── Grabar (crea/actualiza en Odoo + DB inox) ─────────────────────────────
    $('#grabar-btn').on('click', function () {
        const payload = buildPayload();
        if (!validate(payload)) return;

        const $btn = $(this);
        const originalText = $btn.text();
        $btn.prop('disabled', true).text('Grabando...');
        showLoadingOverlay();

        $.ajax({
            url: '/sales/odoo/partners/',
            method: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') },
            data: JSON.stringify(payload),
            success: function (data) {
                const verbo = data.existing ? 'actualizado' : 'creado';
                const aviso = data.db_persisted === false
                    ? `Cliente ${verbo} en Odoo (id ${data.customer_id}), pero no se pudo guardar en la base local: ${data.db_error || 'error desconocido'}.`
                    : `Cliente ${verbo} (id ${data.customer_id})`;
                const icon = data.db_persisted === false ? 'warning' : 'success';
                Swal.fire(data.db_persisted === false ? 'Atención' : 'Éxito', aviso, icon);

                bootstrap.Modal.getInstance(document.getElementById('clienteModal')).hide();

                $inputCliente
                    .val(`${payload.customer.name}${payload.customer.vat ? ' - ' + payload.customer.vat : ''}`)
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
                hideLoadingOverlay();
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
        const dir = buildAddress('dir', 'other');
        if (dir) addresses.push(dir);

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
