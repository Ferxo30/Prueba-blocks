# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
import base64
import io
import logging

class AsistenteReporteCompras(models.TransientModel):
    _inherit = 'l10n_gt_extra.asistente_reporte_compras'

    def print_report_excel_asistelibros(self):
        for w in self:
            result = []
            journal_ids = [x.id for x in w['diarios_id']]
            filtro = [
                ('state','in',['posted']),
                ('journal_id','in',journal_ids),
                ('date','<=',w['fecha_hasta']),
                ('date','>=',w['fecha_desde']),
            ]
            
            if 'type' in self.env['account.move'].fields_get():
                filtro.append(('type','in',['in_invoice','in_refund']))
            else:
                filtro.append(('move_type','in',['in_invoice','in_refund']))
            
            facturas = self.env['account.move'].search(filtro)
            impuesto = self.env['account.tax'].browse(w['impuesto_id'][0])

            for f in facturas:
                local = True
                peq = f.partner_id.pequenio_contribuyente
                total_quetzales = 0
                total_lineas_servicio = 0
                total_lineas_bien = 0
                if f.partner_id.country_id and f.partner_id.country_id.id != f.company_id.country_id.id:
                    local = False

                tipo_cambio = 1
                if f.currency_id.id == f.company_id.currency_id.id:
                    total_quetzales = abs(f.amount_total)
                else:
                    if f.line_ids:
                        for l in f.line_ids:
                            if l.account_id.reconcile:
                                total_quetzales += l.debit - l.credit
                    tipo_cambio = total_quetzales / f.amount_total
                    total_quetzales = abs(total_quetzales)

                for l in f.invoice_line_ids:
                    if f.tipo_gasto == 'servicio':
                        if not f.cadi:
                            if len(l.tax_ids) > 0 or peq:
                                total_lineas_servicio += l.price_unit*l.quantity*(100-l.discount)/100
                        else:
                            total_lineas_servicio += l.price_unit*l.quantity*(100-l.discount)/100
                    else:
                        if not f.cadi:
                            if len(l.tax_ids) > 0 or peq:
                                total_lineas_bien += l.price_unit*l.quantity*(100-l.discount)/100
                        else:
                            total_lineas_bien += l.price_unit*l.quantity*(100-l.discount)/100

                iva = 0
                for l in f.invoice_line_ids:
                    precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                    r = l.tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id, partner=f.partner_id)
    
                    if len(l.tax_ids) > 0:
                        for i in r['taxes']:
                            if i['id'] == w['impuesto_id'].id:
                                iva += i['amount']

                r = [
                    f.date,
                    str(f.journal_id.codigo_establecimiento), # Establecimiento
                    'C' # Compra/Venta
                ]

                # Documento
                if f.type if 'type' in self.env['account.move'].fields_get() else f.move_type == 'in_invoice':
                    if peq:
                        r.append('FPC')
                    elif f.dua:
                        r.append('DA')
                    elif f.fauca:
                        r.append('FA')
                    elif f.ref and len(f.ref.split('-')[0]) > 6:
                        r.append('FCE')
                    else:
                        r.append('FC')
                else:
                    r.append('NC')

                # Serie y numero
                if f.ref and len(f.ref.split('-', 1)) > 1:
                    r.append(f.ref.split('-', 1)[0])
                    r.append(f.ref.split('-', 1)[1])
                else:
                    r.append('')
                    r.append('')

                # Fecha
                r.append(f.date.strftime('%d/%m/%Y'))

                # NIT
                if f.state in ['cancel']:
                    r.append('0')
                elif f.partner_id.vat:
                    r.append(f.partner_id.vat.replace('-','').replace('/',''))
                else:
                    r.append('0')

                # Nombre
                r.append(f.partner_id.name)

                # Local o importacion
                if local:
                    r.append('L')
                else:
                    r.append('I')

                # Bien o servicio de importacion
                if not local and not f.dua:
                    if f.tipo_gasto in ['compra','importacion','combustible','mixto']:
                        r.append('Bien')
                    else:
                        r.append('Servicio')
                else:
                    r.append('')

                # Emitido o anulado
                r.append('')

                # Orden cedula
                r.append('')

                # Registro cedula
                r.append('')

                # FAUCA o DUA
                if not local:
                    if f.fauca:
                        r.append('FAUCA')
                        r.append(f.fauca)
                    elif f.dua:
                        r.append('DUA')
                        r.append(f.dua)
                    else:
                        r.append('')
                        r.append('')
                else:
                    r.append('')
                    r.append('')

                # Valor bien local
                if peq:
                    r.append('')
                else:
                    if local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor bien importacion
                if peq:
                    r.append('')
                else:
                    if not local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor servicio local
                if peq:
                    r.append('')
                else:
                    if local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Valor servicio importacion
                if peq:
                    r.append('')
                else:
                    if not local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Valor exento bien local
                if peq:
                    r.append('')
                else:
                    if local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor exento bien importacion
                if peq:
                    r.append('')
                else:
                    if not local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor exento servicio local
                if peq:
                    r.append('')
                else:
                    if local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Valor exento servicio importacion
                if peq:
                    r.append('')
                else:
                    if not local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Tipo de constancia
                r.append('')

                # Numero de constancia
                r.append('')

                # Valor de constancia
                r.append('')

                # Valor bien pequeño local
                if not peq:
                    r.append('')
                else:
                    r.append('%.2f' % (tipo_cambio*total_lineas_bien))

                # Valor servicios pequeño local
                if not peq:
                    r.append('')
                else:
                    r.append('%.2f' % (tipo_cambio*total_lineas_servicio))

                # Valor bien pequeño importacion
                r.append('')

                # Valor servicios pequeño importacion
                r.append('')

                # IVA
                r.append('%.2f' % iva)

                # Total
                if f.amount_total*(total_lineas_bien+total_lineas_servicio) > 0:
                    r.append('%.2f' % (tipo_cambio*(total_lineas_bien+total_lineas_servicio)))
                else:
                    r.append('%.2f' % 0)

                result.append(r)

            texto = ""
            for l in sorted(result, key=lambda x: x[1]+'-'+x[3]+'-'+str(x[0])+'-'+x[5]):
                l.pop(0)
                if len(l) < 30:
                    logging.warning(l)
                texto += '|'.join(l)+"\r\n"

            logging.warning(texto)

            datos = base64.b64encode(texto.rstrip().encode('utf-8'))
            self.write({'archivo':datos, 'name':'asiste_libros_compras.asl'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.asistente_reporte_compras',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
