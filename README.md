# Rural SACCO OneStop Solutions

**A digital trust layer for rural SACCOs and Chamas in Kenya — built for any phone, any signal, any literacy level.**

> *"Your members will never again ask 'where is my money?' Your treasurer will never again spend a weekend reconciling M-Pesa."*

## The problem

Rural SACCOs run on paper passbooks, Excel, and WhatsApp. Members wait weeks for balances. Treasurers lose weekends matching M-Pesa SMS to passbooks. Loans are approved on friendship, not evidence. Existing software costs KES 12,000+/year, requires smartphones, and assumes English literacy — rural groups are priced out.

## The solution

- **USSD + IVR member channel** — any phone, no data, Kiswahili voice for illiterate members
- **M-Pesa auto-reconciliation** — 99% of deposits matched within 60 seconds
- **Trust Score + Default Rank (A–E)** — loans approved on evidence, not friendship
- **7 automated risk checks** — liquidity, concentration, default, guarantor exposure, aging, delinquency, fraud
- **One-screen colour-coded manager console** — green/red/amber reconciliation
- **Digital passbook + audit trail** — every transaction, every action, timestamped

## Tech stack

Python 3.8+ · Flask · SQLAlchemy · SQLite (offline-first) → PostgreSQL · M-Pesa Daraja API · Africa's Talking (USSD/SMS/IVR)

## Quick start

    pip install -r requirements.txt
    cp .env.example .env
    flask init-db
    flask seed --reset
    flask rescore
    flask run

Then open http://localhost:5000

## Roadmap

| Phase | What |
|---|---|
| 0 | Repo scaffold (this) |
| 1 | Core models, config, app factory |
| 2 | Trust Score + risk engine + seed data |
| 3 | M-Pesa reconciliation engine |
| 4 | USSD/SMS/IVR member channel |
| 5 | Manager console |
| 6 | Excel/PDF reports, SASRA templates |

## License

MIT — see [LICENSE](LICENSE).

**Built in Kenya, for Kenya.**
