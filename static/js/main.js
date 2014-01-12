$(document).ready(function() {

    $("#fb-login-btn").click(function() {
        FB.login(function(response) {
            if (response.authResponse) {
                console.log("Successful login")
            } else {
                console.log("Failed login");
            }
        }, { scope: 'publish_actions,publish_stream,user_photos' });

        return false;
    });

});