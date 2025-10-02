/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/models";

// Ensure the POS order carries and prints the internal sequence (pos_internal_seq)
patch(Order.prototype, {
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (this.pos_internal_seq) {
            json.pos_internal_seq = this.pos_internal_seq;
        } else if (!("pos_internal_seq" in json) && this?.orderlines) {
            // keep key for downstream even if undefined
            json.pos_internal_seq = undefined;
        }
        return json;
    },
    init_from_JSON() {
        super.init_from_JSON(...arguments);
        const json = arguments[0] || {};
        if (json && Object.prototype.hasOwnProperty.call(json, "pos_internal_seq")) {
            this.pos_internal_seq = json.pos_internal_seq;
        }
    },
    export_for_printing() {
        const res = super.export_for_printing(...arguments);
        res.pos_internal_seq = this.pos_internal_seq ?? res.pos_internal_seq;
        return res;
    },
});
