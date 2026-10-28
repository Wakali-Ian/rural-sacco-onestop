"""Bilingual message templates for USSD, SMS, IVR."""
MESSAGES = {
    "en": {
        "welcome": "Rural SACCO\n1. Balance\n2. Mini-statement\n3. Deposit\n4. Loan request\n5. Repay loan",
        "balance": "Your balance is KES {balance:,.2f}. Thank you.",
        "stmt_header": "Last 3 transactions:",
        "stmt_line": "{date}: {type} KES {amount:,.2f}",
        "deposit_info": "Send money via M-Pesa Paybill {shortcode}, account number = your member number ({member_number}). You will receive an SMS receipt.",
        "loan_info": "Rank {rank} ({label}). You can borrow up to KES {max_loan:,.2f} at {rate:.0f}% for {term} months. Guarantors required: {guarantors}. Reply 1 to apply.",
        "loan_applied": "Loan request for KES {amount:,.2f} submitted. You will be contacted.",
        "repay_info": "Your loan outstanding is KES {outstanding:,.2f}. To repay, use M-Pesa Paybill {shortcode}, account = LOAN{loan_number}. You will receive an SMS receipt.",
        "no_loan": "You have no active loan. Good standing!",
        "blacklisted": "Your account is restricted. Please contact your SACCO office.",
        "invalid": "Invalid option. Please try again.",
        "not_found": "Your phone is not registered. Contact your SACCO office.",
        "sms_receipt": "Rural SACCO: {action} KES {amount:,.2f} received. Ref: {ref}. Balance: KES {balance:,.2f}.",
    },
    "sw": {
        "welcome": "Rural SACCO\n1. Salio\n2. Historia\n3. Weka pesa\n4. Ombi la mkopo\n5. Lipa mkopo",
        "balance": "Salio lako ni KES {balance:,.2f}. Asante.",
        "stmt_header": "Miamala 3 ya mwisho:",
        "stmt_line": "{date}: {type} KES {amount:,.2f}",
        "deposit_info": "Tuma pesa kwa M-Pesa Paybill {shortcode}, namba ya akaunti = namba yako ({member_number}). Utapokea SMS.",
        "loan_info": "Daraja {rank} ({label}). Unaweza kukopa hadi KES {max_loan:,.2f} kwa {rate:.0f}% kwa miezi {term}. Wahakikisho: {guarantors}. Jibu 1 kuomba.",
        "loan_applied": "Ombi la mkopo wa KES {amount:,.2f} limewasilishwa. Utawasiliana nasi.",
        "repay_info": "Deni la mkopo wako ni KES {outstanding:,.2f}. Kulipa, tumia M-Pesa Paybill {shortcode}, akaunti = LOAN{loan_number}. Utapokea SMS.",
        "no_loan": "Huna mkopo unaoendelea. Hongera!",
        "blacklisted": "Akaunti yako imezuiwa. Wasiliana na ofisi ya SACCO.",
        "invalid": "Chaguo si sahihi. Tafadhali jaribu tena.",
        "not_found": "Namba yako haijasajiliwa. Wasiliana na ofisi ya SACCO.",
        "sms_receipt": "Rural SACCO: {action} KES {amount:,.2f} imepokelewa. Kumbukumbu: {ref}. Salio: KES {balance:,.2f}.",
    },
}


def t(lang, key, **kwargs):
    lang = lang if lang in MESSAGES else "sw"
    template = MESSAGES[lang].get(key) or MESSAGES["sw"].get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        return template
