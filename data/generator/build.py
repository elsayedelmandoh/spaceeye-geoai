"""One build command: python -m oasis_datakit build  (or: make all)."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import time

import pandas as pd

from . import calendar as C
from . import citizen_ops as CO
from . import energy_water as EW
from . import mobility as M
from . import reference as R
from . import safety_buildings_env as SB
from . import waste as W
from .common import Ctx, load_config


def build_data(ctx: Ctx, verbose=True) -> Ctx:
    t0 = time.time()
    say = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    if ctx.data_dir.exists():
        shutil.rmtree(ctx.data_dir)
    C.build_calendar(ctx); C.write_calendar(ctx)
    R.build_reference(ctx); R.write_reference(ctx)
    say("reference ✓")
    M.traffic(ctx); M.parking(ctx); M.transit(ctx); say("mobility ✓")
    EW.electricity(ctx); _, sl_ep = EW.streetlights(ctx); say("energy ✓")
    EW.water_meters(ctx); EW.network_pressure(ctx); EW.water_quality(ctx); say("water ✓")
    W.bins_and_trips(ctx); say("waste ✓")
    inc = SB.incidents(ctx); SB.camera_status(ctx); say("public safety ✓")
    _, fails = SB.bms(ctx)
    blocks = [b for e in ctx.log if e["id"] == "DQ2" for b in e["blocks"]]
    SB.work_orders(ctx, sl_ep, fails, blocks); say("buildings ✓")
    SB.air_quality(ctx); SB.noise(ctx); say("environment ✓")
    sr = CO.service_requests(ctx); CO.gov_services(ctx); say("citizen services ✓")
    CO.ops_tickets(ctx, inc, sr, blocks); say("operations ✓")
    ctx.rowlog_df = pd.concat(ctx.rowlog, ignore_index=True) if ctx.rowlog else pd.DataFrame()
    say(f"data built in {time.time() - t0:.0f}s")
    return ctx


def checksums(ctx: Ctx) -> dict:
    out = {}
    for p in sorted(list(ctx.data_dir.glob("*.csv")) + list(ctx.ref_dir.glob("*"))):
        out[str(p.relative_to(ctx.root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="oasis_datakit")
    ap.add_argument("command", choices=["build", "data", "docs", "labs"], help="build = data + docs + Day 1 labs")
    ap.add_argument("--edition", default="lite", choices=["lite", "full"])
    a = ap.parse_args(argv)
    if a.edition == "full":
        raise SystemExit("The full edition (12 months, Parquet, H2 and H4) is Phase 2 and is not built yet.")
    cfg = load_config()
    ctx = Ctx(cfg, a.edition)
    build_data(ctx)
    if a.command in ("build", "docs"):
        from . import docs
        docs.write_all(ctx)
    if a.command in ("build", "labs"):
        from . import day1
        day1.write_all(ctx)
    if a.command == "build":
        from .validation import write_report  # noqa: F401  (already run inside docs)
    sums = checksums(ctx)
    (ctx.root / "data" / f"{a.edition}_checksums.sha256").write_text("".join(f"{v}  {k}\n" for k, v in sums.items()))
    print("checksums written")


if __name__ == "__main__":
    main()
