# Port Container Flow Visualiser

An interactive web application for analysing how shipping containers move through a port terminal — from vessel discharge, through the yard, to truck or rail gate-out, and vice versa for outbound loads.

---

## The Problem

A busy container terminal handles thousands of container movements every day across multiple berths, yard blocks, and transport modes. Understanding the flow of containers — where they go, how many steps they take, and which routes are busiest — is critical for planning, performance analysis, and identifying operational bottlenecks.

The raw data for these movements exists in the terminal's operational database, but it's dense and difficult to interpret in tabular form. What was needed was a way to visualise the entire journey of containers through the facility at a glance, with the ability to filter by vessel, date range, cargo type, and flow direction.

---

## What It Does

The visualiser reads container movement records from a PostgreSQL database and renders them as an interactive **Sankey flow diagram** — a chart type specifically suited to showing how volumes move through a sequence of stages.

Each column in the diagram represents a step in the container's journey (Step 1, Step 2, Step 3, etc.). Each node is a location — a ship, a yard berth zone, a rail terminal, or a truck gate. The width of each flow band is proportional to the number of containers that took that route.

**At a glance you can see:**
- Which berths are receiving or dispatching the most containers
- How many re-handles (intermediate yard moves) are happening before gate-out
- The split between truck and rail interchange volumes
- Which vessels drove the most throughput in a given period
- Where data gaps exist in the movement records (broken journey sequences)

---

## Key Features

**Interactive Sankey Diagram**
Click any node or flow band to highlight the full path of containers that passed through it. Everything else fades to the background, making it easy to trace a specific route through the terminal. Click again to reset.

**Berth Zone Colour Coding**
Yard blocks are automatically grouped into their associated berth zones (Berths 6, 7, 8, 9, Rail Block, ISA, Cargo Link) and colour-coded consistently throughout the diagram and analytics.

**Sidebar Filters**
- Date range selection
- Vessel selection (dynamically populated from the data)
- Flow direction — Discharge from Ship, Load onto Ship, or All Flows
- Cargo category (Import, Export, Tranship, Empty)
- Minimum container volume threshold to suppress low-traffic routes
- Visual grouping toggle to switch between individual block labels and grouped berth zones

**Analytics Tab**
A separate tab provides summary statistics: total container and vessel counts, average steps per container, top routes by volume, vessel import/export breakdowns, and origin/destination location rankings.

**Data Gap Diagnostics**
Containers whose recorded movement sequences have gaps (a step that starts with no corresponding previous destination) are flagged as orphaned nodes and listed in a diagnostic table below the chart. This surfaces data quality issues in the source system.

**Step Volume Cards**
Above the diagram, a row of cards shows how many unique containers were active at each step in the sequence, giving an instant sense of where volumes drop off through the journey.

---

## Technology Stack

| Tool | Role |
|---|---|
| **Python** | Core application language |
| **Streamlit** | Web application framework — turns a Python script into an interactive dashboard with no frontend code |
| **Plotly** | Interactive charting library used to render the Sankey diagram with hover, click, and highlight behaviour |
| **Pandas** | All data transformation, filtering, grouping, and aggregation after retrieval from the database |
| **psycopg2** | PostgreSQL database driver for querying the terminal's operational data |
| **JavaScript (embedded)** | Custom click-to-highlight interaction layer injected into the Plotly chart — handles mousedown/mouseup capture, container key tracing across all links and nodes, and node drag suppression |

The application is a single Python file. All chart interactivity beyond basic Plotly hover is implemented in a bespoke JavaScript block that is injected into the chart's HTML at render time. This was necessary because Plotly's native Sankey callbacks don't expose the provenance data (which containers used which path) needed to drive the highlight behaviour.

---

## Use Cases

**Operational Visibility**
Supervisors and planners can open the dashboard during or after a vessel call to immediately see where containers are flowing, how many re-handles occurred, and whether the discharge rate is tracking as expected.

**Berth Planning**
By filtering to a specific vessel and viewing the discharge flow, it becomes clear which yard zones are absorbing the most containers from that call — useful for pre-positioning equipment and planning the next vessel's block allocation.

**Performance Benchmarking**
Comparing vessel calls over time, or filtering by cargo category, reveals patterns like which vessel types generate more re-handles, or whether import containers take more steps to gate-out than export containers take to gate-in.

**Data Quality Auditing**
The orphaned node diagnostic surfaces containers whose journey records have gaps, which can indicate unrecorded moves, system clock issues, or equipment not logging correctly. This is difficult to find in raw tabular data but immediately visible as a flagged node in the Sankey.

---

## About the Interactive Demo

The live demo embedded on this page is a fully functional version of the application running on **Streamlit Community Cloud** (free public hosting). Because this is a portfolio demonstration, it uses entirely **synthetic sample data** — no real terminal data, vessel names, or operational figures are present.

The sample data generator (`demo_data.py`) produces approximately 2,000 fictional container visits across 10 invented vessels, spanning the past 90 days. It covers all berth zones and transport modes, includes a realistic mix of discharge and load flows, and generates some re-handle moves to produce a multi-step Sankey. The data is generated with a fixed random seed each time the server starts, so the structure is consistent — only the dates shift to keep the default 30-day filter populated.

**Everything in the demo is fully interactive:**
- All sidebar filters work and re-render the diagram in real time
- Clicking a node or flow band highlights the paths of containers that used it
- The Analytics tab shows real computed statistics from the synthetic dataset
- The node detail table populates when a step is selected from the dropdown

The real production application connects to the terminal's PostgreSQL database and processes live operational data. The demo demonstrates the interface, interaction model, and analytical capabilities without exposing any company information.
