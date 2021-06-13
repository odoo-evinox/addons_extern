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
    text = fields.Char(default='Pentru retrageri de numerar se va considera ca contul de casa este primul jurnal de cash / registru de casa gasit',  readonly=1)
    statement_filename = fields.Char()
    post_this_payments = fields.Boolean(default=True, help="If you check this after the creation of payments is going to post them")


    def import_file_button(self):
        """Process the file chosen in the wizard, create bank statement(s)
        and return an action."""
        self.ensure_one()
        Payment = self.env['account.payment']
        if not self.statement_filename.endswith('.csv'):
            raise UserError('The file does not have the extersion .csv. We are not continuing')
        if not self.journal_id or (not self.journal_id.bank_id) or ('ransilvania' not in self.journal_id.bank_id.name):
            raise UserError(f'The journal that you choose is has bank name = {self.journal_id.bank_id.name} and does not contain Transilvania in it so we are not going to continue')
        if self.journal_id.type != 'bank':
            raise UserError(f'The Journal type is not bank is {self.journal_id.type}')

            
        result = {
            "written_payments_ids": [],  # list of tuple(resulted_object ,readon/notificatoin,written values) 
            "not_written_payments_ids": [],
            'error_payments_ids':[],
        }
        logger.info("Start to import bank statement file %s", self.statement_filename)
        file_data = base64.b64decode(self.statement_file)
        stream = io.BytesIO(file_data)
        reader  = csv.reader(_reader(stream), quotechar='"', delimiter=',')
        values = []
        
        transaction_rows = False 
        try:
            for fields in reader:
                if not fields:
                    continue
                if fields == transilvania_table_header :
                    if  transaction_rows:
                        raise UserError(f'We found 2 lines with header ={transilvania_table_header}, something is wrong')
                    logger.info(f"I found the start of table = {transilvania_table_header}")
                    transaction_rows = True
                    continue
                if not transaction_rows:
                    continue
                # from here are the transactions that we are going to process
                payment_value_to_wirte = {'journal_id':self.journal_id.id}
                for field_name, value in zip(table_header_to_payment_fields,fields):
                    if  field_name:
                        payment_value_to_wirte[field_name] =  value
                debit = float(fields[debit_index].replace(',','') or '0') *-1
                credit = float(fields[credit_index].replace(',','') or '0' )
                if debit:  # debit and credit are from bank point of view
                    payment_value_to_wirte['payment_type'] = 'outbound' 
                    payment_value_to_wirte['amount'] = debit
                    payment_value_to_wirte['partner_type'] = 'supplier'
                else:
                    payment_value_to_wirte['payment_type'] = 'inbound'
                    payment_value_to_wirte['amount'] = credit
                    payment_value_to_wirte['partner_type'] = 'customer'
                payment_value_to_wirte['bank_balance']=  float(payment_value_to_wirte['bank_balance'].replace(',','') )
                values += [payment_value_to_wirte]
#                print(payment_value_to_wirte)
        except Exception as e:
            raise UserError(_("The following problem occurred during parsing import file.\n\n %s")% str(e))
        
                
        if not values:
            raise UserError( "We did not find any values to import in this file" )
        sequence_date = ''
        index=0  # used to create the squence for transaction 
        fee_account = self.env['account.account'].search([('name','ilike','Cheltuieli cu serviciile bancare'),('code','ilike','6270')],limit=1)
        interest_account =  self.env['account.account'].search([('name','ilike','Venituri din dobânzi'),('code','ilike','7660')],limit=1)
        for val in values:
            uniqueid = val['bank_tranzaction_uniqueid']
            this_date = val['date'].replace('-','')
#            if sequence_date > this_date:
                # raise error? but is working also iwth data in another order
            if this_date != sequence_date:
                index = 0
                sequence_date = this_date
            else:
                index +=1 
            val['sequence']=index #int(sequence_date+ str(index).zfill(3))

            desc = val['original_description'].lower()
            out = val['payment_type'] == 'outbound' 
            val['separated_description'] = desc.replace(';',"\n")
#            print(val['separated_description'] +"\n***************88")
            if out: # out transaction
                if ('comision procesare' in desc or 'taxa rapoarte tranzactii' in desc or 'ota contabila individuala' in desc or 'nota contabila individuala' in desc) : 
                    val['is_bank_fee'] = True
                    val['line_ids'] = [(0,0,{'account_id':fee_account.id,'debit':val['amount']}),(0,0,{'account_id':self.journal_id.default_account_id.id,'credit':val['amount']})]
                elif 'retragere de numerar'  in desc:
                    val['is_internal_transfer'] = True
                    val['transfer_journal_id'] = self.env['account.journal'].search([('type','=','cache')],limit=1)
            else: # are in transaction  + transactions
                if  'nota contabila individuala' in desc: 
                    val['is_bank_interest'] = True
                    val['move_id'] = [ (0,0, {'move_line_ids':
                        [(0,0,{'account_id':interest_account.id,'credit':val['amount'],'currency_id':self.journal_id.currency_id.id}),
                         (0,0,{'account_id':self.journal_id.default_account_id.id,'debit':val['amount'], 'currency_id':self.journal_id.currency_id.id})]
                        })]
            
            if uniqueid:
                same_payment = Payment.search([('bank_tranzaction_uniqueid','=',uniqueid),('state','!=','cancel')])
                if same_payment:
                    result['not_written_payments_ids'].append((same_payment,f'based on bank_tranzaction_uniqueid same_payent exist already registred as {same_payment}',val))
                    continue
# here I must search also the 
                try:
                    res = Payment.create(val)
                    result['written_payments_ids'].append((res,f'OK, created {res}',val))                    
                except Exception as ex:
                    result['error_payments_ids'].append((0,f'ERORR at create: {ex}',val))
                    
                
            else:
                raise UserError(f'The file does not look like transilvania csv export, because does not have bank_tranzaction_uniqueid')
        
        # post payments, reconcile them..    
        if self.post_this_payments:
            for res in result['written_payments_ids']:
                pass
                #res[1].action_post()
            for res in result['not_written_payments_ids']:
                if res[0].state == 'draft':
                    pass
#                    res[0].action_post()
        print(f"result['written_payments_ids']:{result['written_payments_ids']}")
        print(f"result['not_written_payments_ids']:{result['not_written_payments_ids']}")
        print(f"result['error_payments_ids']:{result['error_payments_ids']}")
        t1 = '\n'.join([str(x) for x in result['written_payments_ids']])
        t2 = '\n'.join([str(x) for x in result['not_written_payments_ids']])
        t3 = '\n'.join([str(x) for x in result['error_payments_ids']])
        return {'name':'some name',
                'view_type': 'form', 'view_mode': 'form',
                'res_model': "result.wizard",   'domain': [],  'context': {"default_text1":f"result['written_payments_ids']:\n{t1}",
                                                                           "default_text2":f"result['not_written_payments_ids']:{t2}",
                                                                            "default_text3":f"result['error_payments_ids']:{t3}",    }, 
                'type': 'ir.actions.act_window',  
                'target': 'new'
            
            }
        

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
