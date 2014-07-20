$( function() {
    var editor = CodeMirror.fromTextArea($("#code")[0], {
        mode: "text/x-mariadb",
        theme: "monokai"
    });
} );
