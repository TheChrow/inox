function debounce(func, delay) {
    let timeout;
    return function () {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), delay);
    };
}

$(document).ready(function () {
    $('#inputNumero').on('input', debounce(function () {
        let numero = $(this).val();
        let tipoDoucmento = $('.tipoDocumento').first().text().trim();
        let cardCode = document.getElementById('inputCliente').getAttribute('data-codigosn');
        if (numero.length >= 3) {
            $.ajax({
                url: '/sales/search-products/',
                data: { 'numero': numero, 'cardCode': cardCode },
                dataType: 'json',
                success: function (data) {
                    $('#resultados').empty();
                    if (data.resultados && data.resultados.length > 0) {
                        data.resultados.forEach(function (resultado) {
                            resultado.precio = parseFloat(resultado.precio);
                            resultado.precioAnterior = resultado.precioAnterior;
                            resultado.maxDescuento = parseFloat(resultado.maxDescuento);
                            resultado.stockTotal = parseInt(resultado.stockTotal);
                            const sucursal = $('#sucursal').text().trim();

                            var productoElemento = document.createElement('p');
                            productoElemento.className = 'agregar_productos';
                            productoElemento.setAttribute('data-codigo', resultado.codigo);
                            productoElemento.setAttribute('data-nombre', resultado.nombre);
                            productoElemento.setAttribute('data-imagen', resultado.imagen);
                            productoElemento.setAttribute('data-precio', resultado.precio);
                            productoElemento.setAttribute('data-stockTotal', resultado.stockTotal);
                            productoElemento.setAttribute('data-precioAnterior', resultado.precioAnterior);
                            productoElemento.setAttribute('data-maxDescuento', resultado.maxDescuento);
                            productoElemento.textContent = `${resultado.codigo} | ${resultado.nombre} | Stock Total: ${resultado.stockTotal}`;

                            productoElemento.addEventListener('click', function () {
                                let codigo = this.getAttribute('data-codigo');
                                let nombre = this.getAttribute('data-nombre');
                                let imagen = this.getAttribute('data-imagen');
                                let precioVenta = parseFloat(this.getAttribute('data-precio'));
                                let stockTotal = parseInt(this.getAttribute('data-stockTotal'));
                                let precioLista = parseFloat(this.getAttribute('data-precioAnterior'));
                                let precioDescuento = parseFloat(this.getAttribute('data-maxDescuento'));
                                let cantidad = stockTotal > 0 ? 1 : 0;

                                if (tipoDoucmento == 'Cotización' || tipoDoucmento == 'Solicitud Devolución' || tipoDoucmento == 'Orden de Venta') {
                                    cantidad = 1;
                                }

                                const sucursal = $('#sucursal').text().trim();
                                agregarProducto('null', null, codigo, nombre, imagen, precioVenta, stockTotal, precioLista, precioDescuento, cantidad, sucursal);

                                $('#inputNumero').val('');
                            });

                            $('#resultados').append(productoElemento);
                            $('#resultados').on('click', '*', function () {
                                $('#resultados').empty();
                            });
                        });
                    } else {
                        $('#resultados').text('No se encontraron resultados');
                    }
                }
            });
        } else {
            $('#resultados').empty();
        }
    }, 300)); // debounce de 300ms
});
