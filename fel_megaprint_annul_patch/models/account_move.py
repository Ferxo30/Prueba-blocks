# -*- encoding: utf-8 -*-
import logging, html, uuid, base64, re
from odoo import models, fields, _
from odoo.exceptions import UserError
from lxml import etree
import requests

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Utilidades FEL (tus funciones, con microajustes de estilo y comentarios)
# ---------------------------------------------------------------------
def _pick(model, rec, names):
    for n in names:
        if hasattr(rec, n):
            val = getattr(rec, n)
            if isinstance(val, str):
                if val.strip():
                    return val.strip()
            elif val:
                return val
    return False

def _env_is_test(move, journal_flag):
    is_test = False
    if isinstance(journal_flag, bool):
        is_test = journal_flag
    elif isinstance(journal_flag, str):
        is_test = journal_flag.lower() in ('test', 'pruebas', 'sandbox', 'dev', 'development')
    if not is_test and move.company_id:
        comp_flag = _pick(move, move.company_id, ['pruebas_fel', 'fel_pruebas'])
        if isinstance(comp_flag, bool):
            is_test = comp_flag
        elif isinstance(comp_flag, str):
            is_test = comp_flag.lower() in ('test', 'pruebas', 'sandbox', 'dev', 'development')
    return is_test

def _get_creds(move):
    j = move.journal_id
    usuario = _pick(move, j, ['usuario_fel', 'fel_usuario', 'fel_user', 'user_fel']) if j else False
    apikey  = _pick(move, j, ['clave_fel', 'fel_clave', 'fel_password', 'password_fel']) if j else False
    modo    = _pick(move, j, ['pruebas_fel', 'fel_pruebas', 'fel_environment']) if j else None
    if (not usuario or not apikey) and move.company_id:
        c = move.company_id
        usuario = usuario or _pick(move, c, ['usuario_fel'])
        apikey  = apikey  or _pick(move, c, ['clave_fel'])
    if not usuario or not apikey:
        raise UserError(_("Configure Usuario y API Key FEL en el Diario o en la Compañía."))
    return usuario, apikey, modo

def _request_token(api_host, usuario, apikey):
    headers_xml = {"Content-Type": "application/xml", "Accept": "application/xml"}
    payload = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<SolicitaTokenRequest><usuario>{u}</usuario><apikey>{k}</apikey></SolicitaTokenRequest>'
    ).format(u=usuario, k=apikey)
    url = f'https://{api_host}/api/solicitarToken'
    r = requests.post(url, data=payload.encode("utf-8"), headers=headers_xml, timeout=60)
    if not (r.text or "").strip():
        raise UserError(_("No se pudo solicitar token a Megaprint.\nURL: %s\nHTTP: %s\nRespuesta vacía") % (url, r.status_code))
    try:
        xml = etree.XML(r.text.encode("utf-8"))
    except Exception:
        _logger.exception("TokenResponse inválida (%s): %s", url, r.text)
        raise UserError(_("No se pudo solicitar token a Megaprint.\nURL: %s\nHTTP: %s\nRespuesta:\n%s") % (url, r.status_code, r.text))
    nodes = xml.xpath("//token")
    if not nodes or not nodes[0].text:
        raise UserError(_("Megaprint no devolvió token.\nURL: %s\nHTTP: %s\nRespuesta:\n%s") % (url, r.status_code, r.text))
    return nodes[0].text, url, r.text

def _retornar_xml(api_host, token, uuid_val):
    headers = {"Content-Type": "application/xml", "Accept": "application/xml", "authorization": "Bearer " + token}
    payload = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<RetornarXMLRequest><uuid>{u}</uuid></RetornarXMLRequest>'
    ).format(u=uuid_val)
    url = f'https://{api_host}/api/retornarXML'
    r = requests.post(url, data=payload.encode('utf-8'), headers=headers, timeout=60)
    try:
        xml = etree.XML((r.text or "").encode('utf-8'))
        node = xml.xpath('//xml_dte')
        if node and node[0].text:
            return html.unescape(node[0].text)
    except Exception:
        _logger.exception("No se pudo interpretar retornarXML: %s", r.text)
    return None

