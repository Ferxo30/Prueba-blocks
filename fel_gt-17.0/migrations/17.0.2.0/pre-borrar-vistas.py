import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    util.records.remove_view(cr, xml_id="fel_gt.invoice_form_fel_gt")
    util.records.remove_view(cr, xml_id="fel_gt.journal_form_fel_gt")
    util.records.remove_view(cr, xml_id="fel_gt.view_tax_form_fel_gt")
    util.records.remove_view(cr, xml_id="fel_gt.view_partner_form_fel_gt")
    util.records.remove_view(cr, xml_id="fel_gt.view_company_form_fel_gt")
    _logger.info("Vistas viejas borradas")
