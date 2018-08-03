$( function() {
    if ( $( "#option-useNotifications" ).length ) {
        if ( !window.Notification ) {
            $( "#option-useNotifications .error" ).css( 'display', 'inline' );
            $( "#option-useNotifications-checkbox" ).prop( 'disabled', true );
        }

        $( "#option-useNotifications-checkbox" ).prop( "checked", vars.preferences[ 'use_notifications' ] );

        $( "#option-useNotifications-checkbox" ).change( function () {
            if ( this.checked ) {
                Notification.requestPermission().then( function( result ) {
                    if ( result === 'granted' ) {
                        var notification = new Notification( 'Quarry', {
                            icon: '/static/img/quarry-logo-icon.svg',
                            body: 'Test notification!',
                        } );
                        $.get( '/api/preferences/set/use_notifications/1' );
                    } else if ( result === 'denied' ) {
                        alert( "Can't get notifications permission." );
                        this.checked = false;
                    } else {
                        alert( 'You need to allow notifications for this website to enable this option.' );
                        this.checked = false;
                    }
                } );
            } else {
                $.get( '/api/preferences/set/use_notifications/null' );
            }
        } );
    }
} );
