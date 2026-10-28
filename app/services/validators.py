"""Form validators for member create/edit."""
import re
from datetime import datetime, date


KE_PHONE_RE = re.compile(r"^0[17]\d{8}$")
NAME_RE = re.compile(r"^[A-Za-z\s'\-\.]{2,120}$")


def normalize_phone(p):
    """Return 0XXXXXXXXX or '' if invalid."""
    d = re.sub(r"\D", "", str(p or ""))
    if d.startswith("254") and len(d) == 12:
        d = "0" + d[3:]
    elif len(d) == 9 and d[0] in "71":
        d = "0" + d
    return d


def next_member_number():
    from app.models.member import Member
    last = Member.query.order_by(Member.id.desc()).first()
    if not last:
        return "RSC-1000"
    m = re.search(r"(\d+)$", last.member_number or "")
    n = int(m.group(1)) + 1 if m else 1000
    return f"RSC-{n:04d}"


def validate_member_form(data, member_id=None):
    """Return (errors dict, cleaned dict). errors empty = valid."""
    from app.models.member import Member
    errors, cleaned = {}, {}

    name = (data.get("full_name") or "").strip()
    if not name:
        errors["full_name"] = "Full name is required"
    elif not NAME_RE.match(name):
        errors["full_name"] = "Only letters, spaces, hyphens, apostrophes (2-120 chars)"
    else:
        cleaned["full_name"] = name

    raw = (data.get("phone") or "").strip()
    phone = normalize_phone(raw)
    if not raw:
        errors["phone"] = "Phone is required"
    elif not KE_PHONE_RE.match(phone):
        errors["phone"] = "Valid Kenyan phone, e.g. 0712345678 or +254712345678"
    else:
        clash = Member.query.filter_by(phone=phone).first()
        if clash and clash.id != member_id:
            errors["phone"] = "Phone already registered"
        else:
            cleaned["phone"] = phone

    mnum = (data.get("member_number") or "").strip().upper()
    if not mnum:
        errors["member_number"] = "Member number is required"
    elif not re.match(r"^RSC-\d{3,6}$", mnum):
        errors["member_number"] = "Format: RSC-1234"
    else:
        clash = Member.query.filter_by(member_number=mnum).first()
        if clash and clash.id != member_id:
            errors["member_number"] = "Member number already exists"
        else:
            cleaned["member_number"] = mnum

    nid = (data.get("national_id") or "").strip()
    if nid:
        if not nid.isdigit():
            errors["national_id"] = "National ID must be digits only"
        elif len(nid) < 6 or len(nid) > 10:
            errors["national_id"] = "6-10 digits"
        else:
            clash = Member.query.filter_by(national_id=nid).first()
            if clash and clash.id != member_id:
                errors["national_id"] = "National ID already registered"
            else:
                cleaned["national_id"] = nid
    else:
        cleaned["national_id"] = None

    jd = (data.get("join_date") or "").strip()
    if not jd:
        errors["join_date"] = "Join date is required"
    else:
        try:
            parsed = datetime.strptime(jd, "%Y-%m-%d").date()
            if parsed > date.today():
                errors["join_date"] = "Cannot be in the future"
            else:
                cleaned["join_date"] = parsed
        except ValueError:
            errors["join_date"] = "Invalid date (YYYY-MM-DD)"

    try:
        shares = int((data.get("shares") or "0").strip())
        if shares < 0 or shares > 100000:
            errors["shares"] = "Between 0 and 100,000"
        else:
            cleaned["shares"] = shares
    except ValueError:
        errors["shares"] = "Whole number required"

    lang = (data.get("language_preference") or "sw").strip()
    if lang not in ("sw", "en"):
        errors["language_preference"] = "Pick Swahili or English"
    else:
        cleaned["language_preference"] = lang

    cleaned["consent_given"] = data.get("consent_given") in ("on", "true", "1", "yes")

    return errors, cleaned