def _retornar_pdf_v2(api_host, token, uuid_val, xml_dte_text=None):
    headers = {"Content-Type": "application/xml", "Accept": "application/xml", "authorization": "Bearer " + token}
    url = f'https://{api_host}/api/retornarPDF'

    def _send_and_parse(payload):
        r = requests.post(url, data=payload.encode('utf-8'), headers=headers, timeout=60)
        try:
            xml = etree.XML((r.text or "").encode('utf-8'))
            pdf_node = xml.xpath('//pdf | //PDF')
            if pdf_node and (pdf_node[0].text or '').strip():
                return base64.b64decode(pdf_node[0].text)
            if xml.xpath('//listado_errores'):
                _logger.warning("retornarPDF devolvió errores: %s", r.text)
        except Exception:
            _logger.exception("retornarPDF no interpretable: %s", r.text)
        return None

    # 1) solo UUID
    payload_min = ('<?xml version="1.0" encoding="UTF-8"?><RetornaPDFRequest><uuid>{u}</uuid></RetornaPDFRequest>').format(u=uuid_val)
    pdf = _send_and_parse(payload_min)
    if pdf:
        return pdf
    # 2) con xml_dte
    if not xml_dte_text:
        xml_dte_text = _retornar_xml(api_host, token, uuid_val)
    if xml_dte_text:
        payload_full = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<RetornaPDFRequest><uuid>{u}</uuid><xml_dte><![CDATA[{xml}]]></xml_dte></RetornaPDFRequest>'
        ).format(u=uuid_val, xml=xml_dte_text)
        pdf = _send_and_parse(payload_full)
    return pdf or None

def _extract_annul_uuid_from_chatter(move):
    MM = move.env['mail.message'].sudo()
    msgs = MM.search([('model', '=', 'account.move'), ('res_id', '=', move.id)], order='id desc', limit=15)
    pat = re.compile(r'UUID de anulación:\s*([0-9A-Fa-f-]{36})')
    for m in msgs:
        mt = (m.body or '')
        mt = re.sub(r'<[^>]+>', ' ', mt)
        g = pat.search(mt)
        if g:
            return g.group(1)
    return None

def _save_pdf_on_move(move, pdf_bytes, filename):
    if not pdf_bytes:
        return False
    if 'pdf_fel' in move._fields:
        vals = {'pdf_fel': base64.b64encode(pdf_bytes)}
        if 'pdf_fel_filename' in move._fields:
            vals['pdf_fel_filename'] = filename
        move.write(vals)
    else:
        att = move.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(pdf_bytes),
            'res_model': 'account.move',
            'res_id': move.id,
            'mimetype': 'application/pdf',
        })
        if 'pdf_fel_attachment_id' in move._fields:
            move.write({'pdf_fel_attachment_id': att.id})
    return True

def _to_draft_then_cancel(move):
    # 1) volver a borrador / unpost
    for m in ('button_draft', 'action_draft', 'button_unpost'):
        if hasattr(move, m):
            try:
                getattr(move, m)()
                break
            except Exception as e:
                _logger.info("Intento %s falló: %s", m, e)
    # 2) cancelar
    for m in ('button_cancel', 'action_cancel', '_action_cancel'):
        if hasattr(move, m):
            getattr(move, m)()
            return True
    # 3) forzar state
    if 'state' in move._fields and any(opt[0] == 'cancel' for opt in move._fields['state'].selection):
        try:
            move.write({'state': 'cancel'})
            return True
        except Exception as e:
            _logger.info("No se pudo forzar state=cancel: %s", e)
    return False


