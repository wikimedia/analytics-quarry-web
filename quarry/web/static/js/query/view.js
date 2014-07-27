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
                var d =  JSON.parse(data);
                vars.output_url = d.output_url;
                $("#query-progress").show();
                $("#query-result-error").hide();
                $("#query-result-success").hide();
                checkOutput();
            });
        } );

        return false;
    } );

    function checkOutput() {
        if (vars.output_url) {
            $.get( vars.output_url ).done( function( data ) {
                var d = JSON.parse(data);
                if (d.result === 'ok') {
                    $("#query-result-success table").remove();
                    $.each(d.data, function( i, item ) {
                        var table = swig.render(query_success_template,
                            { locals: item }
                        );
                        $("#query-result-success").append(table);
                    } );
                    $("#success-time").text(d.time.toFixed(4) + "s");
                    $("#query-progress").hide();
                    $("#query-result-error").hide();

                    $("#query-result-success").show();
                    $("#query-result-killed").hide();
                } else if (d.result === 'error') {
                    $("#error-time").text(d.time.toFixed(4) + "s");
                    $("#query-error-message").text(d.error);
                    $("#query-progress").hide();
                    $("#query-result-error").show();
                    $("#query-result-success").hide();
                    $("#query-result-killed").hide();
                } else if (d.result === 'killed' ) {
                    $("#killed-time").text(d.time.toFixed(4) + "s");
                    $("#query-progress").hide();
                    $("#query-result-error").hide();
                    $("#query-result-success").hide();
                    $("#query-result-killed").show();
                }
            } ).fail( function() {
                setTimeout( checkOutput, 5000 );
            } );
        }
    }

    checkOutput();

    var query_success_template = "" +
        "<table class='table table-bordered table-hover'>" +
            "<tr>" +
            "{% for c in headers %}" +
                "<th>{{ c }}</th>" +
            "{% endfor %}" +
            "</tr>" +
            "{% for r in rows %}" +
            "<tr>" +
                "{% for d in r %}" +
                "<td>{{ d }}</td>" +
                "{% endfor %}" +
            "</tr>" +
            "{% endfor %}" +
        "</table>";
} );
