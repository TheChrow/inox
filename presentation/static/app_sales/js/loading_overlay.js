// Helpers globales para mostrar/ocultar el overlay de carga.
// Soportan llamadas concurrentes mediante un contador interno:
// el overlay permanece visible mientras haya al menos un show() sin su hide() pareja.

(function () {
    let counter = 0;

    function getOverlay() {
        return document.getElementById('loadingOverlay');
    }

    window.showLoadingOverlay = function () {
        counter += 1;
        const el = getOverlay();
        if (el) el.style.display = 'flex';
    };

    window.hideLoadingOverlay = function () {
        counter = Math.max(0, counter - 1);
        if (counter === 0) {
            const el = getOverlay();
            if (el) el.style.display = 'none';
        }
    };

    // Reset duro para casos de error inesperado (útil desde la consola).
    window.resetLoadingOverlay = function () {
        counter = 0;
        const el = getOverlay();
        if (el) el.style.display = 'none';
    };
})();
