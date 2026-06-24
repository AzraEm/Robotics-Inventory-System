import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

APP_TITLE = "Robotics Inventory Checkout System"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
INVENTORY_CSV = DATA_DIR / "inventory.csv"
CHECKOUTS_CSV = DATA_DIR / "checkouts.csv"
RETURNS_CSV = DATA_DIR / "returns.csv"

REQUIRED_INVENTORY_COLUMNS = [
    "Part ID", "Part Name", "Category", "Location", "Starting Qty", "Current Qty",
    "Reorder At", "Returnable", "Notes"
]
REQUIRED_CHECKOUT_COLUMNS = [
    "Timestamp", "Team Number", "Student Name", "Part ID", "Part Name", "Quantity", "Purpose", "Status"
]
REQUIRED_RETURNS_COLUMNS = [
    "Timestamp", "Team Number", "Student Name", "Part ID", "Part Name", "Quantity", "Notes"
]

SAMPLE_INVENTORY = [
    ["VEX-001", "Smart Motor", "Electronics", "D-01", 12, 12, 5, "Yes", "High-demand item"],
    ["VEX-002", "Battery", "Electronics", "D-02", 10, 10, 4, "Yes", "Charge after return"],
    ["VEX-003", "Shaft Collar", "Hardware", "A-03", 42, 42, 15, "No", "Often lost"],
    ["VEX-004", "Bearing Flat", "Hardware", "A-04", 60, 60, 20, "No", "Keep near shafts"],
    ["VEX-005", "36T Gear", "Motion", "B-05", 18, 18, 6, "Yes", "Common drivetrain part"],
    ["VEX-006", "C-Channel", "Structure", "C-01", 30, 30, 8, "Yes", "Sort by length separately"],
]


def init_local_files():
    if not INVENTORY_CSV.exists():
        pd.DataFrame(SAMPLE_INVENTORY, columns=REQUIRED_INVENTORY_COLUMNS).to_csv(INVENTORY_CSV, index=False)
    if not CHECKOUTS_CSV.exists():
        pd.DataFrame(columns=REQUIRED_CHECKOUT_COLUMNS).to_csv(CHECKOUTS_CSV, index=False)
    if not RETURNS_CSV.exists():
        pd.DataFrame(columns=REQUIRED_RETURNS_COLUMNS).to_csv(RETURNS_CSV, index=False)


def get_google_client():
    if gspread is None or Credentials is None:
        return None
    if "gcp_service_account" not in st.secrets:
        return None
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)


def using_google_sheets():
    return "google_sheet_name" in st.secrets and get_google_client() is not None


def get_worksheet(sheet, name, columns):
    try:
        ws = sheet.worksheet(name)
    except Exception:
        ws = sheet.add_worksheet(title=name, rows=1000, cols=max(10, len(columns)))
        ws.append_row(columns)
    existing = ws.row_values(1)
    if existing != columns:
        ws.clear()
        ws.append_row(columns)
    return ws


def read_data(sheet_name):
    init_local_files()
    if using_google_sheets():
        client = get_google_client()
        sheet = client.open(st.secrets["google_sheet_name"])
        if sheet_name == "Inventory":
            ws = get_worksheet(sheet, "Inventory", REQUIRED_INVENTORY_COLUMNS)
            data = ws.get_all_records()
            if not data:
                ws.append_rows(SAMPLE_INVENTORY)
                data = ws.get_all_records()
            return pd.DataFrame(data)
        if sheet_name == "Checkouts":
            ws = get_worksheet(sheet, "Checkouts", REQUIRED_CHECKOUT_COLUMNS)
            return pd.DataFrame(ws.get_all_records())
        if sheet_name == "Returns":
            ws = get_worksheet(sheet, "Returns", REQUIRED_RETURNS_COLUMNS)
            return pd.DataFrame(ws.get_all_records())
    file_map = {"Inventory": INVENTORY_CSV, "Checkouts": CHECKOUTS_CSV, "Returns": RETURNS_CSV}
    return pd.read_csv(file_map[sheet_name])


def write_data(sheet_name, df):
    if using_google_sheets():
        client = get_google_client()
        sheet = client.open(st.secrets["google_sheet_name"])
        columns = {
            "Inventory": REQUIRED_INVENTORY_COLUMNS,
            "Checkouts": REQUIRED_CHECKOUT_COLUMNS,
            "Returns": REQUIRED_RETURNS_COLUMNS,
        }[sheet_name]
        ws = get_worksheet(sheet, sheet_name, columns)
        ws.clear()
        ws.update([columns] + df.fillna("").astype(str).values.tolist())
        return
    file_map = {"Inventory": INVENTORY_CSV, "Checkouts": CHECKOUTS_CSV, "Returns": RETURNS_CSV}
    df.to_csv(file_map[sheet_name], index=False)


def append_row(sheet_name, row):
    df = read_data(sheet_name)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_data(sheet_name, df)


def normalize_numbers(df):
    for col in ["Starting Qty", "Current Qty", "Reorder At"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def inventory_metrics(inv):
    total_parts = len(inv)
    total_units = int(inv["Current Qty"].sum()) if not inv.empty else 0
    low_stock = inv[inv["Current Qty"] <= inv["Reorder At"]]
    out_stock = inv[inv["Current Qty"] <= 0]
    return total_parts, total_units, len(low_stock), len(out_stock)


st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide")
st.title("🤖 Robotics Inventory Checkout System")
st.caption("Track VEX/robotics parts, checkout requests, returns, low-stock alerts, and storage locations.")

mode_text = "Google Sheets" if using_google_sheets() else "Local CSV demo mode"
st.sidebar.success(f"Data source: {mode_text}")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Search Parts", "Request Checkout", "Return Parts", "Checkout History", "Admin Inventory"],
)

