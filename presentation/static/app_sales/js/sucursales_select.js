document.addEventListener("DOMContentLoaded", function () {
    // Elementos HTML
    const numeroCotizacion = document.getElementById("numero_cotizacion");
    const sucursal = document.getElementById("sucursal").textContent.trim();
    const selectBodega = document.getElementById("bodega");

    // Validar si existe el atributo "data-docentry"
    if (!numeroCotizacion.hasAttribute("data-docentry")) {
        // Recorrer las opciones del select y seleccionar la que coincida con el valor del <strong>
        Array.from(selectBodega.options).forEach(option => {
            if (option.value === sucursal) {
                option.selected = true;
            }
        });
    }
});
