import click
from app import create_app
from app.models import db

app = create_app()


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialised.")


@app.cli.command("seed")
@click.option("--reset", is_flag=True)
@click.option("--members", default=50)
def seed_cmd(reset, members):
    from scripts.seed import seed, reset as do_reset
    with app.app_context():
        db.create_all()
        if reset:
            do_reset()
            print("Existing data wiped.")
        stats = seed(n_members=members)
        for k, v in stats.items():
            print(f"  {k:>14}: {v}")


@app.cli.command("rescore")
def rescore_cmd():
    from app.services.credit_scoring import score_all_members
    from app.services.risk_engine import run_all_checks
    with app.app_context():
        scores = score_all_members()
        dist = {}
        for s in scores:
            dist[s["rank"]] = dist.get(s["rank"], 0) + 1
        print(f"Scored {len(scores)} members.")
        for rank in ["A", "B", "C", "D", "E"]:
            print(f"  Rank {rank}: {dist.get(rank, 0)}")
        risks = run_all_checks()
        print("Risk checks:")
        for k, v in risks.items():
            print(f"  {k:>20}: {v} open")


@app.cli.command("load-mpesa")
@click.option("--reset", is_flag=True, help="Clear M-Pesa table first")
@click.option("--count", default=40)
def load_mpesa_cmd(reset, count):
    from scripts.mpesa_mock import generate
    from app.models.mpesa import MpesaTransaction
    with app.app_context():
        if reset:
            db.session.query(MpesaTransaction).delete()
            db.session.commit()
            print("M-Pesa table cleared.")
        stats = generate(n=count)
        for k, v in stats.items():
            print(f"  {k:>14}: {v}")


@app.cli.command("reconcile")
def reconcile_cmd():
    from app.services.mpesa_matcher import reconcile_all, method_breakdown
    with app.app_context():
        result = reconcile_all()
        print("Reconciliation complete.")
        print(f"  Processed:  {result['total']}")
        print(f"  Matched:    {result['matched']}")
        print(f"  Unmatched:  {result['unmatched']}")
        if result["matched"] > 0:
            total = result["matched"] + result["unmatched"]
            rate = 100.0 * result["matched"] / total
            print(f"  Match rate: {rate:.1f}%")
        bd = method_breakdown()
        if bd:
            print("Breakdown by method:")
            for method, cnt in bd.items():
                print(f"  {method:>20}: {cnt}")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


@app.cli.command("sms-test")
@click.argument("phone")
@click.argument("message")
def sms_test_cmd(phone, message):
    """Send a test SMS (dev mode prints to console)."""
    from app.services.sms_service import send_sms
    with app.app_context():
        print(send_sms(phone, message))


@app.cli.command("demo")
def demo_cmd():
    """One-command demo reset: seed + M-Pesa + reconcile + rescore."""
    from scripts.seed import seed, reset as do_reset
    from scripts.mpesa_mock import generate
    from app.models.mpesa import MpesaTransaction
    from app.services.credit_scoring import score_all_members
    from app.services.risk_engine import run_all_checks
    from app.services.mpesa_matcher import reconcile_all
    with app.app_context():
        db.create_all()
        do_reset()
        db.session.query(MpesaTransaction).delete()
        db.session.commit()
        print("[1/4] Wiped existing data")
        stats = seed()
        print(f"[2/4] Seeded {stats['members']} members, "
              f"{stats['loans']} loans, {stats['transactions']} transactions")
        generate(n=40)
        r = reconcile_all()
        print(f"[3/4] M-Pesa reconciled: {r['matched']} matched, "
              f"{r['unmatched']} unmatched")
        score_all_members()
        run_all_checks()
        print("[4/4] Scored all members + ran risk checks")
        print("")
        print("DONE. Run `flask run`, open http://localhost:5000")
        print("Login: admin / admin123")


@app.cli.command("backup")
def backup_cmd():
    """Backup sacco.db to backups/ with a timestamp."""
    import shutil
    from datetime import datetime as dt
    from pathlib import Path
    src = Path("sacco.db")
    if not src.exists():
        print("No sacco.db found.")
        return
    Path("backups").mkdir(exist_ok=True)
    dst = Path("backups") / f"sacco_{dt.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy(src, dst)
    print(f"Backed up to {dst}")


@app.cli.command("rewards-recalc")
def rewards_recalc_cmd():
    """Recompute points, streaks, and tiers for all members."""
    from app.services.rewards_engine import recompute_all
    with app.app_context():
        result = recompute_all()
        print(f"Recomputed rewards for {result['processed']} members")


@app.cli.command("bonus-post")
@click.option("--year", type=int, required=True)
@click.option("--no-credit-savings", is_flag=True)
def bonus_post_cmd(year, no_credit_savings):
    """Post annual savings bonuses for the given year."""
    from app.services.rewards_engine import apply_annual_bonus
    with app.app_context():
        r = apply_annual_bonus(year, credit_to_savings=not no_credit_savings)
        print(f"Posted bonuses to {r['posted']} members, total KES {r['total_kes']:,.2f}")


@app.cli.command("etims-init")
@click.option("--pin", required=True)
@click.option("--branch", default="00")
@click.option("--device", required=True)
@click.option("--url", default=None)
def etims_init_cmd(pin, branch, device, url):
    """Initialize an eTIMS OSCU device and store the CMC key."""
    from app.services.etims_service import initialize_device
    with app.app_context():
        cfg = initialize_device(pin, branch, device, base_url=url)
        print(f"eTIMS device initialized for {cfg.kra_pin}. CMC key stored.")


@app.cli.command("etims-sync")
@click.option("--transaction-id", type=int, required=True)
@click.option("--description", default="SACCO transaction")
def etims_sync_cmd(transaction_id, description):
    """Sign a single SACCO transaction and store its eTIMS receipt."""
    from app.services.etims_service import sign_transaction, EtimsError
    with app.app_context():
        try:
            receipt = sign_transaction(transaction_id, description)
            print(f"Receipt {receipt.invoice_no}: {receipt.qr_url}")
        except EtimsError as e:
            print(f"eTIMS error: {e}")
