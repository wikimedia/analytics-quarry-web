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

	if ( vars.can_edit ) {
		$( '#title' ).blur( function () {
			$.post( '/api/query/meta', {
				query_id: vars.query_id,
				title: $( '#title' ).val()
			} ).done( function ( /* data */ ) {
				// Uh, do nothing
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
			query_id: vars.query_id
		} ).done( function ( data ) {
			var d = JSON.parse( data );
			vars.output_url = d.output_url;
			$( '#query-progress' ).show();
			$( '#query-result-error' ).hide();
			$( '#query-result-success' ).hide();
			clearTimeout( window.lastStatusCheck );
			checkStatus( d.qrun_id, false );
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
