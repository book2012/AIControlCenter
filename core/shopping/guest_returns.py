"""Explicit physical return workflow; inventory restoration is separate from refund."""
import re,sqlite3

class ReturnWorkflow:
    def _return_case(self,case_id):
        if type(case_id) is not str or not re.fullmatch(r'[a-f0-9]{8}',case_id):raise ValueError('RETURN_CASE_REQUIRED')
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row
            row=c.execute("SELECT * FROM cases WHERE id=? AND kind='RETURN'",(case_id,)).fetchone()
        if row is None:raise ValueError('RETURN_CASE_REQUIRED')
        case=dict(row);order,draft=self._customer_order(case['customer'],case['order_id'])
        if order['review_state']!='CONFIRMED' or self._fulfillment(case['order_id'])['state']!='DELIVERED' or self.payment(case['order_id'])['state']!='PAID':
            raise ValueError('DELIVERED_PAID_RETURN_REQUIRED')
        return case,order,draft
    def return_status(self,order_id):
        with sqlite3.connect(self.path) as c:
            row=c.execute("SELECT id,state FROM cases WHERE order_id=? AND kind='RETURN' AND state NOT IN ('REQUESTED','REJECTED') ORDER BY created DESC LIMIT 1",(order_id,)).fetchone()
        return {'state':row[1] if row else 'NONE','case_id':row[0] if row else None}
    def receive_return(self,case_id):
        case,_,_=self._return_case(case_id)
        with sqlite3.connect(self.path) as c:
            c.execute('BEGIN IMMEDIATE')
            state=c.execute('SELECT state FROM cases WHERE id=?',(case_id,)).fetchone()[0]
            if state=='RETURN_APPROVED':
                c.execute("UPDATE cases SET state='RETURN_RECEIVED',updated=? WHERE id=?",(self.clock(),case_id))
            elif state not in ('RETURN_RECEIVED','RETURN_RESTOCK_PENDING','RETURN_RESTOCK_UNKNOWN','RETURN_RESTOCKED'):
                raise ValueError('RETURN_APPROVAL_REQUIRED')
        return self.return_status(case['order_id'])
    def _complete_return(self,case_id,receipt):
        case,_,_=self._return_case(case_id)
        if not receipt or receipt.get('outcome')!='STOCK_RETURNED' or receipt.get('order_id')!=case['order_id'] or receipt.get('case_id')!=case_id:
            raise ValueError('RETURN_RECONCILIATION_REQUIRED')
        with sqlite3.connect(self.path) as c:
            c.execute('BEGIN IMMEDIATE')
            operation=c.execute('SELECT state FROM return_stock_operations WHERE case_id=?',(case_id,)).fetchone()
            if not operation:raise ValueError('RETURN_RECONCILIATION_REQUIRED')
            if operation[0]!='RESTORED':
                stamp=self.clock()
                c.execute("UPDATE return_stock_operations SET state='RESTORED',updated=? WHERE case_id=?",(stamp,case_id))
                c.execute("UPDATE cases SET state='RETURN_RESTOCKED',updated=? WHERE id=?",(stamp,case_id))
        return self.return_status(case['order_id'])
    def inspect_return(self,case_id):
        case,row,draft=self._return_case(case_id)
        if self.stock_return is None:raise ValueError('RETURN_RESTORATION_NOT_CONFIGURED')
        with sqlite3.connect(self.path) as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT state FROM return_stock_operations WHERE case_id=?',(case_id,)).fetchone()
            if old:
                if old[0]=='RESTORED':return self.return_status(case['order_id'])
                raise ValueError('RETURN_RECONCILIATION_REQUIRED')
            current=c.execute('SELECT state FROM cases WHERE id=?',(case_id,)).fetchone()[0]
            if current!='RETURN_RECEIVED':raise ValueError('RETURN_RECEIPT_REQUIRED')
            if c.execute('SELECT 1 FROM return_stock_operations WHERE order_id=?',(case['order_id'],)).fetchone():raise ValueError('RETURN_ALREADY_RESTORED')
            self._deny_cancelled(c,case['order_id'])
            c.execute('INSERT INTO return_stock_operations VALUES(?,?,?,?)',(case_id,case['order_id'],'SENDING',self.clock()))
            c.execute("UPDATE cases SET state='RETURN_RESTOCK_PENDING',updated=? WHERE id=?",(self.clock(),case_id))
        try:
            receipt=self.stock_return(row,draft,case)
            return self._complete_return(case_id,receipt)
        except Exception:
            with sqlite3.connect(self.path) as c:
                c.execute("UPDATE return_stock_operations SET state='UNKNOWN',updated=? WHERE case_id=? AND state!='RESTORED'",(self.clock(),case_id))
                c.execute("UPDATE cases SET state='RETURN_RESTOCK_UNKNOWN',updated=? WHERE id=? AND state!='RETURN_RESTOCKED'",(self.clock(),case_id))
            raise ValueError('RETURN_RECONCILIATION_REQUIRED') from None
    def reconcile_return(self,case_id):
        case,row,draft=self._return_case(case_id)
        with sqlite3.connect(self.path) as c:
            op=c.execute('SELECT state FROM return_stock_operations WHERE case_id=?',(case_id,)).fetchone()
        if op and op[0]=='RESTORED':return self.return_status(case['order_id'])
        if not op or op[0] not in ('SENDING','UNKNOWN') or not hasattr(self.stock_return,'reconcile'):
            raise ValueError('RETURN_RECONCILIATION_REQUIRED')
        return self._complete_return(case_id,self.stock_return.reconcile(row,draft,case))
