"""USSD menu state machine. Drives the *XXX# member channel."""
import os
from app.models import db
from app.models.member import Member
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.services.credit_scoring import rank_from_score
from app.services.i18n import t


def _normalize_phone(p):
    d = "".join(c for c in str(p or "") if c.isdigit())
    if d.startswith("254") and len(d) >= 12:
        d = "0" + d[3:12]
    elif len(d) == 9:
        d = "0" + d
    return d


def _get_member(phone):
    d = _normalize_phone(phone)
    if not d or len(d) < 9:
        return None
    return Member.query.filter(Member.phone.like(f"%{d[-9:]}")).first()


def handle_ussd(phone, text):
    """Main USSD handler. Returns 'CON ...' or 'END ...'."""
    member = _get_member(phone)
    lang = member.language_preference if member else "sw"

    if not member:
        return f"END {t(lang, 'not_found')}"

    steps = [s for s in (text or "").split("*") if s != ""]

    if not steps:
        return f"CON {t(lang, 'welcome')}"

    choice = steps[0]
    if choice == "1":
        return f"END {_balance(member, lang)}"
    if choice == "2":
        return f"END {_mini_statement(member, lang)}"
    if choice == "3":
        return f"END {_deposit_info(member, lang)}"
    if choice == "4":
        return _loan_menu(member, lang, steps[1:])
    if choice == "5":
        return f"END {_repay_info(member, lang)}"

    return f"END {t(lang, 'invalid')}"


def _balance(member, lang):
    return t(lang, "balance", balance=float(member.savings_balance or 0))


def _mini_statement(member, lang):
    txns = (Transaction.query
            .filter_by(member_id=member.id)
            .order_by(Transaction.created_at.desc()).limit(3).all())
    if not txns:
        return t(lang, "stmt_header") + "\n(no transactions)"
    lines = [t(lang, "stmt_header")]
    for tx in txns:
        lines.append(t(lang, "stmt_line",
                       date=tx.created_at.strftime("%d/%m"),
                       type=tx.type,
                       amount=float(tx.amount)))
    return "\n".join(lines)


def _deposit_info(member, lang):
    return t(lang, "deposit_info",
             shortcode=os.getenv("MPESA_SHORTCODE", "174379"),
             member_number=member.member_number)


def _repay_info(member, lang):
    active = (Loan.query
              .filter(Loan.member_id == member.id,
                      Loan.status.in_(["active", "disbursed", "overdue"]))
              .first())
    if not active:
        return t(lang, "no_loan")
    return t(lang, "repay_info",
             outstanding=float(active.outstanding_balance or 0),
             shortcode=os.getenv("MPESA_SHORTCODE", "174379"),
             loan_number=active.loan_number)


def _loan_menu(member, lang, sub_steps):
    meta = rank_from_score(member.trust_score or 0)
    if meta["rank"] == "E":
        return f"END {t(lang, 'blacklisted')}"

    active = (Loan.query
              .filter(Loan.member_id == member.id,
                      Loan.status.in_(["active", "disbursed", "overdue"]))
              .first())
    if active:
        return f"END {_repay_info(member, lang)}"

    savings = float(member.savings_balance or 0)
    max_loan = savings * meta["max_loan_multiplier"]

    if not sub_steps:
        info = t(lang, "loan_info",
                 rank=meta["rank"], label=meta["label"],
                 max_loan=max_loan, rate=meta["interest_rate"],
                 term=meta["max_term_months"],
                 guarantors=meta["guarantors_required"])
        return f"CON {info}"

    if sub_steps[0] == "1":
        return f"END {t(lang, 'loan_applied', amount=max_loan)}"

    return f"END {t(lang, 'invalid')}"
