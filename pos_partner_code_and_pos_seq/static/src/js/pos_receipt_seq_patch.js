
/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },
    async beforeShow() {
        if (super.beforeShow) await super.beforeShow();
        const order = this.currentOrder;
        if (order && order.backendId && !order.internal_pos_sequence) {
            try {
                const recs = await this.orm.read("pos.order", [order.backendId], ["internal_pos_sequence"]);
                if (recs && recs[0]) {
                    order.internal_pos_sequence = recs[0].internal_pos_sequence;
                }
            } catch (e) {
                // silencioso: si no se pudo leer, no rompe el recibo
            }
        }
    },
    export_for_printing() {
        const data = super.export_for_printing(...arguments);
        const seq = this.currentOrder ? (this.currentOrder.internal_pos_sequence || null) : null;
        if (seq) {
            data.internal_pos_sequence = seq;
        }
        return data;
    },
});
