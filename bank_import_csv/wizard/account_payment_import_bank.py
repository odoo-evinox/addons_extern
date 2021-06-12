import csv
import codecs
import io

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base.models.res_bank import sanitize_account_number
_reader = codecs.getreader('utf-8')

logger = logging.getLogger(__name__)

transilvania_table_header =  ['Data tranzactie', 'Data valuta', 'Descriere', 'Referinta tranzactiei', 'Debit', 'Credit', 'Sold contabil']
table_header_to_payment_fields = ['date' ,False,          'original_description', 'bank_tranzaction_uniqueid',  False, False,  'bank_balance']
debit_index = 4
credit_index = 5

class AccountPaymentImportBank(models.TransientModel):
    _name = "account.payment.import.bank"
    _description = "Import Bank Statement Files as payments ( not account.bank.statement)"

    statement_file = fields.Binary(
        string="Statement File",
        required=True,
        help="Get you bank statements in electronic format from your bank "
        "and select them here.",
    )
    journal_id = fields.Many2one('account.journal',domain=[('type','=','bank')],require=1, default=lambda self: self.env['account.journal'].search([('type','=','bank')],limit=1))
    suported_formats = fields.Char(default='*.csv format for Banca Transilvania;', help="list of file types and the bank that is for", readonly=1)
    statement_filename = fields.Char()


    def import_file_button(self):
        """Process the file chosen in the wizard, create bank statement(s)
        and return an action."""
        self.ensure_one()
        if not self.statement_filename.endswith('.csv'):
            raise UserError('The file does not have the extersion .csv. We are not continuing')
        if not self.journal_id or (not self.journal_id.bank_id) or ('ransilvania' not in self.journal_id.bank_id.name):
            raise UserError(f'The journal that you choose is has bank name = {self.journal_id.bank_id.name} and does not contain Transilvania in it so we are not going to continue')
        if self.journal_id.type != 'bank':
            raise UserError(f'The Journal type is not bank is {self.journal_id.type}')

            
        result = {
            "statement_ids": [],
            "notifications": [],
        }
        logger.info("Start to import bank statement file %s", self.statement_filename)
        file_data = base64.b64decode(self.statement_file)
        stream = io.BytesIO(file_data)
        reader  = csv.reader(_reader(stream), quotechar='"', delimiter=',')
        values = []
        
        transaction_rows = False 
        try:
            for fields in reader:
                if fields == transilvania_table_header :
                    if  transaction_rows:
                        raise UserError(f'We found 2 lines with header ={transilvania_table_header}, something is wrong')
                    logger.info(f"I found the start of table = {transilvania_table_header}")
                    transaction_rows = True
                    continue
                if not transaction_rows:
                    continue
                # from here are the transactions that we are going to process
                payment_value_to_wirte = {'journal_id':self.journal_id}
                for field_name, value in zip(table_header_to_payment_fields,fields):
                    if  field_name:
                        payment_value_to_wirte[field_name] =  value
                debit = field_name[debit_index] *-1
                credit = field_name[credit_index] 
                if debit:
                    payment_value_to_wirte['payment_type'] = 'outbound' 
                    payment_value_to_wirte['amount'] = float(debit)
                    payment_value_to_wirte['partner_type'] = 'supplier'
                else:
                    payment_value_to_wirte['payment_type'] = 'inbound'
                    payment_value_to_wirte['amount'] = float(credit)
                    payment_value_to_wirte['partner_type'] = 'customer'
                payment_value_to_wirte['amount']=  float(payment_value_to_wirte['bank_balance'])
                values += [payment_value_to_wirte]
        except Exception as e:
            raise UserError(
                _(
                    "The following problem occurred during import. "
                    "The file might not be valid.\n\n %s"
                )
                % str(e)
            )
        
                
        if not values:
            raise UserError( "We did not find any values to import in this file"            )
        # self.env["ir.attachment"].create(self._prepare_create_attachment(result))
        # if self.env.context.get("return_regular_interface_action"):
            # action = (
                # self.env.ref("account.action_bank_statement_tree").sudo().read([])[0]
            # )
            # if len(result["statement_ids"]) == 1:
                # action.update(
                    # {
                        # "view_mode": "form,tree",
                        # "views": False,
                        # "res_id": result["statement_ids"][0],
                    # }
                # )
            # else:
                # action["domain"] = [("id", "in", result["statement_ids"])]
        # else:
            # # dispatch to reconciliation interface
            # lines = self.env["account.bank.statement.line"].search(
                # [("statement_id", "in", result["statement_ids"])]
            # )
            # action = {
                # "type": "ir.actions.client",
                # "tag": "bank_statement_reconciliation_view",
                # "context": {
                    # "statement_line_ids": lines.ids,
                    # "company_ids": self.env.user.company_ids.ids,
                    # "notifications": result["notifications"],
                # },
            # }
        # return action

    def _prepare_create_attachment(self, result):
        vals = {
            "name": self.statement_filename,
            # Attach to first bank statement
            "res_id": result["statement_ids"][0],
            "res_model": "account.bank.statement",
            "datas": self.statement_file,
        }
        return vals
