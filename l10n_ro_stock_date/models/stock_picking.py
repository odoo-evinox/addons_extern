# Copyright (C) 2021-2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from datetime import timedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def force_accounting_date(self):
        for pick in self.filtered(lambda p: p.state == 'done'):
            if pick.accounting_date:
                body = f"<p>{_('Force Accounting Date: ') + str(pick.accounting_date)}</p>"
                body += f"<p>Scheduled Date: {pick.scheduled_date} --> {pick.accounting_date}</p>"
                body += f"<p>Effective Date: {pick.date_done} --> {pick.accounting_date}</p>"

                pick.message_post(body=body)                
                sp_query = """
                    update stock_picking
                        set scheduled_date = accounting_date,
                            date_done = accounting_date
                    where id = %s
                """
                self.env.cr.execute(sp_query, (pick.id, ))

                sm_query = """
                    update stock_move sm
                        set date = sp.accounting_date
                    from stock_picking sp
                    where
                        sp.id = sm.picking_id and
                        picking_id = %s
                """
                self.env.cr.execute(sm_query, (pick.id, ))
     
                sm_line_query = """            
                    update stock_move_line
                        set date = sm.date
                    from stock_move sm
                        where move_id = sm.id
                        and sm.picking_id = %s
                """
                self.env.cr.execute(sm_line_query, (pick.id, ))


                svl_query = """
                update stock_valuation_layer
                    set create_date = sm.date
                from stock_move sm
                    where stock_move_id = sm.id
                    and sm.picking_id = %s
                """
                self.env.cr.execute(svl_query, (pick.id, ))

                am_query = """
                update account_move am
                    set date = svl.create_date
                from stock_valuation_layer svl
                left join stock_move sm on svl.stock_move_id = sm.id

                where 
                    svl.account_move_id = am.id
                    and sm.picking_id = %s
                """
                self.env.cr.execute(am_query, (pick.id, ))            

