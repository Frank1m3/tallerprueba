/**
 * Agrega un buscador a un <select> con muchas opciones (productos, proveedores,
 * solicitantes, etc). El <select> original no se toca: sigue funcionando igual
 * que antes (val(), change(), disabled, mostrar/ocultar <option> para filtros).
 * Uso: $('#cbo_producto').buscadorSelect({ placeholder: 'Buscar producto...' });
 *
 * Modo remoto (para catálogos grandes, ej. item con 80mil+ filas): en vez de
 * filtrar las <option> ya cargadas en el HTML, busca en el servidor mientras
 * el usuario escribe. El <select> arranca vacío (solo la opción "— Seleccione —")
 * y al elegir un resultado se le inyecta dinámicamente la <option> con sus
 * data-* correspondientes, así el resto del código de la página (que lee
 * option:selected .data(...)) sigue funcionando igual.
 * Uso:
 *   $('#cbo_producto').buscadorSelect({
 *     placeholder: 'Buscar producto...',
 *     remote: {
 *       url: '/api/v1/item/buscar',
 *       minLength: 2,          // no busca con menos caracteres (default 1)
 *       delay: 300,            // debounce en ms (default 250)
 *       params: function(){ return { id_sucursal: $('#cbo_sucursal').val() }; },
 *       mapItem: function(item){
 *         return { value: item.id_item, text: item.item_code + ' - ' + item.descripcion,
 *                  data: { codigo: item.item_code, precio: item.precio_unitario, stock: item.stock } };
 *       }
 *     }
 *   });
 */