# ---------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------
class AccountMove(models.Model):
    _inherit = "account.move"

    # Checkbox manual de control
    fel_annulled = fields.Boolean(
        string="Anulada FEL (manual)",
        help="Marca manualmente si el DTE fue anulado en certificador. Se bloquea automáticamente al anular por botón.",
        default=False,
        copy=False,
        tracking=True,
    )

    # Bloquear desmarcado del checkbox una vez activo
    def write(self, vals):
        if 'fel_annulled' in vals and vals['fel_annulled'] is False:
            for rec in self:
                if rec.fel_annulled:
                    raise UserError(_("No es posible desmarcar 'Anulada FEL' una vez activado."))
        return super().write(vals)

    # ------------------ POS helpers (nuevos) ------------------
    def _afcb__pos_orders_from_invoice(self):
        """Detecta órdenes POS ligadas a la factura por campos directos y por referencias visibles."""
        PosOrder = self.env["pos.order"]
        pos_orders = PosOrder

        has_account_move = "account_move" in PosOrder._fields
        has_account_move_id = "account_move_id" in PosOrder._fields
        has_invoice_id = "invoice_id" in PosOrder._fields
        has_pos_reference = "pos_reference" in PosOrder._fields

        for move in self:
            domains = []
            if has_account_move:
                domains.append([("account_move", "=", move.id)])
            if has_account_move_id:
                domains.append([("account_move_id", "=", move.id)])
            if has_invoice_id:
                domains.append([("invoice_id", "=", move.id)])

            candidates = list(filter(None, [
                getattr(move, "ref", None),
                getattr(move, "invoice_origin", None),
                getattr(move, "name", None),
                getattr(move, "payment_reference", None),
            ]))
            candidates = list(dict.fromkeys(candidates))
            if candidates:
                domains.append([("name", "in", candidates)])
                if has_pos_reference:
                    domains.append([("pos_reference", "in", candidates)])
                domains.append([("picking_ids.origin", "in", candidates)])

            if not domains:
                continue

            safe_domain = []
            for d in domains:
                safe_domain = (["|"] + safe_domain + d) if safe_domain else d

            found = PosOrder.search(safe_domain)
            if found:
                pos_orders |= found
            move.message_post(body=_("POS detectado (por dominios): %s") %
                                   (", ".join(found.mapped("name")) or "ninguno"))
        return pos_orders

    def _afcb__return_full_picking(self, picking):
        """Devuelve completamente un picking (wizard y fallback manual), y valida."""
        if picking.state != "done":
            self.message_post(body=_("Picking %s no está en estado 'Hecho'; se omite la devolución.") % picking.name)
            return

        ReturnWizard = self.env["stock.return.picking"].with_context(
            active_id=picking.id,
            active_ids=[picking.id],
            active_model="stock.picking",
        )
        return_type = getattr(picking.picking_type_id, "return_picking_type_id", False) or picking.picking_type_id

        # A) Wizard
        wizard_vals = {"picking_id": picking.id}
        if "location_id" in ReturnWizard._fields:
            wizard_vals["location_id"] = picking.location_dest_id.id
        if "location_dest_id" in ReturnWizard._fields:
            wizard_vals["location_dest_id"] = picking.location_id.id
        if "picking_type_id" in ReturnWizard._fields:
            wizard_vals["picking_type_id"] = return_type.id

        new_picking = False
        try:
            wiz = ReturnWizard.create(wizard_vals)
            if hasattr(wiz, "_onchange_picking_id"):
                wiz._onchange_picking_id()
            lines = getattr(wiz, "product_return_moves", False) or getattr(wiz, "move_ids", False)
            total_qty = 0.0
            for wline in lines:
                qty_done = 0.0
                if wline.move_id and hasattr(wline.move_id, "quantity_done"):
                    qty_done = wline.move_id.quantity_done
                if not qty_done:
                    qty_done = getattr(wline.move_id, "product_uom_qty", 0.0) or getattr(wline, "quantity", 0.0)
                if hasattr(wline, "quantity"):
                    wline.quantity = qty_done
                elif hasattr(wline, "quantity_done"):
                    wline.quantity_done = qty_done
                if hasattr(wline, "to_refund"):
                    wline.to_refund = True
                total_qty += qty_done

            if total_qty > 0:
                res = wiz._create_returns() if hasattr(wiz, "_create_returns") else (
                      wiz.create_returns() if hasattr(wiz, "create_returns") else None)
                new_picking_id = None
                if isinstance(res, (list, tuple)) and res:
                    new_picking_id = res[0]
                elif isinstance(res, dict):
                    new_picking_id = res.get("res_id")
                if not new_picking_id:
                    new = self.env["stock.picking"].search([
                        ("origin", "in", [picking.name, (picking.name or "") + " RETURN"]),
                        ("picking_type_id", "=", return_type.id),
                        ("location_id", "=", picking.location_dest_id.id),
                        ("location_dest_id", "=", picking.location_id.id),
                    ], order="id desc", limit=1)
                    if new:
                        new_picking_id = new.id
                if new_picking_id:
                    new_picking = self.env["stock.picking"].browse(new_picking_id)
        except Exception:
            new_picking = False

        # B) Fallback manual
        if not new_picking:
            StockPicking = self.env["stock.picking"]
            StockMove = self.env["stock.move"]
            new_picking = StockPicking.create({
                "picking_type_id": return_type.id,
                "location_id": picking.location_dest_id.id,   # cliente -> almacén
                "location_dest_id": picking.location_id.id,
                "origin": (picking.name or "") + " RETURN",
                "partner_id": picking.partner_id.id,
                "company_id": picking.company_id.id,
                "move_type": getattr(picking, "move_type", "direct"),
            })
            for mv in getattr(picking, "move_ids_without_package", picking.move_ids):
                qty = getattr(mv, "quantity_done", 0.0) or mv.product_uom_qty
                if qty <= 0:
                    continue
                StockMove.create({
                    "name": mv.name or mv.product_id.display_name,
                    "product_id": mv.product_id.id,
                    "product_uom": mv.product_uom.id,
                    "product_uom_qty": qty,
                    "picking_id": new_picking.id,
                    "location_id": picking.location_dest_id.id,
                    "location_dest_id": picking.location_id.id,
                    "company_id": picking.company_id.id,
                })

        # Confirmar y validar (sin reservar para entradas)
        if hasattr(new_picking, "action_confirm"):
            new_picking.action_confirm()
        ptype_code = getattr(new_picking.picking_type_id, "code", False)
        if ptype_code in ("outgoing", "internal"):
            try:
                if hasattr(new_picking, "action_assign"):
                    new_picking.action_assign()
            except Exception:
                pass
        for mv in getattr(new_picking, "move_ids_without_package", new_picking.move_ids):
            if hasattr(mv, "quantity_done") and not mv.quantity_done:
                mv.quantity_done = mv.product_uom_qty
        ctx = dict(self.env.context, skip_backorder=True)
        if hasattr(new_picking, "button_validate"):
            new_picking.with_context(ctx).button_validate()
        elif hasattr(new_picking, "_action_done"):
            new_picking.with_context(ctx)._action_done()

    # -----------------------------------------------------------------
    # BOTÓN PRINCIPAL: Anular FEL + Devolver picking POS + Cancelar move
    # -----------------------------------------------------------------
    def action_annul_fel_megaprint(self):
        """Anula FEL en Megaprint, actualiza PDF, devuelve picking POS y cancela la factura."""
        for move in self:
            # --- Validaciones FEL previas ---
            if not getattr(move, "requiere_certificacion", None):
                raise UserError(_("FEL no instalado correctamente: falta requiere_certificacion()."))
            if not move.requiere_certificacion():
                raise UserError(_("Este documento no requiere certificación FEL."))
            if not getattr(move, "firma_fel", None):
                raise UserError(_("La factura no posee firma FEL; no se puede anular."))

            # --- Credenciales / entorno ---
            usuario, apikey, modo = _get_creds(move)
            is_test = _env_is_test(move, modo)
            api_host   = "dev2.api.ifacere-fel.com" if is_test else "apiv2.ifacere-fel.com"
            firma_host = ("dev." if is_test else "") + "api.soluciones-mega.com"

            # --- 1) Token ---
            token, __token_url, __raw_token_resp = _request_token(api_host, usuario, apikey)

            # --- 2) XML de anulación sin firma ---
            if not hasattr(move, "dte_anulacion"):
                raise UserError(_("No se encontró dte_anulacion() en el modelo; verifique fel_gt/fel_megaprint."))
            dte = move.dte_anulacion()
            xml_sin_firma = etree.tostring(dte, encoding="UTF-8").decode("utf-8")

            # --- 3) Firma ---
            headers_auth = {"Content-Type": "application/xml", "authorization": "Bearer " + token, "Accept": "application/xml"}
            req_id = str(uuid.uuid5(uuid.NAMESPACE_OID, str(move.id))).upper()
            sign_payload = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<FirmaDocumentoRequest id="{rid}"><xml_dte><![CDATA[{xml}]]></xml_dte></FirmaDocumentoRequest>'
            ).format(rid=req_id, xml=xml_sin_firma)
            r = requests.post(f'https://{firma_host}/api/solicitaFirma', data=sign_payload.encode('utf-8'), headers=headers_auth, timeout=60)
            try:
                sign_xml = etree.XML((r.text or "").encode('utf-8'))
            except Exception:
                _logger.exception("FirmaResponse inválida: %s", r.text)
                raise UserError(_("Error al firmar XML de anulación.\nRespuesta cruda:\n%s") % (r.text or ""))
            signed_nodes = sign_xml.xpath("//xml_dte")
            if not signed_nodes or not signed_nodes[0].text:
                raise UserError(_("No se obtuvo xml_dte firmado.\nRespuesta:\n%s") % (r.text or ""))
            xml_firmado = html.unescape(signed_nodes[0].text)

            # --- 4) Anulación en Megaprint ---
            annul_payload = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<AnulaDocumentoXMLRequest id="{rid}"><xml_dte><![CDATA[{xml}]]></xml_dte></AnulaDocumentoXMLRequest>'
            ).format(rid=req_id, xml=xml_firmado)
            r = requests.post(f'https://{api_host}/api/anularDocumentoXML', data=annul_payload.encode('utf-8'), headers=headers_auth, timeout=60)
            try:
                annul_xml = etree.XML((r.text or "").encode('utf-8'))
            except Exception:
                _logger.exception("AnulaResponse inválida: %s", r.text)
                raise UserError(_("Error al enviar anulación.\nRespuesta cruda:\n%s") % (r.text or ""))
            if annul_xml.xpath("//listado_errores"):
                raise UserError(_("Megaprint devolvió errores:\n%s") % (r.text or ""))

            original_uuid = getattr(move, 'firma_fel', False)
            annul_uuid_nodes = annul_xml.xpath("//uuid")
            annul_uuid = (annul_uuid_nodes and annul_uuid_nodes[0].text) or False

            # --- 5) PDF automático ---
            pdf_bytes = None
            try:
                if original_uuid:
                    pdf_bytes = _retornar_pdf_v2(api_host, token, original_uuid)
                if not pdf_bytes and annul_uuid:
                    pdf_bytes = _retornar_pdf_v2(api_host, token, annul_uuid, xml_firmado)
            except Exception:
                _logger.exception("retornarPDF tras anulación falló")
            saved = _save_pdf_on_move(move, pdf_bytes, f"fel_anulacion_{(original_uuid or annul_uuid or 'doc')}.pdf")

            # --- 6) DEVOLUCIÓN DE PICKINGS POS (si los hay) ---
            pos_orders = move._afcb__pos_orders_from_invoice()
            if pos_orders:
                move.message_post(body=_("Órdenes POS vinculadas: %s") % ", ".join(pos_orders.mapped("name")))
                found_returns = 0
                for order in pos_orders:
                    pickings = order.picking_ids
                    if not pickings:
                        move.message_post(body=_("La orden POS %s no tiene pickings de entrega.") % (order.name))
                        continue
                    for picking in pickings:
                        try:
                            self._afcb__return_full_picking(picking)
                            found_returns += 1
                            move.message_post(body=_("Devolución creada/validada para picking %s.") % picking.name)
                        except Exception as e:
                            move.message_post(body=_("No se pudo devolver picking %s: %s") % (picking.name, e))
                if not found_returns and pickings:
                    move.message_post(body=_("Se hallaron %s pickings pero ninguna devolución pudo validarse.") % len(pickings))
            else:
                move.message_post(body=_("No se encontró ninguna orden POS vinculada a esta factura."))

            # --- 7) CANCELAR FACTURA EN ODOO ---
            # (liberar conciliaciones y cancelar; si no, volver a borrador y cancelar)
            try:
                if getattr(move, "line_ids", False) and hasattr(move.line_ids, "remove_move_reconcile"):
                    move.line_ids.remove_move_reconcile()
            except Exception:
                pass
            if not _to_draft_then_cancel(move):
                _logger.exception("No se pudo cancelar la factura tras anulación FEL (id=%s).", move.id)
                raise UserError(_("FEL anulado (UUID: %s), pero no pude cancelar la factura en Odoo.")
                                % (annul_uuid or original_uuid or '-'))

            # --- 8) Marcar checkbox y mensajería final ---
            move.write({'fel_annulled': True})
            body = _("FEL anulado correctamente en Megaprint.")
            if annul_uuid:
                body += _(" UUID de anulación: %s.") % annul_uuid
            if saved:
                body += _(" PDF FEL actualizado.")
            else:
                body += _(" (No fue posible actualizar el PDF en este momento).")
            move.message_post(body=body)

        return True

    # Alias por si tu botón se llama literalmente "anularFail"
    def anularFail(self):
        return self.action_annul_fel_megaprint()

    # ------------------ Botón: refrescar/actualizar PDF FEL (manual) ------------------
    def action_refresh_fel_pdf_megaprint(self):
        for move in self:
            if not getattr(move, "requiere_certificacion", None) or not move.requiere_certificacion():
                raise UserError(_("Este documento no requiere certificación FEL."))
            usuario, apikey, modo = _get_creds(move)
            is_test = _env_is_test(move, modo)
            api_host = "dev2.api.ifacere-fel.com" if is_test else "apiv2.ifacere-fel.com"

            token, __token_url, __raw_token_resp = _request_token(api_host, usuario, apikey)
            original_uuid = getattr(move, 'firma_fel', False)
            pdf_bytes = None

            if original_uuid:
                pdf_bytes = _retornar_pdf_v2(api_host, token, original_uuid)
            if not pdf_bytes:
                annul_uuid = _extract_annul_uuid_from_chatter(move)
                if annul_uuid:
                    pdf_bytes = _retornar_pdf_v2(api_host, token, annul_uuid)

            if not pdf_bytes:
                raise UserError(_("No fue posible obtener el PDF desde Megaprint. Verifique el UUID y el servicio RetornarPDF."))

            _save_pdf_on_move(move, pdf_bytes, f"fel_actualizado_{(original_uuid or 'doc')}.pdf")
            move.message_post(body=_("PDF FEL actualizado desde Megaprint."))
        return True
