"""Seed the DB with realistic fictional data for demo / testing."""
import random
from datetime import date, datetime, timedelta
from app.models import db
from app.models.member import Member
from app.models.transaction import Transaction
from app.models.loan import Loan, LoanRepayment
from app.models.guarantor import Guarantor
from app.models.meeting import Meeting, MeetingAttendance
from app.models.risk import RiskEvent
from app.models.audit import AuditLog
from app.models.user import User


FIRST = ["John","Mary","Peter","Grace","Daniel","Faith","Samuel","Esther",
         "Michael","Anne","David","Jane","James","Mercy","Paul","Rose",
         "George","Lucy","Patrick","Naomi","Charles","Hannah","Joseph",
         "Ruth","Francis","Sarah","Ezekiel","Beatrice","Simon","Alice"]
LAST  = ["Kamau","Wanjiku","Otieno","Achieng","Mwangi","Njoroge","Kiptoo",
         "Chebet","Odhiambo","Akinyi","Mutua","Kilonzo","Waweru","Muthoni",
         "Barasa","Nekesa","Kipchoge","Jepkosgei","Njeri","Wambui"]


def _rand_phone():
    return f"+2547{random.randint(10_000_000, 99_999_999)}"


def _ensure_user(username, password, role):
    u = User.query.filter_by(username=username).first()
    if u:
        return u
    u = User(username=username, role=role)
    u.set_password(password)
    db.session.add(u)
    return u


def reset():
    for model in [Transaction, LoanRepayment, Guarantor, Loan,
                  MeetingAttendance, Meeting, RiskEvent, AuditLog, Member]:
        db.session.query(model).delete()
    db.session.commit()


def seed(n_members=50, n_months=12, seed_value=42):
    random.seed(seed_value)
    _ensure_user("admin", "admin123", "admin")
    _ensure_user("treasurer", "treasurer123", "treasurer")
    _ensure_user("chairman", "chairman123", "chairman")
    db.session.commit()

    today = date.today()
    members = []
    for i in range(n_members):
        join_days = random.choice([30, 90, 180, 365, 500, 730, 900, 1200])
        m = Member(
            member_number=f"RSC-{1000 + i:04d}",
            full_name=f"{random.choice(FIRST)} {random.choice(LAST)}",
            phone=_rand_phone(),
            join_date=today - timedelta(days=join_days + random.randint(0, 30)),
            status="active",
            shares=random.choice([0, 10, 25, 50, 100]),
            language_preference=random.choice(["sw", "sw", "sw", "en"]),
            consent_given=True,
            trust_score=50.0,
            default_rank="C",
        )
        db.session.add(m)
        members.append(m)
    db.session.commit()

    # 3. Savings transactions
    for m in members:
        n_deposits = random.choice([0, 1, 2, 3, 6, 9, 12, 12, 12])
        balance = 0.0
        for k in range(n_deposits):
            days_ago = random.randint(5, n_months * 30)
            amt = random.choice([200, 500, 500, 1000, 1000, 2000, 3000])
            balance += amt
            db.session.add(Transaction(
                member_id=m.id, type="deposit", amount=amt,
                balance_after=balance, channel=random.choice(["mpesa", "manual"]),
                reference=f"TXN-{m.id}-D{k}",
                mpesa_ref=f"QK{random.randint(10**8, 10**9)}",
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                created_by="seed",
            ))
            if random.random() < 0.4 and balance > amt:
                wd = random.choice([100, 200, 500])
                balance -= wd
                db.session.add(Transaction(
                    member_id=m.id, type="withdrawal", amount=wd,
                    balance_after=balance, channel="manual",
                    reference=f"TXN-{m.id}-W{k}",
                    created_at=datetime.utcnow() - timedelta(days=days_ago - 1),
                    created_by="seed",
                ))
        m.savings_balance = balance
    db.session.commit()

    # 4. Meetings + attendance
    meetings = []
    for i in range(12):
        mt = Meeting(
            meeting_date=today - timedelta(days=30 * i + random.randint(0, 5)),
            agenda="Monthly savings review",
            created_by="seed",
        )
        db.session.add(mt)
        meetings.append(mt)
    db.session.commit()
    for mt in meetings:
        for m in members:
            p = 0.85 if random.random() < 0.8 else 0.35
            status = "present" if random.random() < p else "absent"
            db.session.add(MeetingAttendance(meeting_id=mt.id,
                                             member_id=m.id, status=status))
    db.session.commit()

    # 5. Loans + repayments
    loans = []
    for m in members:
        if random.random() > 0.7:
            continue
        behaviour = random.choices(
            ["good", "overdue", "defaulted"],
            weights=[0.70, 0.20, 0.10], k=1)[0]
        savings = float(m.savings_balance or 0)
        if savings < 500:
            continue
        principal = round(savings * random.uniform(0.8, 2.5), -2)
        term = random.choice([6, 12, 18, 24])
        interest = random.choice([10.0, 12.0, 14.0, 18.0])
        start = today - timedelta(days=random.randint(30, 300))
        if behaviour == "good":
            status = "repaid"
            due = start + timedelta(days=term * 30)
            outstanding = 0.0
        elif behaviour == "overdue":
            status = "active"
            due = today - timedelta(days=random.choice([10, 35, 70]))
            outstanding = principal * random.uniform(0.3, 0.8)
        else:
            status = "defaulted"
            due = today - timedelta(days=random.choice([120, 180, 240]))
            outstanding = principal * random.uniform(0.7, 1.0)
        loan = Loan(
            loan_number=f"LN-{m.id:04d}-{len(loans)+1:03d}",
            member_id=m.id, principal=principal,
            interest_rate=interest, interest_method="flat",
            term_months=term, purpose="Business / school fees",
            status=status, disbursement_date=start, due_date=due,
            outstanding_balance=round(outstanding, 2),
            approved_by="chairman",
        )
        db.session.add(loan)
        loans.append((loan, behaviour, start, term))
    db.session.commit()

    # Repayments
    for loan, behaviour, start, term in loans:
        if behaviour == "good":
            for k in range(term):
                db.session.add(LoanRepayment(
                    loan_id=loan.id, amount=float(loan.principal) / term,
                    principal_portion=float(loan.principal) / term,
                    status="completed",
                    payment_date=datetime.combine(
                        start + timedelta(days=30 * (k + 1)), datetime.min.time()),
                ))
        elif behaviour == "overdue":
            for k in range(random.randint(1, 3)):
                db.session.add(LoanRepayment(
                    loan_id=loan.id, amount=float(loan.principal) * 0.2,
                    principal_portion=float(loan.principal) * 0.2,
                    status="completed",
                    payment_date=datetime.combine(
                        start + timedelta(days=30 * (k + 1)), datetime.min.time()),
                ))
    db.session.commit()

    # 6. Guarantors
    for loan, behaviour, _, _ in loans:
        n_guar = random.randint(1, 2)
        candidates = [m for m in members if m.id != loan.member_id]
        random.shuffle(candidates)
        for g_member in candidates[:n_guar]:
            db.session.add(Guarantor(
                loan_id=loan.id,
                guarantor_member_id=g_member.id,
                amount_guaranteed=float(loan.principal) / n_guar,
                status="active",
            ))
    db.session.commit()

    return {
        "members": len(members),
        "transactions": Transaction.query.count(),
        "loans": Loan.query.count(),
        "repayments": LoanRepayment.query.count(),
        "guarantors": Guarantor.query.count(),
        "meetings": Meeting.query.count(),
        "attendance": MeetingAttendance.query.count(),
    }
