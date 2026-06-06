class Producto {
    constructor(docEntry_linea, linea_documento, productoCodigo, nombre, imagen, precioVenta, stockTotal, precioLista, precioDescuento, cantidad, sucursal, comentario, cuponDescuento, descuentoAplcado) {
        
        this.docEntry_linea = docEntry_linea;
        this.linea_documento = linea_documento;
        this.productoCodigo = productoCodigo;
        this.nombre = nombre;
        this.imagen = imagen;
        this.precioVenta = precioVenta;
        this.stockTotal = stockTotal;
        this.precioLista = precioLista;
        this.precioDescuento = Math.round(precioDescuento);
        this.precioSinDescuento = 0;
        this.totalProducto = precioVenta * cantidad;
        this.cantidad = cantidad;
        this.sucursal = sucursal;
        this.comentario = comentario;
        this.descuentoAplcado = descuentoAplcado ?? 0;
        this.cuponDescuento = cuponDescuento

    }
    

    async obtenerStock(codigoProducto) {
        try {
            const response = await fetch(`/ventas/obtener_stock_bodegas/?idProducto=${codigoProducto}`);
            if (!response.ok) {
                throw new Error("Error al obtener el stock");
            }
            const data = await response.json();
            //console.log("info bodegas:", data)
            return data; // Lista de objetos con bodega y stock
        } catch (error) {
            console.error("Error al obtener el stock:", error);
            return null;
        }
    }

    async actualizarStock(row) {
        const stockData = await this.obtenerStock(this.productoCodigo);

        console.log("Stock data obtenido para el producto", this.productoCodigo, ":", stockData);

        if (stockData) {
            // Mapear las bodegas válidas (excluyendo GR)
            const bodegaMap = {
                "LC": "LC",
                "PH": "PH",
                "ME": "ME",
                "VI": "VI",
                "GR": "GR"
            };

            // Filtrar los datos de stock excluyendo la bodega "GR"
            const stockFiltrado = stockData.filter(bodega => bodega.bodega !== "LLLLL");
            const stockTotalBodegasValidas = stockData.filter(bodega => bodega.bodega !== "LLLLL" && bodegaMap[bodega.bodega]);


            // Calcular el stock total sumando solo las bodegas válidas
            const stockTotal = stockTotalBodegasValidas.reduce((total, bodega) => total + bodega.stock_disponible, 0);

            // Mostrar el stock total
            const stockTotalElem = row.querySelector('[name="stock_total"]');
            const treeTypeItem = stockData.find(item => item.product_type === 'iSalesTree');

            
            if (treeTypeItem) {
                stockTotalElem.textContent = `Total: ${treeTypeItem.stock_total}`;
                stockTotalElem.style.color = treeTypeItem.stock_total === 0 ? 'red' : 'black';
            } else {
                stockTotalElem.textContent = `Total: ${stockTotal}`;
                stockTotalElem.style.color = stockTotal === 0 ? 'red' : 'black';
            }

            let warningIcon = row.querySelector('#warning_container');
            console.log("capturado el warning icon:", warningIcon);

            if (stockTotal === 0) {
                console.log("No hay stock disponible para el producto:", this.productoCodigo);
                warningIcon.hidden = false;
            } else {
                console.log("Hay stock disponible para el producto:", this.productoCodigo);
                warningIcon.hidden = true;
            }

            // Obtener el value de la bodega seleccionada
            const selectBodega = row.querySelector('.form-select');
            const valueSeleccionado = selectBodega.value;

            // Usar el mapa para obtener el código correspondiente
            const bodegaSeleccionada = bodegaMap[valueSeleccionado];

            // Encontrar el stock de la bodega seleccionada
            const stockBodega = stockFiltrado.find(bodega => bodega.bodega === bodegaSeleccionada)?.stock_disponible || 0;

            // Mostrar el stock de la bodega seleccionada
            const stockBodegaElem = row.querySelector('[name="stock_bodega"]');
            stockBodegaElem.textContent = `Stock: ${stockBodega}`;


            // mostrar el stock en transito

            const tr_bodega = `TR_${bodegaSeleccionada}`;


            const stockTRElem = row.querySelector('[name="stock_tr"]');
            const stockTR = stockFiltrado.find(bodega => bodega.bodega === tr_bodega)?.stock_transito || 0;
            stockTRElem.textContent = `TR: ${stockTR}`;

            // Mostrar el stock en arribo
            const stockArriboElem = row.querySelector('[name="stock_arribo"]');
            const stockArribo = stockFiltrado.find(bodega => bodega.bodega === 'RECEP_CD')?.stock_arribo || 0;
            stockArriboElem.textContent = `Arribo: ${stockArribo}`;

            // Mostrar el stock comprometido
            const stockComprometidoElem = row.querySelector('[name="stock_comprometido"]');
            const stockComprometido = stockFiltrado.find(bodega => bodega.bodega === bodegaSeleccionada)?.stock_comprometido || 0;
            stockComprometidoElem.textContent = `Comp: ${stockComprometido}`;
        }
    }

    // Método para crear una fila en la tabla de productos
    crearFila(contprod) {
        let newRow = document.createElement('tbody');
        newRow.className = 'product-row';
        newRow.setAttribute('id', contprod);
        newRow.setAttribute('data-docentryLinea', this.docEntry_linea);
        newRow.setAttribute('data-itemcode', this.productoCodigo);


        // draggable se maneja solo desde el handle, no en toda la fila

        // Verificar si el valor de docEntry_linea es "null"
        if (this.docEntry_linea === "null") {
            newRow.style.backgroundColor = '#F0F2F5'; // Color gris claro cuando es "null"
        }

        newRow.innerHTML = `
        <tr>
            <tr>
                <td style="font-size: 12px; background: transparent; border-style: none; padding-bottom: 0px;" rowspan="2">
                    <div class="row">
                        <div class="col-md-11 col-xxl-6" style="font-size: 14px; font-weight: bold;">
                        <small id="indixe_producto" data-lineNum="${this?.linea_documento}" data-indice="${contprod}">${contprod})</small><small>&nbsp;&nbsp;</small><small style="font-weight-bold" name="sku_producto"></small>
                        </div>
                        <div class="col-md-11 col-xxl-7" style="text-align: center;">
                            <img src="" style="width: 80px;height: 80px; border-radius: 50%; object-fit: cover;" name="img_producto" id="img_productox">
                        </div>
                    </div>
                </td>
                <td style="font-size: 12px; background: transparent; border-style: none; padding-bottom: 0px;" rowspan="2">
                    <div class="row">
                        <div class="col-sm-12 col-lg-12 col-xl-11 col-xxl-10">
                          <select class="form-select bodega-select" style="font-size: 11px;">
                            <optgroup label="Bodega">
                            <option value="LO" selected>Los Olivos (LO)</option>
                            </optgroup>
                          </select>
                        </div>
                        <div class="col" style="text-align: left;">
                            <small style="font-size: 12px;" name="stock_bodega">Stock:  </small>
                            <small style="font-size: 12px;" id="stock_total" name="stock_total">Total: </small>
                            <div id="warning_container" style="display: inline-block;" hidden>
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 16 16" style="color: rgba(255, 7, 7, 1);margin-left: 2px;" name="warning_icon">
                                    <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.15.15 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.2.2 0 0 1-.054.06.1.1 0 0 1-.066.017H1.146a.1.1 0 0 1-.066-.017.2.2 0 0 1-.054-.06.18.18 0 0 1 .002-.183L7.884 2.073a.15.15 0 0 1 .054-.057m1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767z"/>
                                    <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0M7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0z"/>
                                </svg>
                            </div>
                        </div>
                    </div>
                    <div class="col" style="text-align: left;">
                        <small style="font-size: 12px;" name="stock_tr">TR:  </small>
                        <small style="font-size: 12px;" name="stock_arribo">Arribo:  </small>
                        <small style="font-size: 12px;" id="stock_comprometido" name="stock_comprometido">Comp: </small>
                    </div>
                </td>
                <td style="background: transparent;border-style: none;padding-bottom: 0px;" rowspan="2">
                    <div style="font-size: 12px;">
                        <small class="numeric-value" name="precio_venta" data-precio-unitario="100.00" data-precioUnitario="${this.precioVenta}">${formatCurrency(this.precioVenta)}</small>
                    </div>
                    <div style="font-size: 11px;">
                        <small class="numeric-value" style="color: rgb(153,153,153);" name="precio_lista">${formatCurrency(this.precioLista)}</small>
                    </div>

                    <div class="row" style="font-size: 11px;">
                        <div class="col-sm-4 col-md-3 col-xl-2" style="padding-right: 0px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="currentColor" viewBox="0 0 16 16" id="mostrar-descuento" class="bi bi-arrow-right-circle-fill" style="font-size: 18px;">
                                <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0M4.5 7.5a.5.5 0 0 0 0 1h5.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5z"></path>
                            </svg>
                        </div>
                        <div class="col-sm-7 col-md-8">
                            <small  class="numeric-value" style="color: rgb(255,0,0);" id="descuento" name="descuento_max" hidden>Max: ${this.precioDescuento}%</small>
                        </div>
                    </div>
                </td>
                <td style="font-size: 12px;background: transparent;border-style: none;">
                    <div>
                        <input class="form-control format-number" type="number" style="font-size: 12px;width: 60px;" id="agg_descuento" min="0" value="${this.descuentoAplcado ?? 0}" onclick="this.select()">
                        <strong style="font-size: 9;width: 100px; color: red" id="desc_cupon" ${this.cuponDescuento ? '' : 'hidden'}>Cupon: ${this.cuponDescuento ?? 0}%</strong>
                    </div>
                </td>
                <td style="font-size: 11px;background: transparent;font-weight: bold;border-style: none;text-align: center;" id="Precio_Descuento">${formatCurrency(this.precioSinDescuento)}</td>
                <td style="font-size: 12px;background: transparent;border-style: none;">
                    <input class="form-control format-number" type="number" style="font-size: 12px;width: 80px;"  id="calcular_cantidad" name="cantidad" min="1" max="1000" value="${this.cantidad}" onclick="this.select()">
                </td>
                <td style="font-size: 11px;background: transparent;font-weight: bold;border-style: none;text-align: center;">
                    <span id="precio_Venta" data-totalProductValue="${this.totalProducto}">${formatCurrency(this.totalProducto)}</span>
                </td>
            </tr> 
            <tr style="font-size: 12px;background: transparent;">
                <td style="font-size: 11px;background: transparent;padding-top: 0px;border-style: none;padding-bottom: 0px;"colspan="3">
                    <input class="form-control" type="text" placeholder="Comentario" id="comentarios-1" style="font-size: 12px;" value=""></input>
                </td>
                <td style="background: transparent;padding-top: 8px;padding-left: 50px;border-style: none;padding-bottom: 0px;">
                    <div class="d-flex align-items-center gap-2">
                        <!-- Botón eliminar -->
                        <a class="navbar-brand d-flex align-items-center" href="#" style="width: 18px;">
                          <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="currentColor" viewBox="0 0 16 16" id="eliminarp" class="bi bi-trash" style="width: 18px;height: 18px;">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"> </path>
                            <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"> </path>
                          </svg>
                        </a>

                    </div>
                </td>
            <tr style="font-size: 12px;background: transparent;">
                
                <td colspan="7" style="padding-top: 0px; background: transparent;">
                <div class="d-flex align-items-center gap-1">

                    <button 
                        class="btn btn-link btn-sm p-0 d-flex align-items-center justify-content-center text-danger"
                        style="width: 22px; height: 22px;"
                        type="button"
                        id="btn-ficha-tecnica" title="Descargar ficha técnica PDF"
                    >
                        <i class="bi bi-file-earmark-pdf-fill" style="font-size: 16px;"></i>
                    </button>

                    <span name="nombre_producto" style="font-size: 12px; flex-grow: 1;">
                        
                    </span>

                    <span id="drag-handle" 
                        title="Arrastrar para reordenar" 
                        style="cursor: grab; color: #888; user-select: none; padding: 4px 12px; display: flex; align-items: center; justify-content: center;">
                        
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M7 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 5a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                        </svg>
                    </span>

                </div>
                </td>
            </tr>
            </tr>
        `;

        // Safe DOM assignments - prevent XSS from DB-sourced product fields
        newRow.querySelector('[name="sku_producto"]').textContent = this.productoCodigo;
        newRow.querySelector('[name="img_producto"]').setAttribute('src', this.imagen);
        newRow.querySelector('[name="nombre_producto"]').textContent = this.nombre;
        newRow.querySelector('#comentarios-1').value = this.comentario ?? '';
        newRow.querySelector('#btn-ficha-tecnica').addEventListener('click', () => {
            generarFichaTecnica(this.productoCodigo);
        });

        function formatCurrency(value) {
            // Convertimos el valor a número entero
            const integerValue = value;
            let formattedValue = integerValue.toLocaleString('es-ES', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        
            // Si el valor tiene 4 dígitos y no incluye un punto, lo añadimos manualmente
            if (integerValue >= 1000 && integerValue < 10000 && !formattedValue.includes(".")) {
                formattedValue = `${formattedValue.slice(0, 1)}.${formattedValue.slice(1)}`;
            }
        
            // Agregamos el símbolo de peso al principio
            return `$ ${formattedValue}`;
        }

        // Agregar evento mouseover para mostrar stock en otras tiendas
        const precioVentaElem = newRow.querySelector('#stock_total');
        precioVentaElem.addEventListener('mouseover', async () => {
            const stockData = await this.obtenerStock(this.productoCodigo);
            if (stockData) {
                // Filtrar las bodegas para incluir solo las del mapa válido

                const bodegaMap = {
                    "LC": "LC",
                    "PH": "PH",
                    "ME": "ME",
                    "VI": "VI",
                    "GR": "GR"
                };

                const stockFiltrado = stockData.filter(bodega => bodega.bodega in bodegaMap);

                // Crear el contenido del tooltip solo con las bodegas válidas
                const tooltipContent = stockFiltrado
                    .map(bodega => `${bodega.bodega}: ${bodega.stock_disponible}`)
                    .join('\n');

                // Asignar el contenido del tooltip
                precioVentaElem.title = `Stock en otras tiendas:\n${tooltipContent}`;
            }
        });

        this.limitarMaxDescuento(newRow);
        inicializarDragAndDrop(newRow);


        return newRow;
    }

    // Método para alternar la visibilidad del descuento
    alternarMaxDescuento(row) {
        let elemento = row.querySelector('#descuento');
        if (elemento.getAttribute('hidden') !== null) {
            elemento.removeAttribute('hidden');
        } else {
            elemento.setAttribute('hidden', '');
        }
    }

    limitarMaxDescuento(row) {
        // Obtener el valor del descuento máximo
        let descuentoMaxElem = row.querySelector('#descuento');
        let descuentoMax = parseFloat(descuentoMaxElem.textContent.replace('Max: ', ''));
    
        // Configurar el input para limitar el valor máximo
        let inputDescuento = row.querySelector('#agg_descuento');
        inputDescuento.max = descuentoMax;
    
        // Establecer el valor inicial del descuento aplicado en el input
        inputDescuento.value = this.descuentoAplcado;  // Cambié de 0 a this.descuentoAplcado
    
        // Validar el valor actual del input
        inputDescuento.addEventListener('input', function () {
            let valor = parseFloat(inputDescuento.value);
    
            // Si el valor es mayor que el descuento máximo, ajustarlo
            if (valor > descuentoMax) {
                inputDescuento.value = descuentoMax;
            }
    
            // Si el valor es menor que 0, ajustarlo a 0
            if (valor < 0) {
                inputDescuento.value = 0;
            }
        });
    }
    
}

// Función global para manejar la adición de productos
function agregarProducto(docEntry_linea,linea_documento, productoCodigo, nombre, imagen, precioVenta, stockTotal, precioLista, precioDescuento, cantidad = 1, sucursal, comentario, cuponDescuento, descuentoAplcado) {
    // Contador de productos
    console.log("cantidad: ", cantidad);
    console.log("sucursal: ", sucursal);

    let contprod = document.querySelectorAll('#productos tbody').length + 1;

    // Crear una instancia de Producto
    let producto = new Producto(docEntry_linea, linea_documento, productoCodigo, nombre, imagen, precioVenta, stockTotal, precioLista, precioDescuento, cantidad, sucursal, comentario, cuponDescuento, descuentoAplcado);
    
    let newRow = producto.crearFila(contprod);

    document.getElementById('productos').appendChild(newRow);


    console.log("Producto creado xxx:", producto);
    console.log("Producto creado:", producto.cuponDescuento, producto.precioDescuento);


    // ---- APLICAR UI DEL CUPÓN ANTES de inicializar interactividad ----
    if (producto.cuponDescuento && Number(producto.cuponDescuento) > 0) {
        const descuentoCupon = Number(producto.cuponDescuento);

        const inputDescuentoRow = newRow.querySelector('#agg_descuento');
        if (inputDescuentoRow) {
            inputDescuentoRow.max = descuentoCupon;
            inputDescuentoRow.value = 0;
            inputDescuentoRow.setAttribute('disabled', 'disabled');
        }

        const descElem = newRow.querySelector('#desc_cupon');
        if (descElem) {
            descElem.textContent = `Cupon: ${descuentoCupon}%`;
            descElem.hidden = false;
            descElem.dataset.value = descuentoCupon; // <- importante para calcular correctamente
        }
    }


    const indiceProducto = newRow.querySelector('#indixe_producto').getAttribute('data-indice'); 

    const input_descuento = newRow.querySelector('#agg_descuento');
    const value_defecto = "0";
    input_descuento.addEventListener('input', () => {
        if (input_descuento.value === '') {
            input_descuento.value = value_defecto;
        }
    });

    const input_cantidad = newRow.querySelector('#calcular_cantidad');
    const value_defecto_cant = "1";
    input_cantidad.addEventListener('input', () => {
        if (input_cantidad.value === '') {
            input_cantidad.value = value_defecto_cant;
        }
    });

    // Agregar eventos
    newRow.querySelector('#mostrar-descuento').addEventListener('click', function () {
        producto.alternarMaxDescuento(newRow);
    });

    newRow.querySelector('#eliminarp').addEventListener('click', function () {
        // Obtener el índice del producto dentro de la tabla
        const indiceProducto = newRow.querySelector('#indixe_producto').getAttribute('data-indice'); 
    
        // Eliminar la fila del DOM
        newRow.remove();
    
        // Emitir el evento con código del producto e índice
        const event = new CustomEvent('productoEliminado', {
            detail: { 
                codigoProducto: productoCodigo,
                indiceProducto: indiceProducto // Pasar el índice específico
            }
        });
    
        console.log('Evento emitido:', event);
        document.dispatchEvent(event);
    
        // Actualizar los índices de los productos visibles
        actualizarIndicesProductos();

        document.getElementById('inputNumero').focus();
    });
    
    function actualizarIndicesProductos() {
        // Seleccionar todas las filas de los productos
        const filasProductos = document.querySelectorAll('.product-row'); // Asegúrate de que las filas tengan esta clase
        filasProductos.forEach((fila, index) => {
            // Buscar el elemento que muestra el índice y actualizarlo
            const indiceElemento = fila.querySelector('#indixe_producto'); // Ajusta el selector si es necesario
            if (indiceElemento) {
                indiceElemento.textContent = `${index + 1})`; // Actualiza el índice visible
            }
        });
    }    

    producto.actualizarStock(newRow);

    // Evento para actualizar el stock al cambiar de bodega
    newRow.querySelector('.form-select').addEventListener('change', function () {
        producto.actualizarStock(newRow);
    });

    // Llamar a la función agregarInteractividad si es necesario
    agregarInteractividad(newRow, productoCodigo, indiceProducto);
}

    function recalcularIndices() {
        const filas = document.querySelectorAll('tbody.product-row');

        filas.forEach((fila, index) => {
            const nuevoIndice = index + 1;

            // Actualizar id y atributo del tbody
            fila.setAttribute('id', nuevoIndice);

            // Actualizar el texto visible del índice
            const indiceTd = fila.querySelector('#indixe_producto');
            if (indiceTd) {
                indiceTd.textContent = `${nuevoIndice})`;
                indiceTd.setAttribute('data-indice', nuevoIndice);
            }
        });
    }

    let draggedRow = null;

    function inicializarDragAndDrop(fila) {
        const handle = fila.querySelector('#drag-handle');

        if (handle) {
            // Solo activar draggable cuando el usuario presiona el handle
            handle.addEventListener('mousedown', () => {
                fila.setAttribute('draggable', 'true');
            });

            // Desactivar draggable al soltar para evitar arrastre accidental en toda la fila
            handle.addEventListener('mouseup', () => {
                fila.setAttribute('draggable', 'false');
            });
        }

        fila.addEventListener('dragstart', (e) => {
            // Bloquear si el drag no viene del handle
            if (!fila.getAttribute('draggable') || fila.getAttribute('draggable') === 'false') {
                e.preventDefault();
                return;
            }
            draggedRow = fila;
            // Pequeño delay para que el browser tome el snapshot ANTES de opacar
            setTimeout(() => fila.classList.add('dragging'), 0);
            e.dataTransfer.effectAllowed = 'move';
        });

        fila.addEventListener('dragend', () => {
            fila.setAttribute('draggable', 'false');
            fila.classList.remove('dragging');
            draggedRow = null;
            // Limpiar todos los indicadores visuales
            limpiarIndicadores();
        });

        fila.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';

            if (fila === draggedRow) return;

            limpiarIndicadores();

            const rect = fila.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;

            if (e.clientY < midY) {
                fila.classList.add('drag-over-top');    // va ANTES de esta fila
            } else {
                fila.classList.add('drag-over-bottom'); // va DESPUÉS de esta fila
            }
        });

        fila.addEventListener('dragleave', (e) => {
            // Solo limpiar si realmente salimos de la fila (no de un hijo)
            if (!fila.contains(e.relatedTarget)) {
                fila.classList.remove('drag-over-top', 'drag-over-bottom');
            }
        });

        fila.addEventListener('drop', (e) => {
            e.preventDefault();

            if (!draggedRow || fila === draggedRow) return;

            const container = fila.parentNode;
            const rect = fila.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;

            if (e.clientY < midY) {
                container.insertBefore(draggedRow, fila);          // insertar ANTES
            } else {
                container.insertBefore(draggedRow, fila.nextSibling); // insertar DESPUÉS
            }

            limpiarIndicadores();
            recalcularIndices();
        });
    }

    function limpiarIndicadores() {
        document.querySelectorAll('.product-row').forEach(f => {
            f.classList.remove('drag-over-top', 'drag-over-bottom');
        });
    }

    function recalcularIndices() {
        document.querySelectorAll('tbody.product-row').forEach((fila, index) => {
            const nuevoIndice = index + 1;
            fila.setAttribute('id', nuevoIndice);

            const indiceTd = fila.querySelector('[id="indixe_producto"]');
            if (indiceTd) {
                indiceTd.textContent = `${nuevoIndice})`;
                indiceTd.setAttribute('data-indice', nuevoIndice);
            }
        });
    }