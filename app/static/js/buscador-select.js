/**
 * Agrega un buscador a un <select> con muchas opciones (productos, proveedores,
 * solicitantes, etc). El <select> original no se toca: sigue funcionando igual
 * que antes (val(), change(), disabled, mostrar/ocultar <option> para filtros).
 * Uso: $('#cbo_producto').buscadorSelect({ placeholder: 'Buscar producto...' });
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

        return this.each(function () {
            const $select = $(this);
            if ($select.data('bsel-activo')) return;
            $select.data('bsel-activo', true);

            const $wrap = $('<div class="bsel-wrap"></div>');
            const $input = $('<input type="text" class="form-control bsel-input" autocomplete="off">')
                .attr('placeholder', opciones.placeholder);
            const $icono = $('<i class="fas fa-search bsel-icon"></i>');
            const $menu = $('<div class="bsel-menu"></div>');

            $wrap.append($input, $icono, $menu);
            $select.css('display', 'none').after($wrap);

            function sincronizar() {
                $input.val(textoSeleccionado($select));
                $wrap.toggleClass('is-selected', !!$select.val());
                const deshabilitado = !!$select.prop('disabled');
                $input.prop('disabled', deshabilitado);
                $wrap.toggleClass('is-disabled', deshabilitado);
            }

            function render(filtro) {
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

            $input.on('focus', function () {
                if ($select.prop('disabled')) return;
                render('');
                $menu.addClass('show');
            });

            $input.on('input', function () {
                render($(this).val());
                $menu.addClass('show');
            });

            $menu.on('mousedown', '.bsel-item', function (e) {
                e.preventDefault();
                const valor = $(this).attr('data-value');
                $select.val(String(valor)).trigger('change');
                $menu.removeClass('show');
                sincronizar();
            });

            $(document).on('click', function (e) {
                if (!$.contains($wrap[0], e.target)) {
                    $menu.removeClass('show');
                    sincronizar();
                }
            });

            $select.on('change buscador-select:sync', sincronizar);

            new MutationObserver(sincronizar).observe(this, { attributes: true, attributeFilter: ['disabled'] });

            sincronizar();
        });
    };
})(jQuery);
