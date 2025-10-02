
/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosPartner } from "@point_of_sale/app/store/models";

patch(PosPartner.prototype, {
    get searchString() {
        const base = `${this.name || ""}|${this.barcode || ""}|${this.phone || ""}|${this.mobile || ""}|${this.email || ""}`;
        const code = this.partner_internal_code || "";
        return code ? `${base}|${code}` : base;
    },
});

patch(PosPartner, {
    fields() {
        const fields = super.fields(...arguments);
        if (!fields.includes("partner_internal_code")) {
            fields.push("partner_internal_code");
        }
        return fields;
    },
});
