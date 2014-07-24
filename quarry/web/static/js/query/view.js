$( function() {
    var editor = CodeMirror.fromTextArea($("#code")[0], {
        mode: "text/x-mariadb",
        theme: "monokai",
        readOnly: !vars.can_edit
    });

    $('#run-code').click( function() {
        $.post( "/api/query/new", {
            text: editor.getValue(),
            query_id: vars.query_id
        }).done( function( data ) {
            alert( data );
        } );
    } );

} );
