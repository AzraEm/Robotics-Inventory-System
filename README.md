# Robotics Inventory Checkout System

A Streamlit web app for managing a VEX/robotics team inventory system.

## Features

- Dashboard with total inventory and low-stock alerts
- Search parts by name, ID, category, location, or notes
- Checkout request form
- Automatic inventory quantity updates
- Return parts form
- Checkout and return history
- Admin inventory editor
- Google Sheets support
- Local CSV demo mode for testing

## Quick Start: Local Demo Mode

1. Install Python 3.10+.
2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run app.py
```

The app will create a `data/` folder with sample CSV files.

## Google Sheets Setup

1. Create a Google Sheet with this name, for example:

```text
Robotics Inventory System
```

2. Create a Google Cloud service account and download its JSON key.
3. Share the Google Sheet with the service account email address.
4. Create a folder called `.streamlit` in this project.
5. Create `.streamlit/secrets.toml` using this template:

```toml
google_sheet_name = "Robotics Inventory System"

[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
universe_domain = "googleapis.com"
```

6. Run:

```bash
streamlit run app.py
```

The app will automatically create these tabs if they do not already exist:

- Inventory
- Checkouts
- Returns

## Recommended Inventory Columns

The app expects these columns:

- Part ID
- Part Name
- Category
- Location
- Starting Qty
- Current Qty
- Reorder At
- Returnable
- Notes

## Suggested Storage Labels

- A = Hardware: screws, nuts, spacers, shaft collars, bearings
- B = Motion: gears, sprockets, chain, pulleys, belts
- C = Structure: C-channels, plates, gussets, standoffs
- D = Electronics: motors, batteries, controllers, sensors
- E = Pneumatics
- F = Competition emergency spares

Use drawer labels like `A-01`, `B-05`, and `D-02`.
