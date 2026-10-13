from core.shopping.sqlite_resource import connection
"""Immutable operator attestation of an already completed transfer; never transfers money."""
from decimal import Decimal,InvalidOperation
import re,sqlite3

class ManualRefundRecords:
    manual_refund_records_enabled=False
    def refund(self,order_id):
        with connection('file:'+str(self.path.resolve())+'?mode=ro',uri=True) as c:
            row=c.execute('SELECT amount,currency,recorded FROM manual_refunds WHERE order_id=?',(order_id,)).fetchone()
        return {'state':'RECORDED','amount':row[0],'currency':row[1],'recorded_at':row[2]} if row else {'state':'NOT_RECORDED'}

    def record_refund(self,case_id,amount,evidence,actor,update_id):
        if self.manual_refund_records_enabled is not True:raise ValueError('MANUAL_REFUND_DISABLED')
        if type(amount) is not int or not 1<=amount<=10000000:raise ValueError('REFUND_AMOUNT_INVALID')
        if type(evidence) is not str or not re.fullmatch(r'[가-힣A-Za-z0-9._-]{3,80}',evidence):raise ValueError('REFUND_EVIDENCE_REQUIRED')
        if type(actor) is not str or not re.fullmatch(r'telegram-user-[0-9]+',actor):raise ValueError('REFUND_ACTOR_REQUIRED')
        if type(update_id) is not int or not 0<=update_id<2**63-1:raise ValueError('REFUND_UPDATE_REQUIRED')
        case,_,draft=self._return_case(case_id)
        quote=draft['body']['quote']
        try:total=Decimal(quote['final_total'])
        except (InvalidOperation,TypeError,ValueError):raise ValueError('REFUND_AMOUNT_INVALID') from None
        if quote['currency']!='KRW' or not total.is_finite() or total!=amount:raise ValueError('FULL_REFUND_AMOUNT_REQUIRED')
        with connection(self.path) as c:
            c.execute('BEGIN IMMEDIATE')
            state=c.execute('SELECT state FROM cases WHERE id=?',(case_id,)).fetchone()[0]
            restoration=c.execute('SELECT state FROM return_stock_operations WHERE case_id=?',(case_id,)).fetchone()
            if state!='RETURN_RESTOCKED' or not restoration or restoration[0]!='RESTORED':raise ValueError('REFUND_INSPECTION_REQUIRED')
            old=c.execute('SELECT amount,evidence FROM manual_refunds WHERE case_id=?',(case_id,)).fetchone()
            if old:
                if old!=(str(amount),evidence):raise ValueError('REFUND_RECORD_CONFLICT')
            else:
                if c.execute('SELECT 1 FROM manual_refunds WHERE evidence=?',(evidence,)).fetchone():raise ValueError('REFUND_EVIDENCE_REUSED')
                c.execute('INSERT INTO manual_refunds VALUES(?,?,?,?,?,?,?,?)',(case_id,case['order_id'],str(amount),'KRW',evidence,actor,update_id,self.clock()))
        return self.refund(case['order_id'])
