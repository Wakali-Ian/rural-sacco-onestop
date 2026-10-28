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
@click.option("--reset", is_flag=True, help="Wipe existing business data first")
@click.option("--members", default=50, help="Number of members to generate")
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
