"""Generate mock M-Pesa transactions for demo without Daraja credentials.

Strategies (weighted):
  account_ref  (30%) - phone is wrong, but account_ref = member_number
  phone_exact  (40%) - matches member phone exactly
  phone_last9  (15%) - 9-digit form, tests normalization
  orphan       (10%) - unknown phone, will show as unmatched (red)
  dup           (5%) - duplicate trans_id, should be deduped
"""
import random
from datetime import datetime, timedelta
from app.models import db
from app.models.member import Member
from app.models.mpesa import MpesaTransaction


def generate(n=40, seed_value=7):
    random.seed(seed_value)
    members = Member.query.all()
    if not members:
        return {"created": 0, "reason": "no members - run flask seed first"}

    created = 0
    for _ in range(n):
        strategy = random.choices(
            ["account_ref", "phone_exact", "phone_last9", "orphan", "dup"],
            weights=[0.30, 0.40, 0.15, 0.10, 0.05], k=1,
        )[0]
        member = random.choice(members)
        amount = random.choice([100, 200, 500, 500, 1000, 1000, 2000, 3000])
        when = datetime.utcnow() - timedelta(hours=random.randint(1, 72))

        if strategy == "account_ref":
            ref, phone, fname = member.member_number, "+254700000000", ""
        elif strategy == "phone_exact":
            ref, phone, fname = "", member.phone, ""
        elif strategy == "phone_last9":
            ref, phone, fname = "", "".join(c for c in member.phone if c.isdigit())[-9:], ""
        elif strategy == "orphan":
            ref = ""
            phone = f"+2547{random.randint(10_000_000, 99_999_999)}"
            fname = ""
        else:
            ref, phone = "DUP", member.phone
            fname = member.full_name.split()[0]

        tid = f"QK{random.randint(10**8, 10**9)}"
        if MpesaTransaction.query.filter_by(trans_id=tid).first():
            continue

        db.session.add(MpesaTransaction(
            trans_id=tid, trans_time=when, amount=amount,
            msisdn=phone, first_name=fname, account_ref=ref,
            status="unmatched", raw_json="{}",
        ))
        created += 1
    db.session.commit()
    return {
        "created": created,
        "total_mpesa": MpesaTransaction.query.count(),
        "unmatched": MpesaTransaction.query.filter_by(status="unmatched").count(),
    }
