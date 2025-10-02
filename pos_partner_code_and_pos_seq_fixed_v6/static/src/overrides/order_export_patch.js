/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    export_for_printing() {
        const res = super.export_for_printing(...arguments);
        // Si backendOrder trae el correlativo
        if (this.backendOrder && this.backendOrder.pos_internal_seq) {
            res.pos_internal_seq = this.backendOrder.pos_internal_seq;
        }
        // Si la orden local lo trae con otro nombre
        if (!res.pos_internal_seq) {
            if (this.pos_internal_seq) {
                res.pos_internal_seq = this.pos_internal_seq;
            } else if (this.internal_pos_sequence) {
                res.pos_internal_seq = this.internal_pos_sequence;
            }
        }
        return res;
    },
});