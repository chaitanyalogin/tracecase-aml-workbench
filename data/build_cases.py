"""Reproducible fictional fixtures. No real people, accounts or documents."""
import json
from pathlib import Path

def tx(id,date,direction,amount,cp,purpose):
    return dict(id=id,date=date,direction=direction,amount_inr=amount,counterparty_id=cp,purpose=purpose,currency='INR')

def doc(id,title,text,status,transaction_ids=None):
    return dict(id=id,title=title,text=text,status=status,transaction_ids=transaction_ids or [])

cases=[]
for num,name,income in [(1,'Anita Rao',30000),(2,'Vikram Shah',40000)]:
    prefix=f'C{num:03}'
    transactions=[tx(f'{prefix}-T00{i}',f'2026-{m:02}-01T09:00:00','in',income,'EMPLOYER','salary') for i,m in enumerate([7,8,9,10],1)]
    transactions += [tx(f'{prefix}-T005','2026-10-03T12:00:00','out',12000,'LANDLORD','rent'),tx(f'{prefix}-T006','2026-10-07T17:30:00','out',2500,'GROCERY','groceries')]
    customer=dict(id=f'{prefix}-KYC',name=name,account_id=f'SYNTH-{num:04}',occupation='Salaried employee',expected_monthly_inr=income,relationship_since='2025-06-01',source_of_funds='Salary',review_note='Customer names and all associated records are fictional. Expected activity is a training assumption, not a legal threshold.')
    if num==1:
        transactions += [tx(f'{prefix}-T{10+i:03}','2026-10-15T10:00:00','in',120000,f'PAYER-{i:02}','transfer') for i in range(1,11)]
        transactions += [tx(f'{prefix}-T030','2026-10-16T09:00:00','out',570000,'RECIPIENT-A','transfer'),tx(f'{prefix}-T031','2026-10-16T11:00:00','out',570000,'RECIPIENT-B','transfer')]
        documents=[doc(f'{prefix}-D001','Customer statement','Customer says the transfers were collections for friends. The relationship to the ten payers and two recipients is not documented. No invoice, agreement or ownership evidence was provided. The statement is unverified.','Provided; unverified'),doc(f'{prefix}-D002','Review checks record','The synthetic internal record shows no prior case. No external sanctions, PEP or adverse-media screening has been performed. The absence of a screening result is not a clean result.','Synthetic internal record')]
    else:
        transactions += [tx(f'{prefix}-T011','2026-10-15T10:00:00','in',600000,'BUYER-A','transfer'),tx(f'{prefix}-T012','2026-10-15T10:30:00','in',600000,'BUYER-B','transfer'),tx(f'{prefix}-T030','2026-10-16T09:00:00','out',1140000,'MORTGAGE-LENDER','transfer')]
        documents=[doc(f'{prefix}-D001','Fictional property sale completion record','Synthetic case evidence: Vikram Shah is the seller. Recorded total sale proceeds are INR 1,200,000, payable by BUYER-A and BUYER-B in equal portions. The simulated verification log records confirmation of the transaction and parties from the conveyancer through independently recorded contact details. This is a fictional training assertion, not a real registry check.','Verified within fictional scenario',[f'{prefix}-T011',f'{prefix}-T012']),doc(f'{prefix}-D002','Fictional mortgage redemption statement','Synthetic case evidence: outstanding mortgage redemption amount INR 1,140,000, payable to MORTGAGE-LENDER. The fictional verification record confirms the beneficiary and obligation through the recorded lender contact.','Verified within fictional scenario',[f'{prefix}-T030']),doc(f'{prefix}-D003','Review checks record','In this synthetic scenario, completed screening and identity review records show no unresolved matches. No material conflict with the sale documents is recorded. This is fabricated training evidence, not live screening.','Verified within fictional scenario')]
    cases.append(dict(id=prefix,title=f'{name} | Non-routine credits',period_start='2026-10-01',period_end='2026-10-23',customer=customer,transactions=transactions,documents=documents))
Path(__file__).with_name('cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
