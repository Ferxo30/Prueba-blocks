# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
import base64
import io
import logging

class AsistenteReporteVentas(models.TransientModel):
    _inherit = 'l10n_gt_extra.asistente_reporte_ventas'

    def print_report_excel_asistelibros(self):
        for w in self:
            result = []
            
            journal_ids = [x.id for x in w['diarios_id']]
            filtro = [
                ('state','in',['posted','cancel']),
                ('journal_id','in',journal_ids),
                ('date','<=',w['fecha_hasta']),
                ('date','>=',w['fecha_desde']),
            ]
            
            if 'type' in self.env['account.move'].fields_get():
                filtro.append(('type','in',['out_invoice','out_refund']))
            else:
                filtro.append(('move_type','in',['out_invoice','out_refund']))
    
            facturas = self.env['account.move'].search(filtro)

            for f in facturas:
                doc_criva = f.criva
                criva = f.valor_constancia
                local = True
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
                        total_lineas_servicio += l.price_unit*l.quantity*(100-l.discount)/100
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
                    'V' # Compra/Venta
                ]

                # Documento
                if f.type if 'type' in self.env['account.move'].fields_get() else f.move_type == 'out_invoice':
                    if 'firma_fel' in f.fields_get() and f.firma_fel:
                        r.append('FCE')
                    else:
                        r.append('FC')
                else:
                    r.append('NC')

                # Serie y numero
                if 'firma_fel' in f.fields_get() and f.firma_fel:
                    r.append('FACE'+f.serie_fel)
                    r.append(f.numero_fel)
                elif f.name and len(f.name.split('-',1)) > 1:
                    r.append(f.name.split('-', 1)[0])
                    r.append(f.name.split('-', 1)[1])
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

                # Local o exportacion
                if local:
                    r.append('L')
                else:
                    r.append('E')

                # Bien o servicio de exportacion
                if not local:
                    if f.tipo_gasto in ['compra','importacion','combustible','mixto']:
                        r.append('Bien')
                    else:
                        r.append('Servicio')
                else:
                    r.append('')

                # Emitido o anulado
                if f.state in ['open','paid']:
                    r.append('E')
                else:
                    r.append('A')

                # Orden cedula
                r.append('')

                # Registro cedula
                r.append('')

                # FAUCA o DUA y valor
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
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor bien exportacion
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if not local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor servicio local
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Valor servicio exportacion
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if not local and not f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Valor exento bien local
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor exento bien exportacion
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if not local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_bien))
                    else:
                        r.append('0')

                # Valor exento servicio local
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Valor exento servicio exportacion
                if f.state in ['cancel']:
                    r.append('')
                else:
                    if not local and f.cadi and f.amount_total != 0:
                        r.append('%.2f' % (tipo_cambio*total_lineas_servicio))
                    else:
                        r.append('0')

                # Tipo, numero y valor de constancia
                if f.state in ['cancel']:
                    r.append('')
                    r.append('')
                    r.append('')
                else:
                    if criva != 0:
                        r.append('CRIVA')
                        r.append(doc_criva)
                        r.append('%.2f' % criva)
                    else:
                        r.append('')
                        r.append('')
                        r.append('')

                # Valor bien pequeño local
                r.append('')

                # Valor servicios pequeño local
                r.append('')

                # Valor bien pequeño exportacion
                r.append('')

                # Valor servicios pequeño exportacion
                r.append('')

                # IVA
                if f.state in ['cancel']:
                    r.append('')
                else:
                    r.append('%.2f' % iva)

                # Total
                if f.state in ['cancel']:
                    r.append('%.2f' % 0)
                else:
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
            self.write({'archivo':datos, 'name':'asiste_libros_ventas.asl'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.asistente_reporte_ventas',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
