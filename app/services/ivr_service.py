"""Voice IVR handler — responds to incoming calls with member balance (Kiswahili)."""
from app.services.ussd_service import _get_member
from app.services.i18n import t


def handle_voice_call(phone):
    """Returns dict: {action, text, language} for the voice blueprint to speak."""
    member = _get_member(phone)
    if not member:
        return {"action": "play", "text": t("sw", "not_found"), "language": "sw"}
    lang = member.language_preference or "sw"
    text = t(lang, "balance", balance=float(member.savings_balance or 0))
    return {"action": "play", "text": text, "language": lang}
