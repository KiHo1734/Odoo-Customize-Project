odoo.define('shopfloor.app', function (require) {
    "use strict";

    const ajax = require('web.ajax');

    function loadWorkorders() {
        ajax.jsonRpc('/shopfloor/workorders', 'call', {})
            .then(function (data) {
                console.log(data);
            });
    }

    document.addEventListener('DOMContentLoaded', loadWorkorders);
});
