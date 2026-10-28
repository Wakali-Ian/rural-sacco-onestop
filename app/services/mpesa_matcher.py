"""Match raw M-Pesa transactions to members and post deposits as Transactions."""
from datetime import datetime, timedelta
from app.models import db
from app.models.member import Member
from app.models.mpesa import MpesaTransaction
from app.models.transaction import Transaction


def _normalize_phone(p):
    """Normalize KE phone numbers to 0XXXXXXXXX (10 digits).

    Handles: +254712345678, 254712345678, 0712345678, 712345678
    """
    if not p:
        return ""
    d = "".join(c for c in str(p) if c.isdigit())
    if d.startswith("254") and len(d) >= 12:
        d = d[3:12]
    if len(d) == 9:
        return "0" + d
    if len(d) == 10 and d.startswith("0"):
        return d
    return d


def _match_by_account_ref(m):
    if not m.account_ref:
        return None
    member = Member.query.filter_by(member_number=m.account_ref).first()
    if member:
        return member, 1.0, "account_ref"
    return None


def _match_by_phone(m):
    if not m.msisdn:
        return None
    target = _normalize_phone(m.msisdn)
    if not target:
        return None
    for member in Member.query.all():
        if _normalize_phone(member.phone) == target:
            return member, 0.95, "phone_exact"
    return None


def _match_by_name_amount_time(m):
    if not m.first_name or not m.trans_time:
        return None
    window = timedelta(hours=2)
    amount = float(m.amount or 0)
    for member in Member.query.all():
        first = (member.full_name or "").split()[0].lower()
        if first != m.first_name.lower():
            continue
        recent = (Transaction.query
                  .filter(Transaction.member_id == member.id,
                          Transaction.type == "deposit",
                          Transaction.created_at >= m.trans_time - window,
                          Transaction.created_at <= m.trans_time + window)
                  .first())
        if recent and abs(float(recent.amount) - amount) < 1.0:
            return member, 0.70, "name_amount_time"
    return None


STRATEGIES = (_match_by_account_ref, _match_by_phone, _match_by_name_amount_time)


def match_one(m):
    for fn in STRATEGIES:
        result = fn(m)
        if result:
            return result
    return None


def apply_match(m, member, confidence, method):
    txn = Transaction(
        member_id=member.id, type="deposit", amount=m.amount,
        mpesa_ref=m.trans_id, reference=f"MPS-{m.trans_id}",
        channel="mpesa", status="completed", created_by="mpesa",
        created_at=m.trans_time or datetime.utcnow(),
    )
    db.session.add(txn)
    db.session.flush()
    member.savings_balance = float(member.savings_balance or 0) + float(m.amount)
    txn.balance_after = member.savings_balance
    m.matched_transaction_id = txn.id
    m.matched_at = datetime.utcnow()
    m.match_method = method
    m.match_confidence = confidence
    m.status = "matched"
    return txn


def reconcile_all():
    pending = MpesaTransaction.query.filter_by(status="unmatched").all()
    matched = 0
    unmatched = 0
    for m in pending:
        result = match_one(m)
        if result:
            member, conf, method = result
            apply_match(m, member, conf, method)
            matched += 1
        else:
            unmatched += 1
    db.session.commit()
    return {"matched": matched, "unmatched": unmatched, "total": len(pending)}


def method_breakdown():
    rows = (db.session.query(MpesaTransaction.match_method,
                             db.func.count(MpesaTransaction.id))
            .filter(MpesaTransaction.status == "matched")
            .group_by(MpesaTransaction.match_method).all())
    return {method or "unknown": count for method, count in rows}
