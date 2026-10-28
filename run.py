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
