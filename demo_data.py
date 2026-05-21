import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_sample_data():
    """
    Generates realistic synthetic container movement data.
    Fixed random seed keeps structure consistent; dates are relative to today
    so the default 30-day sidebar filter always has data to display.
    """
    rng = np.random.default_rng(42)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    period_start = today - timedelta(days=90)

    # Three tiers: large mainline vessels, medium regional, small feeder.
    _vessel_tiers = {
        "MSC AURORA":    "large",
        "EVER FORTUNE":  "large",
        "MAERSK SATURN": "large",
        "OOCL PACIFIC":  "medium",
        "CMA MISTRAL":   "medium",
        "HMM OLYMPIA":   "medium",
        "ONE HARMONY":   "medium",
        "PIL NAVIGATOR": "small",
        "ANL WYONG":     "small",
        "COSCO STAR":    "small",
    }
    vessels = list(_vessel_tiers.keys())

    categories = ["IMPORT", "EXPORT", "TRANSHIP", "EMPTY"]
    cat_weights = np.array([0.45, 0.35, 0.12, 0.08])

    # (block, min_row, max_row, weight) — higher weight = more containers placed here
    _pool = [
        ("M",   1, 14, 3), ("L",  1, 20, 5), ("K",  1, 20, 5), ("J",  3, 20, 3),  # Berth 6
        ("J",   1,  2, 1), ("I",  1, 20, 4), ("H",  1, 20, 5), ("G",  1, 20, 4),   # Berth 7
        ("F",  15, 22, 2),
        ("F",   1, 14, 3), ("E",  1, 20, 4), ("D",  3, 20, 3),                     # Berth 8
        ("D",   1,  2, 1), ("C",  1, 20, 3), ("B",  2, 20, 2),                     # Berth 9
    ]
    _blks  = [x[0] for x in _pool]
    _mins  = [x[1] for x in _pool]
    _maxs  = [x[2] for x in _pool]
    _wts   = np.array([x[3] for x in _pool], dtype=float)
    _probs = _wts / _wts.sum()

    _specials = [
        ("RBJ", 1, 5), ("RBH", 1, 5),  # Rail Block
        ("RG1", 1, 3), ("RG2", 1, 3),  # ISA
        ("MX1", 1, 2),                  # Cargo Link
    ]

    def rand_yard():
        i = int(rng.choice(len(_blks), p=_probs))
        return _blks[i], str(int(rng.integers(_mins[i], _maxs[i] + 1)))

    def rand_special():
        i = int(rng.integers(0, len(_specials)))
        blk, mn, mx = _specials[i]
        return blk, str(int(rng.integers(mn, mx + 1)))

    def rand_ctr_no():
        pfx = rng.choice(["TEMU", "MSCU", "TCKU", "HLCU", "OOLU", "CCLU"])
        return f"{pfx}{int(rng.integers(1_000_000, 9_999_999))}"

    def rand_cat():
        return categories[int(rng.choice(len(categories), p=cat_weights))]

    rows = []
    ctr_key = 100001

    def add(k, no, vessel, cat, t, src, src_blk, src_row, tgt, tgt_blk, tgt_row):
        rows.append({
            "ctr_key":        k,
            "ctr_no":         no,
            "ship_id":        vessel,
            "cargo_category": cat,
            "time":           t,
            "source_raw":     src,
            "target_raw":     tgt,
            "pick_blk":       src_blk,
            "pick_y":         str(src_row) if src_row else "",
            "pick_x":         int(rng.integers(1, 9)),
            "pick_z":         int(rng.integers(1, 5)),
            "place_blk":      tgt_blk,
            "place_y":        str(tgt_row) if tgt_row else "",
            "place_x":        int(rng.integers(1, 9)),
            "place_z":        int(rng.integers(1, 5)),
        })

    for vessel in vessels:
        tier = _vessel_tiers[vessel]

        if tier == "large":
            n_calls            = int(rng.integers(2, 4))    # 2-3 calls
            dis_lo,  dis_hi   = 800,  1600
            load_lo, load_hi  = 500,  1100
            sp_lo,   sp_hi    = 20,   40
            churn_lo, churn_hi = 8,   16
        elif tier == "medium":
            n_calls            = int(rng.integers(1, 3))    # 1-2 calls
            dis_lo,  dis_hi   = 150,  420
            load_lo, load_hi  = 100,  300
            sp_lo,   sp_hi    = 10,   25
            churn_lo, churn_hi = 3,   8
        else:                                                # small feeder
            n_calls            = int(rng.integers(1, 3))    # 1-2 calls
            dis_lo,  dis_hi   = 40,   130
            load_lo, load_hi  = 25,   95
            sp_lo,   sp_hi    = 5,    15
            churn_lo, churn_hi = 1,   4

        for _ in range(n_calls):
            call_day = period_start + timedelta(days=int(rng.integers(0, 90)))

            # Discharge: Ship → Block → [optional re-handle] → [X-ray] → Truck/Rail
            for _ in range(int(rng.integers(dis_lo, dis_hi + 1))):
                k = ctr_key; ctr_key += 1
                no = rand_ctr_no(); cat = rand_cat()
                blk1, row1 = rand_yard()
                t0 = call_day + timedelta(hours=float(rng.uniform(0, 8)))

                add(k, no, vessel, cat, t0,
                    "Ship", "", "", f"Block {blk1}", blk1, row1)

                if rng.random() < 0.22:
                    blk2, row2 = rand_yard()
                    t1 = t0 + timedelta(hours=float(rng.uniform(6, 24)))
                    add(k, no, vessel, cat, t1,
                        f"Block {blk1}", blk1, row1,
                        f"Block {blk2}", blk2, row2)
                    blk_f, row_f = blk2, row2
                    t_gate = t1 + timedelta(hours=float(rng.uniform(24, 60)))
                else:
                    blk_f, row_f = blk1, row1
                    t_gate = t0 + timedelta(hours=float(rng.uniform(18, 72)))

                # ~1% of discharge containers are sent out for X-ray scanning,
                # then returned to a yard block before final gate-out.
                # Produces the consecutive target_raw='Truck'/source_raw='Truck' pattern
                # that the X-Ray Trips analytics section detects.
                if rng.random() < 0.01:
                    blk_xr, row_xr = rand_yard()
                    t_xr_out = t_gate
                    t_xr_in  = t_xr_out + timedelta(hours=float(rng.uniform(2, 8)))
                    t_gate   = t_xr_in  + timedelta(hours=float(rng.uniform(6, 24)))
                    add(k, no, vessel, cat, t_xr_out,
                        f"Block {blk_f}", blk_f, row_f, "Truck", "", "")
                    add(k, no, vessel, cat, t_xr_in,
                        "Truck", "", "", f"Block {blk_xr}", blk_xr, row_xr)
                    blk_f, row_f = blk_xr, row_xr

                gate = "Truck" if rng.random() < 0.72 else "Rail"
                add(k, no, vessel, cat, t_gate,
                    f"Block {blk_f}", blk_f, row_f, gate, "", "")

            # Load: Truck/Rail → Block → [optional re-handle] → Ship
            for _ in range(int(rng.integers(load_lo, load_hi + 1))):
                k = ctr_key; ctr_key += 1
                no = rand_ctr_no(); cat = rand_cat()
                blk1, row1 = rand_yard()
                gate = "Truck" if rng.random() < 0.72 else "Rail"
                t0 = call_day - timedelta(hours=float(rng.uniform(24, 72)))

                add(k, no, vessel, cat, t0,
                    gate, "", "", f"Block {blk1}", blk1, row1)

                if rng.random() < 0.15:
                    blk2, row2 = rand_yard()
                    t1 = t0 + timedelta(hours=float(rng.uniform(6, 20)))
                    add(k, no, vessel, cat, t1,
                        f"Block {blk1}", blk1, row1,
                        f"Block {blk2}", blk2, row2)
                    blk_f, row_f = blk2, row2
                    t_ship = call_day + timedelta(hours=float(rng.uniform(0, 6)))
                else:
                    blk_f, row_f = blk1, row1
                    t_ship = call_day + timedelta(hours=float(rng.uniform(0, 8)))

                add(k, no, vessel, cat, t_ship,
                    f"Block {blk_f}", blk_f, row_f, "Ship", "", "")

            # Special-block flows (ISA, Rail Block, Cargo Link)
            for _ in range(int(rng.integers(sp_lo, sp_hi + 1))):
                k = ctr_key; ctr_key += 1
                no = rand_ctr_no(); cat = rand_cat()
                sp_blk, sp_row = rand_special()
                blk1, row1 = rand_yard()
                t0 = call_day + timedelta(hours=float(rng.uniform(0, 12)))
                t1 = t0 + timedelta(hours=float(rng.uniform(6, 36)))
                t2 = t1 + timedelta(hours=float(rng.uniform(12, 48)))

                if rng.random() < 0.5:
                    # Discharge → yard → special staging → gate
                    add(k, no, vessel, cat, t0,
                        "Ship", "", "", f"Block {blk1}", blk1, row1)
                    add(k, no, vessel, cat, t1,
                        f"Block {blk1}", blk1, row1,
                        f"Block {sp_blk}", sp_blk, sp_row)
                    gate = "Truck" if rng.random() < 0.6 else "Rail"
                    add(k, no, vessel, cat, t2,
                        f"Block {sp_blk}", sp_blk, sp_row, gate, "", "")
                else:
                    # Gate → special staging → yard → ship
                    gate = "Truck" if rng.random() < 0.6 else "Rail"
                    add(k, no, vessel, cat, t0,
                        gate, "", "", f"Block {sp_blk}", sp_blk, sp_row)
                    add(k, no, vessel, cat, t1,
                        f"Block {sp_blk}", sp_blk, sp_row,
                        f"Block {blk1}", blk1, row1)
                    add(k, no, vessel, cat, t2,
                        f"Block {blk1}", blk1, row1, "Ship", "", "")

            # Multi-step churning containers (customs holds, wrong-bay restacks, strip/stuff).
            # Each container is re-handled 11–16 times block-to-block, producing journey chains
            # of 13–18 steps in the Sankey — the "boxes that move many times" visible at the right
            # tail of the step-sequence cards.
            for _ in range(int(rng.integers(churn_lo, churn_hi + 1))):
                k = ctr_key; ctr_key += 1
                no = rand_ctr_no(); cat = rand_cat()
                n_rehandles = int(rng.integers(11, 17))
                blk, row = rand_yard()
                t = call_day + timedelta(hours=float(rng.uniform(0, 6)))

                add(k, no, vessel, cat, t, "Ship", "", "", f"Block {blk}", blk, row)
                for _ in range(n_rehandles):
                    blk2, row2 = rand_yard()
                    t = t + timedelta(hours=float(rng.uniform(3, 20)))
                    add(k, no, vessel, cat, t,
                        f"Block {blk}", blk, row,
                        f"Block {blk2}", blk2, row2)
                    blk, row = blk2, row2
                t += timedelta(hours=float(rng.uniform(6, 24)))
                gate = "Truck" if rng.random() < 0.72 else "Rail"
                add(k, no, vessel, cat, t, f"Block {blk}", blk, row, gate, "", "")

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"])
    return df
