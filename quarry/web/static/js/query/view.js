$( function() {
    var editor = CodeMirror.fromTextArea($("#code")[0], {
        mode: "text/x-mariadb",
        theme: "monokai",
        readOnly: !vars.can_edit,
        matchBrackets: true
    });

    if (vars.can_edit) {
        $('#title').blur(function() {
            $.post( "/api/query/meta", {
                query_id: vars.query_id,
                title: $('#title').val()
            } ).done( function( data ) {
                // Uh, do nothing
            } );
        });
    }

    $("#un-star-query").click( function() {
        $.post( "/api/query/unstar", {
            query_id: vars.query_id
        }).done(function( data ) {
            $('#content').removeClass('starred');
        });
    });

    $("#star-query").click( function() {
        $.post( "/api/query/star", {
            query_id: vars.query_id
        }).done(function( data ) {
            $('#content').addClass('starred');
        });
    });

    $("#query-description").blur( function() {
        $.post( "/api/query/meta", {
            query_id: vars.query_id,
            description: $("#query-description").val()
        } ).done( function() {
            // Uh, do nothing?
        } );
    } );

    $("#toggle-publish").click( function() {
        $.post( "/api/query/meta", {
            query_id: vars.query_id,
            published: vars.published ? 0 : 1
        }).done(function( data ) {
            $("#content").toggleClass("published");
            vars.published = !vars.published;
        } );
    } );

    $('#run-code').click( function() {
        $.post( "/api/query/run", {
            text: editor.getValue(),
            query_id: vars.query_id
        }).done( function( data ) {
            var d = JSON.parse(data);
            vars.output_url = d.output_url;
            $("#query-progress").show();
            $("#query-result-error").hide();
            $("#query-result-success").hide();
            clearTimeout( window.lastStatusCheck );
            checkStatus(d.qrun_id);
        } );

        return false;
    } );

    function checkStatus(qrun_id) {
        var url = '/run/' + qrun_id + '/status';
        $.get( url ).done( function( data ) {
            $( "#query-status" ).html( 'Query status: <strong>' + data.status + '</strong>' );
            $('#query-result').html(
                nunjucks.render( 'query-status.html', data )
            );
            if ( data.status === 'complete' ) {
                // kick off other things!
                populateResults( qrun_id, 0, data.extra.resultsets.length );
            } else if ( data.status === 'queued' || data.status === 'running' ) {
                window.lastStatusCheck = setTimeout( function() { checkStatus( qrun_id ); }, 5000 );
            }
        } );
    }

    function populateResults(qrun_id, resultset_id, till) {
        var url = '/run/' + qrun_id + '/output/' + resultset_id + '/json';
        console.log( url );
        $.get( url ).done( function( data ) {
            var columns = [];
            $.each( data.headers, function( i, header ) {
                columns.push( { 'title': header } );
            } );

            var tableContainer = $( nunjucks.render( 'query-resultset.html', {
                'only_resultset': resultset_id === till - 1,
                'resultset_number': resultset_id + 1,
                'rowcount': data.rows.length,
                'resultset_id': resultset_id,
                'run_id': qrun_id
            } ) );
            var table = tableContainer.find( 'table' );
            $( table ).dataTable({
                'data': data.rows,
                'columns': columns,
                'scrollX': true,
                'pagingType': 'simple_numbers',
                'paging': data.rows.length > 100,
                'pageLength': 100,
                'deferRender': true
            } );

            $( '#query-result' ).append( tableContainer );

            // Ugly hack to ensure that table rows actually show
            // up. Otherwise they don't until you do a resize.
            // Browser and DOM bugs are the best.
            $( table ).DataTable().draw();

            if ( resultset_id < till - 1 ) {
                populateResults( qrun_id, resultset_id + 1, till );
            }
        } );
    }

    if ( vars.qrun_id ) {
        checkStatus(vars.qrun_id);
    }
} );
