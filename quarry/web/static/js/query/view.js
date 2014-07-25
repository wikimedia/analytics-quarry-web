$( function() {
    var editor = CodeMirror.fromTextArea($("#code")[0], {
        mode: "text/x-mariadb",
        theme: "monokai",
        readOnly: !vars.can_edit
    });

    if (vars.can_edit) {
        $('#title').editable(function(value, settings) {
            $.post( "/api/query/meta", {
                query_id: vars.query_id,
                title: value
            } ).done( function( data ) {
                alert( data );
            } );
            return value;
        }, {
            tooltip: 'Click to edit',
            height: 'None',
        } );
    }

    $('#run-code').click( function() {
        $.post( "/api/query/new", {
            text: editor.getValue(),
            query_id: vars.query_id
        }).done( function( data ) {
            var d = JSON.parse(data);
            $.post( "/api/query/run", {
                query_rev_id: d.id,
            }).done( function( data ) {
                alert( data );
            });
        } );
    } );

} );
