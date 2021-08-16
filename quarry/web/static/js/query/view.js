$( function () {
	function htmlEscape( str ) {
		return String( str )
			.replace( /&/g, '&amp;' )
			.replace( /"/g, '&quot;' )
			.replace( /'/g, '&#39;' )
			.replace( /</g, '&lt;' )
			.replace( />/g, '&gt;' );
	}

	CodeMirror.extendMode( 'sql', { electricChars: ')' } );
	function makeEditor() {
		return CodeMirror.fromTextArea( $( '#code' )[ 0 ], {
			mode: 'text/x-mariadb',
			theme: 'monokai',
			readOnly: !vars.can_edit,
			matchBrackets: true
		} );
	}

	var editor = makeEditor();
	$( '#query-description' ).autosize();
	$.ajax( {
		url: '/api/dbs',
		success: function ( data ) {
			addAutocompleteDB( document.getElementById( 'query-db' ), data.dbs );
		}
	} );

	function addAutocompleteDB( input_elem, options ) {
		/* Autocomplete an input element from the given array
		adapted from https://www.w3schools.com/howto/howto_js_autocomplete.asp*/
		var currentFocus;
		input_elem.addEventListener( 'input', function () {
			var list_elem, i, val = this.value;
			closeAllLists();
			if ( !val ) { return false; }
			currentFocus = -1;

			list_elem = $( '<div></div>', {
				id: this.id + '-autocomplete-list',
				'class': 'autocomplete-items'
			} );
			list_elem.appendTo( input_elem.parentElement );
			for ( i = 0; i < options.length; i++ ) {
				/* check if the item starts with the same letters as the text field value:*/
				if ( options[ i ].substr( 0, val.length ).toUpperCase() === val.toUpperCase() ) {
					$( '<div><strong>' + options[ i ].substr( 0, val.length ) + options[ i ].substr( val.length ) + '</strong><input type="hidden" value="' + options[ i ] + '">' )
						.on( {
							click: function () {
								input_elem.value = this.getElementsByTagName( 'input' )[ 0 ].value;
								closeAllLists();
							}
						} )
						.appendTo( list_elem );
					console.log( 'Got a matching element to', val, '  -> ', options[ i ] );
				}
			}
		} );

		input_elem.addEventListener( 'keydown', function ( e ) {
			var list_elem = document.getElementById( this.id + '-autocomplete-list' );
			if ( list_elem ) { list_elem = list_elem.getElementsByTagName( 'div' ); }
			if ( e.keyCode === 40 ) {
				/* If the arrow DOWN key is pressed,
				increase the currentFocus variable:*/
				currentFocus++;
				/* and and make the current item more visible:*/
				addActive( list_elem );
			} else if ( e.keyCode === 38 ) {
				/* If the arrow UP key is pressed,
				decrease the currentFocus variable:*/
				currentFocus--;
				/* and and make the current item more visible:*/
				addActive( list_elem );
			} else if ( e.keyCode === 13 ) {
				/* If the ENTER key is pressed, prevent the form from being submitted,*/
				e.preventDefault();
				if ( currentFocus > -1 ) {
				/* and simulate a click on the "active" item:*/
					if ( list_elem ) { list_elem[ currentFocus ].click(); }
				}
			}
		} );

		function addActive( list_elem ) {
			/* tag the next item in the list as active by adding the autocomplete-active class*/
			if ( !list_elem ) { return false; }
			removeActive( list_elem );
			if ( currentFocus >= list_elem.length ) { currentFocus = 0; }
			if ( currentFocus < 0 ) { currentFocus = ( list_elem.length - 1 ); }
			list_elem[ currentFocus ].classList.add( 'autocomplete-active' );
		}

		function removeActive( list_elem ) {
			/* clear all active items from the list*/
			for ( var i = 0; i < list_elem.length; i++ ) {
				list_elem[ i ].classList.remove( 'autocomplete-active' );
			}
		}

		function closeAllLists( not_to_close ) {
			/* close all autocomplete lists in the document, except the one passed as an argument:*/
			var i, autocomplete_items = document.getElementsByClassName( 'autocomplete-items' );
			for ( i = 0; i < autocomplete_items.length; i++ ) {
				if ( not_to_close !== autocomplete_items[ i ] && not_to_close !== input_elem ) {
					autocomplete_items[ i ].parentNode.removeChild( autocomplete_items[ i ] );
				}
			}
		}

		/* clear all autocomplete lists if there's a click anywhere */
		document.addEventListener( 'click', function ( e ) {
			closeAllLists( e.target );
		} );
	}

	if ( vars.can_edit ) {
		$( '#title' ).blur( function () {
			var title = $( '#title' ).val();
			$.post( '/api/query/meta', {
				query_id: vars.query_id,
				title: title
			} ).done( function ( /* data */ ) {
				document.title = ( title || 'Untitled query #' + vars.query_id ) + ' - Quarry';
			} );
		} );
	}

	$( '#togglehl' ).click( function () {
		if ( editor === null ) {
			editor = makeEditor();
		} else {
			editor.toTextArea();
			editor = null;
		}
	} );

	$( '#un-star-query' ).click( function () {
		$.post( '/api/query/unstar', {
			query_id: vars.query_id
		} ).done( function ( /* data */ ) {
			$( '#content' ).removeClass( 'starred' );
		} );
	} );

	$( '#star-query' ).click( function () {
		$.post( '/api/query/star', {
			query_id: vars.query_id
		} ).done( function ( /* data */ ) {
			$( '#content' ).addClass( 'starred' );
		} );
	} );

	$( '#query-description' ).blur( function () {
		$.post( '/api/query/meta', {
			query_id: vars.query_id,
			description: $( '#query-description' ).val()
		} ).done( function () {
			// Uh, do nothing?
		} );
	} );

	$( '#toggle-publish' ).click( function () {
		$.post( '/api/query/meta', {
			query_id: vars.query_id,
			published: vars.published ? 0 : 1
		} ).done( function ( /* data */ ) {
			$( '#content' ).toggleClass( 'published' );
			vars.published = !vars.published;
		} );
	} );

	$( '#run-code' ).click( function () {
		$.post( '/api/query/run', {
			text: editor !== null ? editor.getValue() : $( '#code' ).val(),
			query_database: $( '#query-db' ).val(),
			query_id: vars.query_id
		} )
			.done( function ( data ) {
				var d = JSON.parse( data );
				vars.output_url = d.output_url;
				$( '#query-progress' ).show();
				$( '#query-result-error' ).hide();
				$( '#query-result-success' ).hide();
				clearTimeout( window.lastStatusCheck );
				checkStatus( d.qrun_id, false );
			} )
			.fail( function ( resp ) {
				alert( resp.responseText );
			} );

		return false;
	} );

	function checkStatus( qrun_id, silent ) {
		var url = '/run/' + qrun_id + '/status';
		$.get( url ).done( function ( data ) {
			$( '#query-status' ).html( 'Query status: <strong>' + data.status + '</strong>' );
			$( '#query-result' ).html(
				nunjucks.render( 'query-status.html', data )
			);
			if ( data.status === 'complete' ) {
				if ( data.extra.resultsets.length ) {
					populateResults( qrun_id, 0, data.extra.resultsets.length );
				} else {
					$( '#query-result' ).prepend( '<p id="emptyresultsetmsg">This query returned no results.</p>' );
				}

				let runningdate = new Date( data.timestamp * 1000 ),
					// Compatibility handling, old requests do not have the execution time stored.
					headertext = 'Executed on ';
				if ( data.extra.runningtime ) {
					headertext = 'Executed in ' + data.extra.runningtime + ' seconds as of ';
				}
				$( '#query-result' ).prepend(
					'<p id="queryheadermsg">' + headertext + '<span title="' + runningdate.toString() + '">' +
					runningdate.toDateString() + '</span>.</p>'
				);

				if ( !silent && vars.preferences.use_notifications ) {
					let title = $( '#title' ).val() ? '"' + $( '#title' ).val() + '"' : 'Untitled query #' + vars.query_id;
					sendNotification( title + ' execution has been completed' );
				}
			} else if ( data.status === 'queued' || data.status === 'running' ) {
				window.lastStatusCheck = setTimeout( function () {
					checkStatus( qrun_id, false );
				}, 5000 );
			}

			$( '#show-explain' ).off().click( function () {
				$.get( '/explain/' + data.extra.connection_id ).done( function ( data ) {
					var $table = $( '#explain-results-table' );
					if ( !$table.length ) {
						$table = $( '<table>' ).attr( {
							'class': 'table',
							id: 'explain-results-table'
						} );

						$( '#query-result-container' ).append( $table );
					}

					populateTable( $table, data );
				} );
			} );
		} );
	}

	function populateTable( $table, data ) {
		var columns = [];
		$.each( data.headers, function ( i, header ) {
			columns.push( {
				title: htmlEscape( header ),
				render: function ( data /* , type, row */ ) {
					if ( typeof data === 'string' ) {
						return htmlEscape( data );
					} else {
						return data;
					}
				}
			} );
		} );

		$table.dataTable( {
			data: data.rows,
			columns: columns,
			scrollX: true,
			pagingType: 'simple_numbers',
			paging: data.rows.length > 100,
			pageLength: 100,
			deferRender: true,
			order: [],
			destroy: true
		} );

		// Ugly hack to ensure that table rows actually show
		// up. Otherwise they don't until you do a resize.
		// Browser and DOM bugs are the best.
		$table.DataTable().draw();
	}

	function slugifyTitle() {
		return ( $( '#title' ).val() || 'untitled' )
			.toLowerCase()
			.split( /[\t !"#$%&'()*-/<=>?@[\\\]^_`{|},.]+/g )
			.filter( function ( word ) { return word; } )
			.join( '-' );
	}

	function populateResults( qrun_id, resultset_id, till ) {
		var url = '/run/' + qrun_id + '/output/' + resultset_id + '/json';
		$.get( url ).done( function ( data ) {
			var tableContainer = $( nunjucks.render( 'query-resultset.html', {
					only_resultset: resultset_id === till - 1,
					resultset_number: resultset_id + 1,
					rowcount: data.rows.length,
					resultset_id: resultset_id,
					run_id: qrun_id,
					query_id: vars.query_id,
					slugify_title: slugifyTitle()
				} ) ),
				$table = tableContainer.find( 'table' );
			$( '#query-result' ).append( tableContainer );

			populateTable( $table, data );

			if ( resultset_id < till - 1 ) {
				populateResults( qrun_id, resultset_id + 1, till );
			}
		} );
	}

	function sendNotification( text ) {
		if ( Notification.permission === 'granted' ) {
			// eslint-disable-next-line no-new
			new Notification( 'Quarry', {
				icon: '/static/img/quarry-logo-icon.svg',
				body: text
			} );
		} else {
			console.log( 'Can\'t send notification, permission value is set to ' + Notification.permission );
			$.get( '/api/preferences/set/use_notifications/null' );
		}
	}

	if ( vars.qrun_id ) {
		checkStatus( vars.qrun_id, true );
	} else {
		$( '#query-status' ).text( 'This query has never yet been executed' );
	}
} );
