/* Lista de cotizaciones — versión Odoo
 * Reescribe la paginación rota del proyecto original usando el total real
 * devuelto por el endpoint /sales/odoo/quotations/list/ (search_count).
 */
document.addEventListener("DOMContentLoaded", function () {

    const ENDPOINT = "/sales/odoo/quotations/list/";
    const PAGE_SIZE = 20;

    let currentPage = 1;
    let totalPages = 1;
    let totalRecords = 0;
    let inFlight = null;

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

    const $ = (sel) => document.querySelector(sel);
    const tbody = $("#listadoCotizaciones");
    const emptyState = $("#lc-empty");
    const summary = $("#lc-summary");
    const overlay = $("#loadingOverlay");
    const paginationEl = document.querySelector(".lc-pagination");
    const filterForm = $("#filterForm");
    const searchInput = $("#buscarlistacootizacion");
    const vendedorSelect = $("#filtro_vendedor");
    const estadoSelect = $("#filtro_estado");
    const inputBruto = $("#buscar_bruto");
    const inputNeto = $("#buscar_neto");

    /* ── Overlay ───────────────────────────────────────────────────── */
    const showLoading = () => { overlay.hidden = false; };
    const hideLoading = () => { overlay.hidden = true; };

    /* ── Formateadores ─────────────────────────────────────────────── */
    const formatCurrency = (value) => {
        const number = Number(value) || 0;
        const integerValue = Math.floor(number);
        const formatted = integerValue.toLocaleString("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
        return `$ ${formatted}`;
    };

    const formatDate = (raw) => {
        if (!raw) return "—";
        const isoDate = raw.includes(" ") ? raw.split(" ")[0] : raw;
        const parts = isoDate.split("-");
        if (parts.length !== 3) return raw;
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    };

    const resolveSalesperson = (record) => {
        const raw = record.x_studio_vendedor;
        if (Array.isArray(raw)) return raw[1] || "—";
        if (typeof raw === "string" && raw.trim()) return raw.trim();
        if (Array.isArray(record.user_id)) return record.user_id[1] || "—";
        return "—";
    };

    const stateInfo = (state) => {
        switch (state) {
            case "draft":
            case "sent":
                return { label: "Abierto", className: "lc-badge--open" };
            case "sale":
            case "done":
                return { label: "Cerrado", className: "lc-badge--closed" };
            case "cancel":
                return { label: "Cancelado", className: "lc-badge--cancel" };
            default:
                return { label: state || "—", className: "lc-badge--default" };
        }
    };

    /* ── Recolección de filtros ────────────────────────────────────── */
    const getFilters = () => {
        const dateFrom = filterForm.querySelector('[name="fecha_inicio"]').value;
        const dateTo = filterForm.querySelector('[name="fecha_fin"]').value;
        const dateDoc = filterForm.querySelector('[name="fecha_documento"]').value;
        const docNum = filterForm.querySelector('[name="docNum"]').value.trim();
        const partnerText = filterForm.querySelector('[name="cardName"]').value.trim();
        const salespersonName = vendedorSelect.value.trim();
        const state = estadoSelect.value.trim();
        const amountTotalRaw = inputBruto.value.trim();
        const amountTotal = amountTotalRaw === "" ? null : Number(amountTotalRaw);

        return {
            date_from: dateFrom || null,
            date_to: dateTo || null,
            date_doc: dateDoc || null,
            doc_num: docNum || null,
            partner_text: partnerText || null,
            salesperson_name: salespersonName || null,
            state: state || null,
            amount_total: Number.isFinite(amountTotal) ? amountTotal : null,
        };
    };

    /* ── Fetch + render ────────────────────────────────────────────── */
    const fetchData = (page = 1) => {
        if (inFlight) {
            inFlight.abort();
        }
        currentPage = page;
        showLoading();

        const filters = getFilters();
        const payload = {
            ...filters,
            page,
            page_size: PAGE_SIZE,
        };

        const controller = new AbortController();
        inFlight = controller;

        fetch(ENDPOINT, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify(payload),
            signal: controller.signal,
        })
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((err) => {
                        throw new Error(err.error || "Error en la respuesta del servidor");
                    });
                }
                return response.json();
            })
            .then((data) => {
                renderRecords(data.records || []);
                totalRecords = data.total || 0;
                totalPages = data.total_pages || 1;
                updateSummary(data);
                updatePagination();
            })
            .catch((error) => {
                if (error.name === "AbortError") return;
                console.error("Error al listar cotizaciones:", error);
                renderRecords([]);
                summary.textContent = "Error al cargar cotizaciones";
            })
            .finally(() => {
                if (inFlight === controller) {
                    inFlight = null;
                }
                hideLoading();
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
    };

    const renderRecords = (records) => {
        tbody.innerHTML = "";

        if (!records.length) {
            emptyState.hidden = false;
            return;
        }
        emptyState.hidden = true;

        const fragment = document.createDocumentFragment();
        records.forEach((record) => {
            const tr = document.createElement("tr");

            const partner = Array.isArray(record.partner_id) ? record.partner_id : [null, "—"];
            const partnerId = partner[0];
            const partnerName = partner[1] || "Cliente desconocido";

            const salespersonName = resolveSalesperson(record);

            const status = stateInfo(record.state);
            const folio = record.name || `#${record.id}`;
            const fecha = formatDate(record.date_order);
            const neto = formatCurrency(record.amount_untaxed);
            const bruto = formatCurrency(record.amount_total);

            tr.innerHTML = `
                <td class="lc-cell-folio">
                    <a href="#" class="lc-link docentry-link" data-docentry="${record.id}">${folio}</a>
                </td>
                <td class="lc-cell-customer">
                    <a href="#" class="lc-link cliente-link" data-partner-id="${partnerId ?? ""}">
                        <span class="lc-customer-name">${escapeHtml(partnerName)}</span>
                    </a>
                </td>
                <td>${escapeHtml(salespersonName)}</td>
                <td>${fecha}</td>
                <td><span class="lc-badge ${status.className}">${status.label}</span></td>
                <td class="lc-cell-right">${neto}</td>
                <td class="lc-cell-right">${bruto}</td>
            `;
            fragment.appendChild(tr);
        });
        tbody.appendChild(fragment);

        tbody.querySelectorAll(".docentry-link").forEach((link) => {
            link.addEventListener("click", (event) => {
                event.preventDefault();
                const docEntry = event.currentTarget.getAttribute("data-docentry");
                if (!docEntry) return;
                showLoading();
                window.location.href = `/sales/generate-quote/?docentry=${docEntry}`;
            });
        });

        tbody.querySelectorAll(".cliente-link").forEach((link) => {
            link.addEventListener("click", (event) => {
                event.preventDefault();
                const partnerId = event.currentTarget.getAttribute("data-partner-id");
                if (!partnerId) return;
                showLoading();
                window.location.href = `/sales/create-customers/?partner_id=${partnerId}`;
            });
        });
    };

    const escapeHtml = (text) => {
        if (text === null || text === undefined) return "";
        return String(text)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    };

    /* ── Resumen + Paginación correcta ─────────────────────────────── */
    const updateSummary = (data) => {
        const total = data.total ?? 0;
        if (!total) {
            summary.textContent = "Sin resultados";
            return;
        }
        const from = (data.page - 1) * data.page_size + 1;
        const to = Math.min(from + data.records.length - 1, total);
        summary.textContent = `Mostrando ${from}–${to} de ${total} cotizaciones`;
    };

    const updatePagination = () => {
        paginationEl.innerHTML = "";

        const addItem = ({ label, page, disabled = false, active = false, ellipsis = false, ariaLabel }) => {
            const li = document.createElement("li");
            li.classList.add("page-item");
            if (disabled) li.classList.add("disabled");
            if (active) li.classList.add("active");
            if (ellipsis) li.classList.add("lc-ellipsis");

            const a = document.createElement("a");
            a.classList.add("page-link");
            a.href = "#";
            a.innerHTML = label;
            if (ariaLabel) a.setAttribute("aria-label", ariaLabel);

            if (!disabled && !active && !ellipsis && page) {
                a.addEventListener("click", (event) => {
                    event.preventDefault();
                    fetchData(page);
                });
            }

            li.appendChild(a);
            paginationEl.appendChild(li);
        };

        addItem({
            label: '<span aria-hidden="true">«</span>',
            page: currentPage - 1,
            disabled: currentPage <= 1,
            ariaLabel: "Anterior",
        });

        const pages = buildPageList(currentPage, totalPages);
        pages.forEach((p) => {
            if (p === "…") {
                addItem({ label: "…", ellipsis: true });
            } else {
                addItem({
                    label: String(p),
                    page: p,
                    active: p === currentPage,
                });
            }
        });

        addItem({
            label: '<span aria-hidden="true">»</span>',
            page: currentPage + 1,
            disabled: currentPage >= totalPages,
            ariaLabel: "Siguiente",
        });
    };

    /* Genera una lista compacta de páginas: 1 … 4 5 [6] 7 8 … 20 */
    const buildPageList = (page, total) => {
        if (total <= 1) return [1];
        const result = [];
        const window = 1;
        const first = 1;
        const last = total;

        const start = Math.max(first + 1, page - window);
        const end = Math.min(last - 1, page + window);

        result.push(first);
        if (start > first + 1) result.push("…");
        for (let i = start; i <= end; i++) result.push(i);
        if (end < last - 1) result.push("…");
        if (last !== first) result.push(last);

        return result;
    };

    /* ── Búsqueda en barra superior ────────────────────────────────── */
    const applySearchBar = () => {
        const text = (searchInput.value || "").trim();
        if (!text) {
            fetchData(1);
            return;
        }

        if (/^\d+$/.test(text)) {
            filterForm.querySelector('[name="docNum"]').value = text;
        } else if (/^\d{1,4}[-\/]\d{1,2}[-\/]\d{1,4}$/.test(text)) {
            const parts = text.split(/[-\/]/);
            let iso = text;
            if (parts[0].length === 4) {
                iso = `${parts[0]}-${parts[1].padStart(2, "0")}-${parts[2].padStart(2, "0")}`;
            } else {
                iso = `${parts[2]}-${parts[1].padStart(2, "0")}-${parts[0].padStart(2, "0")}`;
            }
            filterForm.querySelector('[name="fecha_documento"]').value = iso;
        } else {
            const lowered = text.toLowerCase();
            const estadoMap = { "abierto": "O", "cerrado": "C", "cancelado": "Y" };
            if (estadoMap[lowered]) {
                estadoSelect.value = estadoMap[lowered];
            } else {
                filterForm.querySelector('[name="cardName"]').value = text;
            }
        }

        searchInput.value = "";
        fetchData(1);
    };

    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            applySearchBar();
        }
    });
    $("#lupa-busqueda").addEventListener("click", applySearchBar);

    /* ── Filtros: Enter, change y limpieza ─────────────────────────── */
    filterForm.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && event.target.tagName !== "TEXTAREA") {
            event.preventDefault();
            fetchData(1);
        }
    });

    filterForm.querySelectorAll("select").forEach((select) => {
        select.addEventListener("change", () => fetchData(1));
    });

    filterForm.querySelectorAll("input").forEach((input) => {
        if (input === searchInput) return;
        input.addEventListener("input", () => {
            if (input.value === "") fetchData(1);
        });
        if (input.type === "date") {
            input.addEventListener("change", () => fetchData(1));
        }
    });

    /* ── Neto calculado en vivo a partir del bruto ─────────────────── */
    inputBruto.addEventListener("input", () => {
        const bruto = parseFloat(inputBruto.value) || 0;
        const neto = bruto * 0.84;
        inputNeto.value = neto ? Math.round(neto) : "";
    });

    /* ── Filtros iniciales desde URL ───────────────────────────────── */
    const urlParams = new URLSearchParams(window.location.search);
    const rutSN = urlParams.get("rutSN");
    const nombreSN = urlParams.get("nombreSN");
    if (rutSN) filterForm.querySelector('[name="cardName"]').value = rutSN;
    if (nombreSN) filterForm.querySelector('[name="cardName"]').value = nombreSN;

    /* ── Primera carga ─────────────────────────────────────────────── */
    fetchData(1);
});
