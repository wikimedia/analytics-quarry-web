$( function() {
    var editor = CodeMirror.fromTextArea($("#code")[0], {
        mode: "text/x-mariadb",
        theme: "monokai",
        readOnly: !vars.can_edit,
        matchBrackets: true
    });

    if (vars.can_edit) {
        $('#title').editable(function(value, settings) {
            $.post( "/api/query/meta", {
                query_id: vars.query_id,
                title: value
            } ).done( function( data ) {
            } );
            return value;
        }, {
            tooltip: 'Click to edit',
            height: 'None',
        } );
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
            checkOutput();
        } );

        return false;
    } );

    function checkOutput() {
        if (vars.output_url) {
            $.get( vars.output_url ).done( function( d ) {
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
