odoo.define('payment_sagepay.payment_in', function (require) {
"use strict";
var ajax = require('web.ajax');
    $(document).ready(function()
      {
        $( "#paypal_button" ).addClass( "hidden" );
        $('input[type=radio][name=payment_rad]').change(function() {
            if (this.id == 'paypal_payment') {
                $( "#panel_body" ).addClass( "hidden" );
                $( "#paypal_button" ).removeClass( "hidden" );
            }
            else if (this.id == 'card_payment') {
                $( "#panel_body" ).removeClass( "hidden" );
                $( "#paypal_button" ).addClass( "hidden" );
            }
      });
        var counter = 0;
        $('#expiry').keyup(function()
        {
            counter += 1;
            if (counter == 2) {
                $(this).val($(this).val() + "/");
            };
            if ($('#expiry').val().length == 0) {
                console.log("hik");
                counter = 0;
            };
        });
    });
});
