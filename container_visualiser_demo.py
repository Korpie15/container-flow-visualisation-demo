import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from collections import defaultdict
from demo_data import generate_sample_data

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Port Container Flow Visualiser")
st.write("Analyse container movements through the terminal using this interactive dashboard.")

st.info("Demo Mode — all data shown is synthetic sample data. No real company or operational information is used.", icon="ℹ️")

# Colour key
st.markdown("""
<div style="background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #31333f; margin-bottom: 25px;">
    <div style="font-size: 0.75em; font-weight: bold; color: #a3a8b4; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px;">Yard Blocks</div>
    <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 14px;">
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #17a2b8; padding-left: 10px;">
            <strong style="color: #17a2b8;">Berth 6</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks K, L, M (all rows)<br>Block J (rows 3+) · Block M (rows 1–14)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #28a745; padding-left: 10px;">
            <strong style="color: #28a745;">Berth 7</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks G, H, I (all rows)<br>Block J (rows 1–2) · Block F (rows 15+)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #ffc107; padding-left: 10px;">
            <strong style="color: #ffc107;">Berth 8</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Block E (all rows)<br>Block F (rows 1–14) · Block D (rows 3+)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #dc3545; padding-left: 10px;">
            <strong style="color: #dc3545;">Berth 9</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Block C (all rows)<br>Block D (rows 1–2) · Block B (rows 2+)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #fd7e14; padding-left: 10px;">
            <strong style="color: #fd7e14;">Rail Block</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks RB· (rail-side storage)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #d63384; padding-left: 10px;">
            <strong style="color: #d63384;">ISA</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks RG· (intermodal staging area)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #20c997; padding-left: 10px;">
            <strong style="color: #20c997;">Cargo Link</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks MX1, MX2</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #6c757d; padding-left: 10px;">
            <strong style="color: #6c757d;">RE</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks RE· (reefer plug area)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #0dcaf0; padding-left: 10px;">
            <strong style="color: #0dcaf0;">RW</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Blocks RW· (west rail area)</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #ff7f50; padding-left: 10px;">
            <strong style="color: #ff7f50;">Pondus</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Block P, x=6, y=2–3</span>
        </div>
    </div>
    <div style="font-size: 0.75em; font-weight: bold; color: #a3a8b4; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px;">Transport Modes</div>
    <div style="display: flex; flex-wrap: wrap; gap: 12px;">
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #007bff; padding-left: 10px;">
            <strong style="color: #007bff;">Ship</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Vessel seaside operations</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #fd7e14; padding-left: 10px;">
            <strong style="color: #fd7e14;">Rail</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Rail interchange movements</span>
        </div>
        <div style="flex: 1; min-width: 160px; border-left: 5px solid #6f42c1; padding-left: 10px;">
            <strong style="color: #6f42c1;">Truck</strong><br>
            <span style="font-size: 0.8em; color: #a3a8b4;">Truck gate pick-up / delivery</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load demo data (cached — generates once per session)
# ---------------------------------------------------------------------------
@st.cache_data
def _load_demo_data():
    return generate_sample_data()

# ---------------------------------------------------------------------------
# Sidebar Filter Controls
# ---------------------------------------------------------------------------
st.sidebar.header("Filter Controls")

today         = datetime.date.today()
default_start = today - datetime.timedelta(days=30)
selected_date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(default_start, today),
    min_value=today - datetime.timedelta(days=90),
    max_value=today,
)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date = today - datetime.timedelta(days=90)
    end_date   = today

st.sidebar.header("Load / Discharge Filters")
min_discharge = st.sidebar.number_input("Minimum Discharge for Ship", min_value=0, value=0, step=1)
min_load      = st.sidebar.number_input("Minimum Load for Ship",      min_value=0, value=0, step=1)

# ---------------------------------------------------------------------------
# Derive vessel/category lists from demo data filtered to the date range
# ---------------------------------------------------------------------------
_all_data = _load_demo_data()

_in_range_keys = _all_data[
    (_all_data["time"].dt.date >= start_date) &
    (_all_data["time"].dt.date <= end_date)
]["ctr_key"].unique()
_date_filtered = _all_data[_all_data["ctr_key"].isin(_in_range_keys)]

all_vessels = sorted(_date_filtered["ship_id"].dropna().unique().tolist())
categories  = sorted(_all_data["cargo_category"].dropna().unique().tolist())

filtered_vessels = all_vessels
if min_discharge > 0 or min_load > 0:
    _vessel_counts = {}
    for _v in all_vessels:
        _vdf = _date_filtered[_date_filtered["ship_id"] == _v]
        _dis, _ld = 0, 0
        for _k, _g in _vdf.groupby("ctr_key"):
            _sg = _g.sort_values("time")
            if _sg.iloc[0]["source_raw"] == "Ship":
                _dis += 1
            if (_sg["target_raw"] == "Ship").any():
                _ld += 1
        _vessel_counts[_v] = (_dis, _ld)
    filtered_vessels = [
        v for v in all_vessels
        if _vessel_counts.get(v, (0, 0))[0] >= min_discharge
        and _vessel_counts.get(v, (0, 0))[1] >= min_load
    ]

selected_vessel   = st.sidebar.selectbox("Select Vessel ID", ["All Vessels"] + filtered_vessels)
flow_type         = st.sidebar.selectbox(
    "Select Flow Direction",
    ["Discharge from Ship", "Load onto Ship", "All Flows"],
)
selected_categories = st.sidebar.multiselect(
    "Select Cargo Category",
    options=categories,
    default=[],
    placeholder="All categories",
)

st.sidebar.header("Visual Grouping & Noise Reduction")
group_by_berth = st.sidebar.checkbox("Group Blocks", value=True, key="group_by_blocks")
hide_orphans   = st.sidebar.checkbox("Hide Orphaned Locations (Data Gaps)", value=False, key="hide_orphans")
min_volume     = st.sidebar.slider("Minimum Container Volume (Threshold)", min_value=1, max_value=100, value=1)

with st.sidebar.expander("Layout Customisation", expanded=False):
    chart_height = st.slider("Chart Height (Pixels)", min_value=600, max_value=1500, value=900, step=50)
    node_padding = st.slider("Vertical Node Spacing (Padding)", min_value=10, max_value=50, value=20)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def map_to_berth(block, row_str):
    if not block or not row_str:
        return None
    try:
        row = int(row_str)
    except (ValueError, TypeError):
        import re
        m = re.search(r"(\d+)", str(row_str))
        if m:
            try:
                row = int(m.group(1))
            except Exception:
                return None
        else:
            return None

    block = block.upper().strip()
    blocks_order = ['M', 'L', 'K', 'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
    if block not in blocks_order:
        return None

    if block == 'M' and row <= 14:
        return "Berth 6"
    elif block in ['L', 'K']:
        return "Berth 6"
    elif block == 'J' and row >= 3:
        return "Berth 6"
    elif block == 'J' and row <= 2:
        return "Berth 7"
    elif block in ['I', 'H', 'G']:
        return "Berth 7"
    elif block == 'F' and row >= 15:
        return "Berth 7"
    elif block == 'F' and row <= 14:
        return "Berth 8"
    elif block == 'E':
        return "Berth 8"
    elif block == 'D' and row >= 3:
        return "Berth 8"
    elif block == 'D' and row <= 2:
        return "Berth 9"
    elif block == 'C':
        return "Berth 9"
    elif block == 'B' and row >= 2:
        return "Berth 9"
    return None


def group_block_label(block, row_str, x_str=None):
    if not block:
        return None
    normalized_block = str(block).upper().strip()
    if normalized_block == "P":
        try:
            if int(x_str) == 6 and int(row_str) in (2, 3):
                return "Pondus"
        except (ValueError, TypeError):
            pass
    if normalized_block in ("MX1", "MX2"):
        return "Cargo Link"
    if normalized_block.startswith("RG"):
        return "ISA"
    if normalized_block.startswith("RB"):
        return "Rail Block"
    if normalized_block.startswith("RE"):
        return "RE"
    if normalized_block.startswith("RW"):
        return "RW"
    berth = map_to_berth(normalized_block, row_str)
    if berth:
        return berth
    return normalized_block


def group_block_label_strict(block, row_str, x_str=None):
    if not block:
        return None
    normalized_block = str(block).upper().strip()
    if normalized_block == "P":
        try:
            if int(x_str) == 6 and int(row_str) in (2, 3):
                return "Pondus"
        except (ValueError, TypeError):
            pass
    if normalized_block in ("MX1", "MX2"):
        return "Cargo Link"
    if normalized_block.startswith("RG"):
        return "ISA"
    if normalized_block.startswith("RB"):
        return "Rail Block"
    if normalized_block.startswith("RE"):
        return "RE"
    if normalized_block.startswith("RW"):
        return "RW"
    berth = map_to_berth(normalized_block, row_str)
    if berth:
        return berth
    return None

# ---------------------------------------------------------------------------
# Filter demo data by sidebar selections
# ---------------------------------------------------------------------------
_in_range = _all_data[
    (_all_data["time"].dt.date >= start_date) &
    (_all_data["time"].dt.date <= end_date)
]["ctr_key"].unique()

df_raw = _all_data[_all_data["ctr_key"].isin(_in_range)].copy()

if selected_vessel != "All Vessels":
    _vessel_keys = df_raw[df_raw["ship_id"] == selected_vessel]["ctr_key"].unique()
    df_raw = df_raw[df_raw["ctr_key"].isin(_vessel_keys)]

if selected_categories:
    df_raw = df_raw[df_raw["cargo_category"].isin(selected_categories)]

# ---------------------------------------------------------------------------
# Process data and build the interactive visualisation
# ---------------------------------------------------------------------------
if not df_raw.empty:
    processed_moves = []

    for ctr_key, group in df_raw.groupby("ctr_key"):
        sorted_group = group.sort_values("time")

        moves = []
        for _, row in sorted_group.iterrows():
            src     = row["source_raw"]
            tgt     = row["target_raw"]
            src_blk = row["pick_blk"]
            src_y   = row["pick_y"]
            tgt_blk = row["place_blk"]
            tgt_y   = row["place_y"]

            if src != "Unknown" and tgt != "Unknown":
                moves.append((src, tgt, src_blk, src_y, row["pick_x"], tgt_blk, tgt_y, row["place_x"], row["ship_id"], row["cargo_category"]))

        if not moves:
            continue

        prev_tgt_final = None
        for j, (src, tgt, src_blk, src_y, src_x, tgt_blk, tgt_y, tgt_x, ship_id, cargo_category) in enumerate(moves):
            move_seq  = j + 1
            src_final = src
            tgt_final = tgt

            if group_by_berth:
                if isinstance(src, str) and src.startswith("Block "):
                    src_group = group_block_label(src_blk, src_y, src_x)
                    if src_group:
                        src_final = src_group
                if isinstance(tgt, str) and tgt.startswith("Block "):
                    tgt_group = group_block_label(tgt_blk, tgt_y, tgt_x)
                    if tgt_group:
                        tgt_final = tgt_group

            if j > 0 and prev_tgt_final is not None and src_final != prev_tgt_final:
                break

            processed_moves.append({
                "ctr_key":        ctr_key,
                "ctr_no":         row["ctr_no"],
                "ship_id":        ship_id,
                "cargo_category": cargo_category,
                "move_seq":       move_seq,
                "source_node":    f"Step {move_seq}: {src_final}",
                "target_node":    f"Step {move_seq + 1}: {tgt_final}",
                "source_clean":   src_final,
                "target_clean":   tgt_final,
                "pick_blk":       src_blk,
                "place_blk":      tgt_blk,
                "pick_x":         row["pick_x"],
                "pick_y":         row["pick_y"],
                "pick_z":         row["pick_z"],
                "place_x":        row["place_x"],
                "place_y":        row["place_y"],
                "place_z":        row["place_z"],
            })
            prev_tgt_final = tgt_final

    df_processed = pd.DataFrame(processed_moves)

    if not df_processed.empty:
        if min_discharge > 0 or min_load > 0:
            import_counts = {}
            export_counts = {}

            for ship_id in df_processed['ship_id'].unique():
                ship_data = df_processed[df_processed['ship_id'] == ship_id]
                imports = len(ship_data[(ship_data['move_seq'] == 1) & (ship_data['source_clean'] == 'Ship')]['ctr_key'].unique())
                import_counts[ship_id] = imports
                exports = len(ship_data[ship_data['target_clean'] == 'Ship']['ctr_key'].unique())
                export_counts[ship_id] = exports

            valid_ships = [
                s for s, cnt in import_counts.items()
                if cnt >= min_discharge and export_counts.get(s, 0) >= min_load
            ]
            df_processed = df_processed[df_processed['ship_id'].isin(valid_ships)]

        if flow_type == "Discharge from Ship":
            import_keys = df_processed[
                (df_processed["move_seq"] == 1) &
                (df_processed["source_node"].str.endswith(": Ship"))
            ]["ctr_key"].unique()
            df_processed = df_processed[df_processed["ctr_key"].isin(import_keys)]
        elif flow_type == "Load onto Ship":
            export_keys = df_processed[
                df_processed["target_node"].str.endswith(": Ship")
            ]["ctr_key"].unique()
            df_processed = df_processed[df_processed["ctr_key"].isin(export_keys)]

    if not df_processed.empty:
        df_grouped  = df_processed.groupby(["source_node", "target_node"]).size().reset_index(name="move_count")
        df_filtered = df_grouped[df_grouped["move_count"] >= min_volume].copy()

        if not df_filtered.empty:
            all_sources          = set(df_filtered['source_node'].unique())
            all_targets          = set(df_filtered['target_node'].unique())
            non_step_one_sources = {n for n in all_sources if not n.startswith("Step 1:")}
            orphaned_nodes       = non_step_one_sources - all_targets

            node_to_keys     = {}
            orphaned_details = []

            if orphaned_nodes:
                df_orphans = df_processed[df_processed['source_node'].isin(orphaned_nodes)]
                for node in orphaned_nodes:
                    keys             = df_orphans[df_orphans['source_node'] == node]['ctr_key'].unique()
                    node_to_keys[node] = list(keys)
                    for k in keys:
                        journey       = df_processed[df_processed['ctr_key'] == k].sort_values('move_seq')
                        journey_steps = list(journey['source_clean'].unique())
                        journey_steps.append(journey['target_clean'].iloc[-1])
                        orphaned_details.append({
                            "Orphaned Location":         node,
                            "Container Key":             k,
                            "Recorded Journey Sequence": " to ".join(journey_steps),
                        })

            if hide_orphans:
                df_filtered = df_filtered[
                    (~df_filtered['source_node'].isin(orphaned_nodes)) &
                    (~df_filtered['target_node'].isin(orphaned_nodes))
                ].copy()
                orphaned_nodes   = set()
                orphaned_details = []

            unique_nodes = sorted(
                pd.concat([df_filtered['source_node'], df_filtered['target_node']]).unique(),
                key=lambda n: (int(n.split(":")[0].replace("Step ", "").strip()) if ":" in n else 0, n),
            )
            node_mapping = {node: idx for idx, node in enumerate(unique_nodes)}

            df_filtered['source_idx'] = df_filtered['source_node'].map(node_mapping)
            df_filtered['target_idx'] = df_filtered['target_node'].map(node_mapping)

            def get_step_num(node_name):
                try:
                    return int(node_name.split(":")[0].replace("Step ", "").strip())
                except Exception:
                    return 1

            steps    = [get_step_num(n) for n in unique_nodes]
            max_step = max(steps) if steps else 1

            step_counts = {}
            for s in range(1, max_step + 1):
                if s == 1:
                    keys = set(df_processed[df_processed['move_seq'] == 1]['ctr_key'])
                else:
                    keys = (
                        set(df_processed[df_processed['move_seq'] == s]['ctr_key']) |
                        set(df_processed[df_processed['move_seq'] == s - 1]['ctr_key'])
                    )
                step_counts[s] = len(keys)

            st.subheader("Step Sequence & Container Volume")
            STEP_SCROLL_THRESHOLD = 20
            if max_step > STEP_SCROLL_THRESHOLD:
                _W        = max(max_step * 110, 1400)
                _ml       = 20
                _pw       = _W - _ml - 20
                _spacing  = (0.96 / (max_step - 1) * _pw) if max_step > 1 else _pw
                _card_w   = max(55, min(110, int(_spacing) - 4))
                _items    = []
                for s in range(1, max_step + 1):
                    x_frac    = (0.02 + 0.96 * (s - 1) / (max_step - 1)) if max_step > 1 else 0.5
                    center_px = _ml + x_frac * _pw
                    left_px   = center_px - _card_w / 2
                    _items.append(
                        f'<div style="position:absolute;left:{left_px:.1f}px;width:{_card_w}px;'
                        f'text-align:center;background-color:#1e222b;padding:10px 4px;'
                        f'border-radius:8px;border:1px solid #31333f;">'
                        f'<div style="margin:0;color:#ffffff;font-size:0.9em;font-weight:bold;">Step {s}</div>'
                        f'<span style="font-size:1.15em;color:#17a2b8;font-weight:bold;">{step_counts.get(s, 0):,}</span>'
                        f'<div style="font-size:0.72em;color:#a3a8b4;">Containers</div></div>'
                    )
                scrollable_cards_html = (
                    f'<div style="position:relative;width:{_W}px;height:90px;min-width:{_W}px;">'
                    + "".join(_items) + '</div>'
                )
            else:
                header_cols = st.columns(max_step)
                for s in range(1, max_step + 1):
                    with header_cols[s - 1]:
                        st.markdown(
                            f'<div style="text-align:center;background-color:#1e222b;padding:12px;'
                            f'border-radius:8px;border:1px solid #31333f;margin-bottom:15px;">'
                            f'<h4 style="margin:0;color:#ffffff;font-size:1.15em;">Step {s}</h4>'
                            f'<span style="font-size:1.35em;color:#17a2b8;font-weight:bold;">{step_counts.get(s, 0):,}</span>'
                            f'<div style="font-size:0.8em;color:#a3a8b4;">Containers</div></div>',
                            unsafe_allow_html=True,
                        )

            x_coords = [
                0.02 + 0.96 * (get_step_num(n) - 1) / (max_step - 1) if max_step > 1 else 0.5
                for n in unique_nodes
            ]

            node_volumes = {
                n: max(
                    df_filtered[df_filtered['target_node'] == n]['move_count'].sum(),
                    df_filtered[df_filtered['source_node'] == n]['move_count'].sum(),
                )
                for n in unique_nodes
            }

            step_groups = defaultdict(list)
            for n in unique_nodes:
                step_groups[get_step_num(n)].append((n, node_volumes.get(n, 0)))
            for s in step_groups:
                step_groups[s].sort(key=lambda x: x[1], reverse=True)

            step_volumes = {s: sum(v for _, v in nl) for s, nl in step_groups.items()}
            max_step_vol = max(step_volumes.values()) if step_volumes else 1

            y_coords_map = {}
            for s, nl in step_groups.items():
                if not nl:
                    continue
                num   = len(nl)
                scale = step_volumes[s] / max_step_vol
                half  = scale * 0.45
                y_min = max(0.02, 0.5 - half)
                y_max = min(0.98, 0.5 + half)
                for i, (n, _) in enumerate(nl):
                    y_coords_map[n] = 0.5 if num == 1 else y_min + (y_max - y_min) * i / (num - 1)

            y_coords = [y_coords_map[n] for n in unique_nodes]

            COLOR_PALETTE = {
                "Berth 6": "rgba(23, 162, 184, 0.8)",    "Berth 7": "rgba(40, 167, 69, 0.8)",
                "Berth 8": "rgba(255, 193, 7, 0.8)",     "Berth 9": "rgba(220, 53, 69, 0.8)",
                "Rail Block": "rgba(253, 126, 20, 0.8)", "ISA": "rgba(214, 51, 132, 0.8)",
                "Cargo Link": "rgba(32, 201, 151, 0.8)", "RE": "rgba(108, 117, 125, 0.8)",
                "RW": "rgba(13, 202, 240, 0.8)",         "Pondus": "rgba(255, 127, 80, 0.8)",
                "Truck": "rgba(111, 66, 193, 0.8)",      "Rail": "rgba(253, 126, 20, 0.8)",
                "Ship": "rgba(0, 123, 255, 0.8)",
            }
            LINK_COLOR_PALETTE = {
                "Berth 6": "rgba(23, 162, 184, 0.6)",    "Berth 7": "rgba(40, 167, 69, 0.6)",
                "Berth 8": "rgba(255, 193, 7, 0.6)",     "Berth 9": "rgba(220, 53, 69, 0.6)",
                "Rail Block": "rgba(253, 126, 20, 0.55)", "ISA": "rgba(214, 51, 132, 0.55)",
                "Cargo Link": "rgba(32, 201, 151, 0.55)", "RE": "rgba(108, 117, 125, 0.55)",
                "RW": "rgba(13, 202, 240, 0.55)",        "Pondus": "rgba(255, 127, 80, 0.55)",
                "Truck": "rgba(111, 66, 193, 0.55)",     "Rail": "rgba(253, 126, 20, 0.55)",
                "Ship": "rgba(0, 123, 255, 0.55)",
            }

            node_colors = []
            for n in unique_nodes:
                matched = False
                for key, col in COLOR_PALETTE.items():
                    if key in n:
                        node_colors.append(col)
                        matched = True
                        break
                if not matched:
                    node_colors.append("rgba(108, 117, 125, 0.8)")

            link_colors = []
            for _, r in df_filtered.iterrows():
                matched = False
                for key, col in LINK_COLOR_PALETTE.items():
                    if key in r['target_node']:
                        link_colors.append(col)
                        matched = True
                        break
                if not matched:
                    link_colors.append("rgba(173, 181, 189, 0.25)")

            display_labels = []
            for n in unique_nodes:
                parts = n.split(": ", 1)
                name  = parts[1] if len(parts) > 1 else n
                if n in orphaned_nodes:
                    keys = node_to_keys.get(n, [])
                    sk   = ", ".join(map(str, keys[:5]))
                    if len(keys) > 5:
                        sk += f" (+{len(keys)-5} more)"
                    display_labels.append(f"{name} (GAP! Keys: {sk})")
                else:
                    display_labels.append(name)

            fig = go.Figure(data=[go.Sankey(
                arrangement = "snap",
                textfont    = dict(color="#ffffff", size=12),
                node = dict(
                    pad=node_padding, thickness=20,
                    line=dict(color="black", width=0.5),
                    label=display_labels, color=node_colors,
                    align="left", x=x_coords, y=y_coords,
                ),
                link = dict(
                    source=df_filtered['source_idx'], target=df_filtered['target_idx'],
                    value=df_filtered['move_count'], color=link_colors,
                    hovertemplate='Route: %{source.label} to %{target.label}<br>Containers: %{value}<extra></extra>',
                ),
            )])

            sankey_needs_scroll = max_step > STEP_SCROLL_THRESHOLD
            fig.update_layout(
                title_text=f"Interactive Container Flow ({flow_type})",
                font_size=12, height=chart_height,
                margin=dict(t=50, b=20, l=20, r=20),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font_color="#ffffff",
                **({"width": max(max_step * 110, 1400)} if sankey_needs_scroll else {}),
            )

            tab1, tab2 = st.tabs(["Flow Visualization", "Analytics"])

            with tab1:
                import json as _json
                _nc_j  = _json.dumps(list(node_colors))
                _lc_j  = _json.dumps(list(link_colors))
                _src_j = _json.dumps(list(df_filtered['source_idx'].astype(int)))
                _tgt_j = _json.dumps(list(df_filtered['target_idx'].astype(int)))

                _link_keys = []
                for _, _lr in df_filtered.iterrows():
                    _lk = df_processed[
                        (df_processed['source_node'] == _lr['source_node']) &
                        (df_processed['target_node'] == _lr['target_node'])
                    ]['ctr_key'].unique().tolist()
                    _link_keys.append(_lk)

                _node_keys = [
                    df_processed[
                        (df_processed['source_node'] == _n) | (df_processed['target_node'] == _n)
                    ]['ctr_key'].unique().tolist()
                    for _n in unique_nodes
                ]

                _lkj = _json.dumps(_link_keys)
                _nkj = _json.dumps(_node_keys)
                sankey_div_html = fig.to_html(include_plotlyjs="cdn", full_html=False)

                _HIGHLIGHT_JS = f"""
<script>
(function() {{
  var origNode={_nc_j}, origLink={_lc_j}, srcs={_src_j}, tgts={_tgt_j};
  var linkKeys={_lkj}, nodeKeys={_nkj};
  function setup() {{
    var gd=document.querySelector('.js-plotly-plot');
    if(!gd||typeof gd.on!=='function'){{setTimeout(setup,300);return;}}
    var active=false, lastHovered=null;
    function dimNodeText(c){{gd.querySelectorAll('g.sankey-node').forEach(function(el,i){{var t=el.querySelector('text');if(t)t.style.opacity=c.has(i)?'1':'0.15';}});}}
    function resetNodeText(){{gd.querySelectorAll('g.sankey-node text').forEach(function(el){{el.style.opacity='1';}});}}
    function reset(){{Plotly.restyle(gd,{{'node.color':[origNode.slice()],'link.color':[origLink.slice()]}}).then(resetNodeText);active=false;}}
    function traceKeys(ks,cn,cl){{for(var i=0;i<linkKeys.length;i++){{var lk=linkKeys[i];for(var k=0;k<lk.length;k++){{if(ks.has(lk[k])){{cl.add(i);cn.add(srcs[i]);cn.add(tgts[i]);break;}}}}}}}}
    function handleHit(pt){{
      var idx=pt.pointNumber,ks;
      if(pt.flow!==undefined){{if(idx<0||idx>=linkKeys.length)return;ks=new Set(linkKeys[idx]);}}
      else{{if(idx<0||idx>=nodeKeys.length)return;ks=new Set(nodeKeys[idx]);}}
      if(ks.size===0)return;
      var cn=new Set(),cl=new Set();traceKeys(ks,cn,cl);
      if(cn.size===0&&cl.size===0)return;
      Plotly.restyle(gd,{{
        'node.color':[origNode.map(function(c,i){{return cn.has(i)?c:'rgba(100,100,100,0.15)';}})],
        'link.color':[origLink.map(function(c,i){{return cl.has(i)?c:'rgba(100,100,100,0.05)';}})]
      }}).then(function(){{dimNodeText(cn);}});
      active=true;
    }}
    gd.on('plotly_hover',function(ev){{if(ev&&ev.points&&ev.points.length)lastHovered=ev.points[0];}});
    var mdPos=null,mdHov=null;
    gd.addEventListener('mousedown',function(e){{mdPos=[e.clientX,e.clientY];mdHov=lastHovered;lastHovered=null;}},true);
    gd.addEventListener('mouseup',function(e){{
      if(!mdPos)return;var pos=mdPos,hov=mdHov;mdPos=null;mdHov=null;
      if(!hov||Math.hypot(e.clientX-pos[0],e.clientY-pos[1])>5)return;
      if(active){{reset();return;}}handleHit(hov);
    }});
    var da=0;
    function disableDrag(){{var els=gd.querySelectorAll('g.sankey-node');if(els.length===0){{if(da++<20)setTimeout(disableDrag,300);return;}}
      els.forEach(function(el){{if(!el._dd){{el._dd=true;el.style.cursor='default';el.addEventListener('mousedown',function(e){{e.stopImmediatePropagation();}},true);}}}});}}
    disableDrag();
    function fixText(){{document.querySelectorAll('svg text').forEach(function(el){{el.removeAttribute('stroke');el.removeAttribute('stroke-width');el.style.stroke='none';el.style.strokeWidth='0';}});}}
    var obs=new MutationObserver(function(){{if(document.querySelectorAll('svg text').length>0){{fixText();obs.disconnect();}}}});
    obs.observe(document.body,{{childList:true,subtree:true}});setTimeout(function(){{fixText();obs.disconnect();}},2000);
  }}
  setTimeout(setup,500);
}})();
</script>"""

                if sankey_needs_scroll:
                    components.html(
                        f"""<!DOCTYPE html><html><head>
<style>body{{margin:0;padding:8px 0 0 0;background:#0e1117;overflow:hidden;font-family:sans-serif;}}
#scroller{{overflow-x:auto;overflow-y:hidden;}}</style></head><body>
<div id="scroller">
  <div style="display:inline-flex;gap:8px;min-width:max-content;padding:0 0 10px 0;">{scrollable_cards_html}</div>
  <div>{sankey_div_html}</div>
</div>{_HIGHLIGHT_JS}</body></html>""",
                        height=chart_height + 140, scrolling=False,
                    )
                else:
                    components.html(
                        f"""<!DOCTYPE html><html><head>
<style>body{{margin:0;padding:0;background:#0e1117;overflow:hidden;font-family:sans-serif;}}</style></head><body>
{sankey_div_html}{_HIGHLIGHT_JS}</body></html>""",
                        height=chart_height + 20, scrolling=False,
                    )

                @st.fragment
                def _node_detail(df_proc, uniq_nodes, orphan_details):
                    if "selected_flow_node" not in st.session_state:
                        st.session_state["selected_flow_node"] = "(None)"

                    st.selectbox(
                        "Selected Step/Block",
                        ["(None)"] + uniq_nodes,
                        key="selected_flow_node",
                    )

                    sel = st.session_state["selected_flow_node"]
                    if sel == "(None)":
                        sel = None

                    if orphan_details:
                        st.subheader("Data Gap Diagnostics")
                        st.write(
                            "The container visits listed below have broken sequences where a step starts "
                            "without a corresponding previous target step. This is typically caused by "
                            "missing logging activity or unrecorded moves on roadways."
                        )
                        st.dataframe(pd.DataFrame(orphan_details), use_container_width=True)

                    if sel:
                        sel_label = sel.split(": ", 1)[1] if ": " in sel else sel
                        try:
                            sel_step = int(sel.split(":")[0].replace("Step ", "").strip())
                        except (ValueError, IndexError):
                            sel_step = 1

                        df_node_rows = df_proc[
                            (df_proc["source_node"] == sel) |
                            (df_proc["target_node"] == sel)
                        ][[
                            "ctr_key", "ctr_no", "ship_id", "cargo_category", "move_seq",
                            "source_clean", "target_clean",
                            "pick_blk", "place_blk",
                            "pick_x", "pick_y", "pick_z",
                            "place_x", "place_y", "place_z",
                        ]].drop_duplicates()

                        st.subheader(f"Selected Step Details: {sel}")

                        show_incoming = st.toggle(
                            f"Show only incoming moves (Step {sel_step - 1} → {sel_label})",
                            value=False,
                            key="incoming_only_toggle",
                        )

                        display_rows = (
                            df_node_rows[df_node_rows["move_seq"] == sel_step - 1]
                            if show_incoming and sel_step > 1
                            else df_node_rows
                        )

                        st.caption(
                            f"{len(display_rows['ctr_key'].unique()):,} unique containers found for {sel_label}."
                        )
                        st.dataframe(
                            display_rows.sort_values(["ctr_key", "move_seq"]),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.caption("Click a node in the Sankey chart to see container keys for that step.")

                _node_detail(df_processed, unique_nodes, orphaned_details)

            with tab2:
                st.subheader("Summary Analytics")

                total_containers          = len(df_processed['ctr_key'].unique())
                total_vessels             = len(df_processed['ship_id'].unique())
                avg_steps_per_container   = df_processed.groupby('ctr_key')['move_seq'].max().mean()
                avg_containers_per_vessel = total_containers / total_vessels if total_vessels > 0 else 0

                containers_by_vessel   = df_processed.groupby('ship_id')['ctr_key'].nunique().sort_values(ascending=False)
                containers_by_category = df_processed.groupby('cargo_category')['ctr_key'].nunique().sort_values(ascending=False)
                top_routes             = df_grouped.nlargest(10, 'move_count')[['source_node', 'target_node', 'move_count']].copy()
                top_routes['Route']    = top_routes['source_node'] + ' → ' + top_routes['target_node']

                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Total Containers", f"{total_containers:,}")
                with col2: st.metric("Total Vessels",    f"{total_vessels:,}")
                with col3: st.metric("Avg Steps/Container", f"{avg_steps_per_container:.2f}")
                with col4: st.metric("Avg Containers/Vessel", f"{avg_containers_per_vessel:.2f}")

                st.markdown("---")
                st.subheader("Distribution Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Top 10 Routes by Container Volume**")
                    st.dataframe(top_routes[['Route', 'move_count']].rename(columns={'move_count': 'Container Count'}), use_container_width=True, hide_index=True)
                with col2:
                    st.write("**Containers by Cargo Category**")
                    st.dataframe(pd.DataFrame({'Category': containers_by_category.index, 'Count': containers_by_category.values}), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("Vessel Analysis")
                vessel_df = pd.DataFrame({'Vessel': containers_by_vessel.index, 'Container Count': containers_by_vessel.values})
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Top 15 Vessels by Container Volume**")
                    st.dataframe(vessel_df.head(15), use_container_width=True, hide_index=True)
                with col2:
                    vessel_stats = []
                    for v in df_processed['ship_id'].unique():
                        vd        = df_processed[df_processed['ship_id'] == v]
                        imports   = len(vd[(vd['move_seq'] == 1) & (vd['source_clean'] == 'Ship')]['ctr_key'].unique())
                        exports   = len(vd[vd['target_clean'] == 'Ship']['ctr_key'].unique())
                        avg_steps = vd.groupby('ctr_key')['move_seq'].max().mean()
                        vessel_stats.append({'Vessel': v, 'Imports': imports, 'Exports': exports, 'Avg Steps': f"{avg_steps:.2f}"})
                    st.write("**Vessel Import/Export Summary**")
                    st.dataframe(pd.DataFrame(vessel_stats).sort_values('Imports', ascending=False).head(15), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("Location Analysis")
                source_counts = df_processed['source_clean'].value_counts()
                target_counts = df_processed['target_clean'].value_counts()
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Top Origin Locations**")
                    st.dataframe(pd.DataFrame({'Location': source_counts.index, 'Containers': source_counts.values}), use_container_width=True, hide_index=True)
                with col2:
                    st.write("**Top Destination Locations**")
                    st.dataframe(pd.DataFrame({'Location': target_counts.index, 'Containers': target_counts.values}), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("X-Ray Trips")
                st.write(
                    "Containers that made a truck out-and-back trip via TIP (e.g. Block H → TIP → Block E). "
                    "Each consecutive Truck-out / Truck-in pair counts as one X-ray trip."
                )

                _rs = df_raw.sort_values(['ctr_key', 'time'])
                _rs = _rs.assign(
                    _next_src=_rs.groupby('ctr_key')['source_raw'].shift(-1)
                )
                _xray_hits = _rs[
                    (_rs['target_raw'] == 'Truck') & (_rs['_next_src'] == 'Truck')
                ].copy()

                if not _xray_hits.empty:
                    _xray_hits['_in_range'] = _xray_hits['time'].apply(
                        lambda t: start_date <= (t.date() if hasattr(t, 'date') else t) <= end_date
                    )
                    _total_moves = df_raw.groupby('ctr_key').size().rename('Total Moves')
                    _ctr_info    = df_raw.groupby('ctr_key')[['ctr_no', 'cargo_category']].first()
                    _agg = _xray_hits.groupby('ctr_key').agg(
                        **{'X-Ray Trips (All)':      ('target_raw', 'count'),
                           'X-Ray Trips (In Range)': ('_in_range',  'sum')}
                    )
                    xray_df = (
                        _agg
                        .join(_ctr_info)
                        .join(_total_moves)
                        .reset_index()
                        .rename(columns={'ctr_key': 'Container Key', 'ctr_no': 'Container No',
                                         'cargo_category': 'Cargo Category'})
                        [['Container Key', 'Container No', 'Cargo Category',
                          'X-Ray Trips (All)', 'X-Ray Trips (In Range)', 'Total Moves']]
                        .sort_values('X-Ray Trips (All)', ascending=False)
                    )
                else:
                    xray_df = pd.DataFrame()

                if not xray_df.empty:
                    _xc1, _xc2, _xc3 = st.columns(3)
                    _xc1.metric("Containers Sent for X-Ray", f"{len(xray_df):,}")
                    _xc2.metric("Total X-Ray Trips (All)", f"{xray_df['X-Ray Trips (All)'].sum():,}")
                    _xc3.metric("X-Ray Trips Within Date Range", f"{xray_df['X-Ray Trips (In Range)'].sum():,}")
                    st.dataframe(xray_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No X-ray trips detected in the current filtered data.")
        else:
            st.warning("All data was filtered out by your Minimum Container Volume setting. Try lowering the threshold.")
    else:
        st.info("No container movements found matching those active filters.")
else:
    st.info("No container movements found matching those active filters.")
