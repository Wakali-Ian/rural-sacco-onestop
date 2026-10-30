"""KRA eTIMS OSCU integration: device init, item save, sale signing."""
import json
import requests
from datetime import datetime
from app.models import db
from app.models.etims import EtimsConfig, EtimsReceipt
from app.models.transaction import Transaction


class EtimsError(Exception):
    pass


def _post(cfg, path, payload):
    url = cfg.base_url.rstrip("/") + path
    headers = {"Content-Type": "application/json"}
    if cfg.cmc_key:
        headers["CMCKey"] = cfg.cmc_key
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    try:
        data = r.json()
    except ValueError:
        raise EtimsError(f"Non-JSON response: {r.text[:200]}")
    if data.get("resultCd") not in ("000", "0", "00", "0000"):
        raise EtimsError(data.get("resultMsg") or f"KRA error {data.get('resultCd')}")
    return data


def initialize_device(pin, branch_id, device_serial, base_url=None):
    cfg = EtimsConfig.query.filter_by(kra_pin=pin).first() or EtimsConfig(kra_pin=pin)
    cfg.branch_id = branch_id
    cfg.device_serial = device_serial
    if base_url:
        cfg.base_url = base_url
    payload = {
        "tin": pin,
        "bhfId": branch_id,
        "dvcSrlNo": device_serial,
    }
    data = _post(cfg, "/selectInitOsdcInfo", payload)
    cfg.cmc_key = data["data"]["cmcKey"]
    cfg.last_initialized = datetime.utcnow()
    db.session.add(cfg)
    db.session.commit()
    return cfg


def save_item(cfg, item_code, item_name, unit_price, tax_type="B",
              item_class="8111180000"):
    payload = {
        "itemCd": item_code,
        "itemClsCd": item_class,
        "itemNm": item_name,
        "prc": float(unit_price),
        "qtyUnitCd": "U",
        "taxTyCd": tax_type,
        "dftPrc": float(unit_price),
    }
    return _post(cfg, "/saveItem", payload)


def build_invoice_payload(cfg, invoice_no, trader_invoice_no, amount,
                          description, buyer_pin=None):
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    item = {
        "itemCd": f"SACCO-{invoice_no}",
        "itemNm": description[:100],
        "prc": float(amount),
        "qty": 1,
        "qtyUnitCd": "U",
        "taxTyCd": "B",
        "itemClsCd": "8111180000",
    }
    return {
        "invcNo": invoice_no,
        "orgInvcNo": invoice_no,
        "trdInvcNo": trader_invoice_no,
        "tin": cfg.kra_pin,
        "bhfId": cfg.branch_id,
        "confirmDt": now,
        "custTin": buyer_pin or None,
        "custNm": "SACCO Member",
        "salesTyCd": "N",
        "rcptTyCd": "S",
        "pmtTyCd": "01",
        "itemList": [item],
    }


def sign_sale(cfg, transaction, description="SACCO deposit / savings"):
    existing = EtimsReceipt.query.filter_by(transaction_id=transaction.id).first()
    if existing:
        return existing
    invoice_no = f"SAC-{transaction.id:06d}"
    payload = build_invoice_payload(
        cfg, invoice_no, transaction.reference or invoice_no,
        float(transaction.amount), description,
    )
    data = _post(cfg, "/saveTrnsSalesOsdc", payload)
    info = data.get("data", {})
    receipt = EtimsReceipt(
        transaction_id=transaction.id,
        invoice_no=invoice_no,
        receipt_signature=info.get("receiptSignature"),
        qr_url=info.get("qrUrl"),
        control_unit_invoice_no=info.get("cuInvcNo"),
        raw_response=json.dumps(data),
        status="signed",
    )
    db.session.add(receipt)
    db.session.commit()
    return receipt


def sign_transaction(transaction_id, description=None):
    cfg = EtimsConfig.get_active()
    if not cfg or not cfg.cmc_key:
        raise EtimsError("eTIMS not configured or device not initialized")
    txn = Transaction.query.get(transaction_id)
    if not txn:
        raise EtimsError("Transaction not found")
    return sign_sale(cfg, txn, description or f"SACCO {txn.type}")
