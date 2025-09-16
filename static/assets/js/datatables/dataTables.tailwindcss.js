/*! DataTables Tailwind CSS integration
 */

(function( factory ){
	if ( typeof define === 'function' && define.amd ) {
		// AMD
		define( ['jquery', 'datatables.net'], function ( $ ) {
			return factory( $, window, document );
		} );
	}
	else if ( typeof exports === 'object' ) {
		// CommonJS
		var jq = require('jquery');
		var cjsRequires = function (root, $) {
			if ( ! $.fn.dataTable ) {
				require('datatables.net')(root, $);
			}
		};

		if (typeof window === 'undefined') {
			module.exports = function (root, $) {
				if ( ! root ) {
					// CommonJS environments without a window global must pass a
					// root. This will give an error otherwise
					root = window;
				}

				if ( ! $ ) {
					$ = jq( root );f
				}

				cjsRequires( root, $ );
				return factory( $, root, root.document );
			};
		}
		else {
			cjsRequires( window, jq );
			module.exports = factory( jq, window, window.document );
		}
	}
	else {
		// Browser
		factory( jQuery, window, document );
	}
}(function( $, window, document ) {
'use strict';
var DataTable = $.fn.dataTable;



/*
 * This is a tech preview of Tailwind CSS integration with DataTables.
 */

// Set the defaults for DataTables initialisation
$.extend( true, DataTable.defaults, {
	renderer: 'tailwindcss'
} );


// Default class modification
$.extend( true, DataTable.ext.classes, {
	container: "dt-container dt-tailwindcss",
	search: {
		input: "form-control py-2"
	},
	length: {
		select: ""
	},
	processing: {
		container: "dt-processing"
	},
	paging: {
		active: 'bg-lightprimary dark:bg-darkprimary',
		notActive: '',
		button: 'min-h-10 min-w-10 justify-center inline-block items-center text-center text-dark bg-hover py-2 px-3 text-sm rounded-lg focus:outline-none  disabled:opacity-50 disabled:pointer-events-none dark:text-darklink',
	},
	table: 'dataTable min-w-full',
	thead: { cell: 'p-4 text-base text-start font-semibold text-link dark:text-white capitalize' },
	tbody: {
		cell: 'text-dark dark:text-darklink p-4 border-b border-light-dark whitespace-nowrap'
	},
	tfoot: {
		cell: 'p-3 text-left hidden '
	},
} );

DataTable.ext.renderer.pagingButton.tailwindcss = function (settings, buttonType, content, active, disabled) {
	var classes = settings.oClasses.paging;
	var btnClasses = [classes.button];

	btnClasses.push(active ? classes.active : classes.notActive);
	btnClasses.push(disabled ? classes.notEnabled : classes.enabled);

	var a = $('<a>', {
		'href': disabled ? null : '#',
		'class': btnClasses.join(' ')
	})
		.html(content);

	return {
		display: a,
		clicker: a
	};
};

DataTable.ext.renderer.pagingContainer.tailwindcss = function (settings, buttonEls) {
	var classes = settings.oClasses.paging;

	buttonEls[0].addClass(classes.first);
	buttonEls[buttonEls.length -1].addClass(classes.last);

	return $('<ul/>').addClass('pagination sm:flex  sm:mt-0 mt-4 items-center gap-x-1 ').append(buttonEls);
};

DataTable.ext.renderer.layout.tailwindcss = function ( settings, container, items ) {
	var row = $( '<div/>', {
			"class": items.full ?
				'grid grid-cols-1 gap-4' :
				'gap-4 sm:flex  justify-between p-4 items-center'
		} )
		.appendTo( container );

	$.each( items, function (key, val) {
		var klass;

		// Apply start / end (left / right when ltr) margins
		if (val.table) {
			klass = 'col-span-2';
		}
		else if (key === 'start') {
			klass = 'justify-self-start';
		}
		else if (key === 'end') {
			klass = 'justify-end';
		}
		else {
			klass = 'col-span-2 justify-self-center';
		}

		$( '<div/>', {
				id: val.id || null,
				"class": klass + ' ' + (val.className || '')
			} )
			.append( val.contents )
			.appendTo( row );
	} );
};


return DataTable;
}));