inventory = normalize_numbers(read_data("Inventory"))
checkouts = read_data("Checkouts")
returns = read_data("Returns")

if page == "Dashboard":
    total_parts, total_units, low_count, out_count = inventory_metrics(inventory)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Parts", total_parts)
    c2.metric("Total Units", total_units)
    c3.metric("Low Stock", low_count)
    c4.metric("Out of Stock", out_count)

    st.subheader("Low-Stock Alerts")
    low_stock = inventory[inventory["Current Qty"] <= inventory["Reorder At"]].sort_values("Current Qty")
    if low_stock.empty:
        st.success("No low-stock items right now.")
    else:
        st.dataframe(low_stock[["Part ID", "Part Name", "Category", "Location", "Current Qty", "Reorder At"]], use_container_width=True)

    st.subheader("Current Inventory")
    st.dataframe(inventory, use_container_width=True)

elif page == "Search Parts":
    st.subheader("Search Parts")
    query = st.text_input("Search by part name, ID, category, location, or notes")
    category = st.selectbox("Filter by category", ["All"] + sorted(inventory["Category"].dropna().astype(str).unique().tolist()))
    filtered = inventory.copy()
    if query:
        q = query.lower()
        filtered = filtered[filtered.astype(str).apply(lambda row: row.str.lower().str.contains(q).any(), axis=1)]
    if category != "All":
        filtered = filtered[filtered["Category"].astype(str) == category]
    st.dataframe(filtered, use_container_width=True)

elif page == "Request Checkout":
    st.subheader("Request Parts")
    available = inventory[inventory["Current Qty"] > 0].copy()
    if available.empty:
        st.warning("No parts are currently available.")
    else:
        labels = available.apply(lambda r: f"{r['Part ID']} — {r['Part Name']} ({r['Current Qty']} available, {r['Location']})", axis=1).tolist()
        selected_label = st.selectbox("Choose part", labels)
        selected_part_id = selected_label.split(" — ")[0]
        part_row = inventory[inventory["Part ID"] == selected_part_id].iloc[0]
        with st.form("checkout_form"):
            team = st.text_input("Team Number")
            student = st.text_input("Student Name")
            qty = st.number_input("Quantity", min_value=1, max_value=int(part_row["Current Qty"]), value=1)
            purpose = st.text_area("Purpose / robot subsystem / notes")
            submitted = st.form_submit_button("Submit Checkout")
        if submitted:
            if not team or not student:
                st.error("Please enter team number and student name.")
            else:
                idx = inventory.index[inventory["Part ID"] == selected_part_id][0]
                inventory.at[idx, "Current Qty"] = int(inventory.at[idx, "Current Qty"]) - int(qty)
                write_data("Inventory", inventory)
                append_row("Checkouts", {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Team Number": team,
                    "Student Name": student,
                    "Part ID": selected_part_id,
                    "Part Name": part_row["Part Name"],
                    "Quantity": int(qty),
                    "Purpose": purpose,
                    "Status": "Checked Out",
                })
                st.success(f"Checked out {qty} × {part_row['Part Name']} to Team {team}.")
                st.rerun()

elif page == "Return Parts":
    st.subheader("Return Parts")
    labels = inventory.apply(lambda r: f"{r['Part ID']} — {r['Part Name']} ({r['Location']})", axis=1).tolist()
    selected_label = st.selectbox("Choose returned part", labels)
    selected_part_id = selected_label.split(" — ")[0]
    part_row = inventory[inventory["Part ID"] == selected_part_id].iloc[0]
    with st.form("return_form"):
        team = st.text_input("Team Number")
        student = st.text_input("Student Name")
        qty = st.number_input("Quantity returned", min_value=1, value=1)
        notes = st.text_area("Condition / notes")
        submitted = st.form_submit_button("Submit Return")
    if submitted:
        if not team or not student:
            st.error("Please enter team number and student name.")
        else:
            idx = inventory.index[inventory["Part ID"] == selected_part_id][0]
            inventory.at[idx, "Current Qty"] = int(inventory.at[idx, "Current Qty"]) + int(qty)
            write_data("Inventory", inventory)
            append_row("Returns", {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Team Number": team,
                "Student Name": student,
                "Part ID": selected_part_id,
                "Part Name": part_row["Part Name"],
                "Quantity": int(qty),
                "Notes": notes,
            })
            st.success(f"Returned {qty} × {part_row['Part Name']} from Team {team}.")
            st.rerun()

elif page == "Checkout History":
    st.subheader("Checkout History")
    st.dataframe(checkouts, use_container_width=True)
    st.subheader("Return History")
    st.dataframe(returns, use_container_width=True)

elif page == "Admin Inventory":
    st.subheader("Admin Inventory Editor")
    st.info("Edit quantities, locations, reorder thresholds, categories, and notes. Click Save when finished.")
    edited = st.data_editor(inventory, num_rows="dynamic", use_container_width=True)
    if st.button("Save Inventory Changes"):
        for col in REQUIRED_INVENTORY_COLUMNS:
            if col not in edited.columns:
                edited[col] = ""
        edited = edited[REQUIRED_INVENTORY_COLUMNS]
        edited = normalize_numbers(edited)
        write_data("Inventory", edited)
        st.success("Inventory saved.")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Tip: Use bin labels like A-01, B-05, D-02 so teams can find parts quickly.")