(function ($) {
    function textoSeleccionado($select) {
        const op = $select.find('option:selected');
        return (op.length && op.val()) ? op.text().trim() : '';
    }

    function opcionesVisibles($select) {
        return $select.find('option').filter(function () {
            return this.value !== '' && $(this).css('display') !== 'none';
        });
    }

    $.fn.buscadorSelect = function (opciones) {
        opciones = $.extend({ placeholder: 'Buscar...' }, opciones);
        const remoto = opciones.remote || null;

        return this.each(function () {
            const $select = $(this);
            if ($select.data('bsel-activo')) return;
            $select.data('bsel-activo', true);

            const $wrap = $('<div class="bsel-wrap"></div>');
            const $input = $('<input type="text" class="form-control bsel-input" autocomplete="off">')
                .attr('placeholder', opciones.placeholder);
            const $icono = $('<i class="fas fa-search bsel-icon"></i>');
            // Botón para cancelar/limpiar la selección actual sin tener que elegir
            // otro producto (antes no había forma de "deshacer" una elección).
            const $limpiar = $('<button type="button" class="bsel-clear" tabindex="-1" title="Quitar selección">&times;</button>');
            // El menú se agrega al <body> (position:fixed) para que no lo recorten
            // contenedores con overflow:hidden/auto (tarjetas, modales, etc.).
            const $menu = $('<div class="bsel-menu"></div>').appendTo('body');

            $wrap.append($input, $icono, $limpiar);
            $select.css('display', 'none').after($wrap);

            function posicionarMenu() {
                const rect = $wrap[0].getBoundingClientRect();
                $menu.css({
                    position: 'fixed',
                    left: rect.left + 'px',
                    top: rect.bottom + 4 + 'px',
                    width: rect.width + 'px'
                });
            }

            function ocultarMenu() {
                $menu.removeClass('show');
            }

            function sincronizar() {
                $input.val(textoSeleccionado($select));
                $wrap.toggleClass('is-selected', !!$select.val());
                const deshabilitado = !!$select.prop('disabled');
                $input.prop('disabled', deshabilitado);
                $wrap.toggleClass('is-disabled', deshabilitado);
            }

            function renderLocal(filtro) {
                const f = (filtro || '').toLowerCase();
                const items = opcionesVisibles($select).filter(function () {
                    return $(this).text().toLowerCase().includes(f);
                });
                $menu.empty();
                if (items.length === 0) {
                    $menu.append('<div class="bsel-empty">Sin resultados</div>');
                    return;
                }
                items.each(function () {
                    const $item = $('<div class="bsel-item"></div>')
                        .text($(this).text().trim())
                        .attr('data-value', $(this).val());
                    $menu.append($item);
                });
            }

            function seleccionarRemoto(item) {
                // Saca cualquier <option> que hayamos inyectado antes (solo dejamos
                // la que está seleccionada ahora) para no acumular basura en el <select>.
                $select.find('option[data-bsel-dinamica]').remove();
                const $op = $('<option data-bsel-dinamica="1"></option>').val(item.value).text(item.text);
                if (item.data) {
                    for (const clave in item.data) {
                        if (Object.prototype.hasOwnProperty.call(item.data, clave)) {
                            $op.attr('data-' + clave, item.data[clave]);
                        }
                    }
                }
                $select.append($op);
                $select.val(String(item.value)).trigger('change');
            }

            let ultimaPeticion = 0;
            let seleccionarPrimeroAlLlegar = false;
            function renderRemoto(filtro) {
                const q = (filtro || '').trim();
                const minLength = remoto.minLength || 1;
                if (q.length < minLength) {
                    $menu.empty().append('<div class="bsel-empty">Escriba para buscar…</div>');
                    seleccionarPrimeroAlLlegar = false;
                    return;
                }
                const idPeticion = ++ultimaPeticion;
                const params = $.extend({ q: q }, typeof remoto.params === 'function' ? remoto.params() : (remoto.params || {}));
                $.getJSON(remoto.url, params, function (res) {
                    if (idPeticion !== ultimaPeticion) return; // respuesta vieja, se descarta
                    const lista = remoto.parseResponse ? remoto.parseResponse(res) : (res.data || []);
                    $menu.empty();
                    if (!lista.length) {
                        $menu.append('<div class="bsel-empty">Sin resultados</div>');
                        seleccionarPrimeroAlLlegar = false;
                        return;
                    }
                    lista.forEach(function (crudo) {
                        const item = remoto.mapItem ? remoto.mapItem(crudo) : crudo;
                        $('<div class="bsel-item"></div>').text(item.text).data('bsel-item', item).appendTo($menu);
                    });
                    // Si el usuario apretó Enter antes de que llegara la respuesta
                    // (ej. escribió un código y no esperó el debounce), elegimos
                    // directamente el primer resultado apenas llega.
                    if (seleccionarPrimeroAlLlegar) {
                        seleccionarPrimeroAlLlegar = false;
                        seleccionarRemoto($menu.find('.bsel-item').first().data('bsel-item'));
                        ocultarMenu();
                        sincronizar();
                    }
                }).fail(function () {
                    if (idPeticion !== ultimaPeticion) return;
                    $menu.empty().append('<div class="bsel-empty">Error al buscar</div>');
                    seleccionarPrimeroAlLlegar = false;
                });
            }

            let temporizador = null;
            function render(filtro) {
                if (remoto) {
                    // Vacía el menú YA (sincrónico): si quedaba algo de una búsqueda
                    // anterior, no debe seguir ahí mientras se espera el debounce,
                    // porque Enter podría "elegir" un resultado viejo que ya no
                    // corresponde a lo que el usuario acaba de escribir.
                    const q = (filtro || '').trim();
                    const minLength = remoto.minLength || 1;
                    $menu.empty().append(
                        q.length < minLength
                            ? '<div class="bsel-empty">Escriba para buscar…</div>'
                            : '<div class="bsel-empty">Buscando…</div>'
                    );
                    clearTimeout(temporizador);
                    if (q.length >= minLength) {
                        temporizador = setTimeout(function () { renderRemoto(filtro); }, remoto.delay || 250);
                    }
                } else {
                    renderLocal(filtro);
                }
            }

            function seleccionarPrimerResultado() {
                const $primero = $menu.find('.bsel-item').first();
                if (!$primero.length) return false;
                if (remoto) {
                    seleccionarRemoto($primero.data('bsel-item'));
                } else {
                    $select.val(String($primero.attr('data-value'))).trigger('change');
                }
                ocultarMenu();
                sincronizar();
                return true;
            }

            $input.on('focus', function () {
                if ($select.prop('disabled')) return;
                render($input.val());
                posicionarMenu();
                $menu.addClass('show');
            });

            $input.on('input', function () {
                render($(this).val());
                posicionarMenu();
                $menu.addClass('show');
            });

            // Enter: elige el primer resultado ya mostrado. Si todavía no llegó
            // la respuesta (el usuario tipeó rápido y apretó Enter antes del
            // debounce), la búsqueda se dispara ya mismo y se selecciona apenas
            // llegue el resultado, sin esperar a que el usuario abra la lista.
            $input.on('keydown', function (e) {
                if (e.which !== 13 && e.key !== 'Enter') return;
                e.preventDefault();
                if (seleccionarPrimerResultado()) return;
                if (remoto) {
                    clearTimeout(temporizador);
                    seleccionarPrimeroAlLlegar = true;
                    renderRemoto($(this).val());
                }
            });

            $menu.on('mousedown', '.bsel-item', function (e) {
                e.preventDefault();
                if (remoto) {
                    seleccionarRemoto($(this).data('bsel-item'));
                } else {
                    const valor = $(this).attr('data-value');
                    $select.val(String(valor)).trigger('change');
                }
                ocultarMenu();
                sincronizar();
            });

            $limpiar.on('mousedown', function (e) {
                // preventDefault evita que el input pierda foco antes de limpiar
                e.preventDefault();
                e.stopPropagation();
                $select.find('option[data-bsel-dinamica]').remove();
                $select.val('').trigger('change');
                ocultarMenu();
                sincronizar();
                $input.val('').focus();
            });

            $(document).on('click', function (e) {
                if (!$.contains($wrap[0], e.target) && !$.contains($menu[0], e.target)) {
                    ocultarMenu();
                    sincronizar();
                }
            });

            // Reposicionar (o cerrar, si sale de vista) al hacer scroll o resize,
            // incluyendo scroll dentro de contenedores anidados (fase de captura).
            window.addEventListener('scroll', function () {
                if ($menu.hasClass('show')) posicionarMenu();
            }, true);
            $(window).on('resize', function () {
                if ($menu.hasClass('show')) posicionarMenu();
            });

            $select.on('change buscador-select:sync', sincronizar);

            new MutationObserver(sincronizar).observe(this, { attributes: true, attributeFilter: ['disabled'] });

            sincronizar();
        });
    };
})(jQuery);
