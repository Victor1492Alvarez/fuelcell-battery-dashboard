# FC_Battery_Dashboard_REV6.py (Updated Full Version with Tank Selection, Expanders, PDF)
import tempfile
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import requests
import os
from kpi_calculator_version2 import *
import plotly.graph_objects as go

# Cache cleaning
st.cache_data.clear()
st.cache_resource.clear()

st.set_page_config(page_title="DMFC&Battery System Dashboard", layout="wide")
st.title("🔋 Camping Truck KPI Dashboard")

col1, col2 = st.columns([4, 1])
with col1:
    st.subheader("DMFC & Battery System Performance Analyzer")

# 🔹 Help Section 1: App Introduction
with st.expander("ℹ️ About This App"):
    st.markdown("""
    This dashboard simulates the performance of a hybrid energy supply system using a **direct methanol fuel cell EFOY Pro 2800 (DMFC)** and an EFOY Li 105 Lithium Battery from the company SFC Energy AG.

    🔍 Objective: Estimate energy needs and analyze autonomy, methanol consumption and system efficiency under three typical camping scenarios: Base, Moderate, and Peak Load.

    🛠️ Tip: Use the sidebar at the left to explore different usage patterns by adjusting the operating hours of each device and tanks!.
    """)

# Sidebar - Scenario Selection
st.sidebar.header("Adjust Scenarios and Methanol Storage")
scenario = st.sidebar.selectbox("Select Load Scenario", ["Base 500 W", "Moderate 750 W", "Peak 1000 W"])

# Sidebar - Methanol Tank Size Selection
tank_option = st.sidebar.selectbox("Select Methanol Tank", ["M5 - 5 L", "M10 - 10 L", "M20 - 20 L"])
tank_liters = int(tank_option.split('-')[1].strip().split(' ')[0])

# Define appliances by scenario
if scenario == "Base 500 W":
    appliances = [
        {"name": "Laptop (230 V)", "power": 95, "hours": 4},
        {"name": "Led Lighting (12 V)", "power": 15, "hours": 6},
        {"name": "Cool box (12 V)", "power": 60, "hours": 8},
        {"name": "Smartphone (2 chargers)", "power": 25, "hours": 2},
        {"name": "Electric kettle (12 V)", "power": 300, "hours": 0.5},
        {"name": "Radio (12 V)", "power": 5, "hours": 3},
    ]
elif scenario == "Moderate 750 W":
    appliances = [
        {"name": "Laptop (230 V)", "power": 95, "hours": 4},
        {"name": "Led Lighting (12 V)", "power": 15, "hours": 6},
        {"name": "Cool box (12 V)", "power": 60, "hours": 8},
        {"name": "Bed warmer (12 V)", "power": 240, "hours": 3},
        {"name": "Smartphone (3 chargers)", "power": 35, "hours": 2},
        {"name": "Electric kettle (12 V)", "power": 300, "hours": 0.5},
        {"name": "Radio (12 V)", "power": 5, "hours": 3},
    ]
else:
    appliances = [
        {"name": "Laptop (230 V)", "power": 95, "hours": 4},
        {"name": "Led Lighting (12 V)", "power": 15, "hours": 6},
        {"name": "Cool box (12 V)", "power": 60, "hours": 8},
        {"name": "Fan Heater (12 V)", "power": 490, "hours": 2},
        {"name": "Smartphone (3 chargers)", "power": 35, "hours": 2},
        {"name": "Electric kettle (12 V)", "power": 300, "hours": 0.5},
        {"name": "Radio (12 V)", "power": 5, "hours": 3},
    ]

custom_appliances = []
st.sidebar.header("Adjust Operating Hours")
for app in appliances:
    h = st.sidebar.slider(f"{app['name']} Hours", 0.0, 24.0, float(app['hours']), 0.5)
    custom_appliances.append({"name": app['name'], "power": app['power'], "hours": h})

# 🔹 Help Section 2: System Constants
with st.expander("System Constants (SFC Energy AG References)"):
    constants_df = pd.DataFrame({
        "Parameter": ["Battery Capacity", "Battery Voltage", "Battery Energy", "Fuel Cell Output", "Fuel Cell Efficiency", "Methanol Energy Density", "Methanol Consumption"],
        "Value": [f"{BATTERY_CAPACITY_AH} Ah", f"{BATTERY_VOLTAGE} V", f"{BATTERY_CAPACITY_WH} Wh", f"{FUEL_CELL_OUTPUT_W} W", f"{FUEL_CELL_EFFICIENCY*100:.1f}%", f"{METHANOL_ENERGY_DENSITY:.2f} kWh/L", f"{METHANOL_CONSUMPTION_PER_KWH} L/kWh"]
    })
    st.table(constants_df)

# 🔹 Help Section 3: KPI Formula Descriptions
with st.expander("What are the KPI Calculations about?"):
    st.markdown("""
    1. Daily Energy Demand [Wh] = Σ(Power × Hours) for each device.  
    2. Methanol Consumption [L] = (Daily Energy / 1000) × 0.9 L/kWh.  
    3. Tank Autonomy [days] = Methanol Available / Daily Consumption.  
    4. Battery Autonomy [h] = Battery Capacity / Daily Energy × 24.  
    5. Battery Charge Time [h] = Energy Deficit / Fuel Cell Output.  
    6. System Efficiency [%] = Electrical Energy delivered to system / Methanol Energy.
    """)

# 🧾 Main Calculations
daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(tank_liters, methanol_per_day)
battery_hours = battery_discharge_time(daily_demand_wh)
battery_energy_wh = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy_wh = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
efficiency_pct = global_system_efficiency(battery_energy_wh, fuel_cell_energy_wh, methanol_per_day)
battery_deficit = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
charge_time = battery_charge_time_needed(battery_deficit)

# KPIs
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("📂 Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("🔋 Battery Autonomy", f"{battery_hours:.1f} h")
k5.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")
k6.metric("⚡ Battery Charge Time", f"{charge_time:.1f} h")

# Appliance Summary
st.markdown("Equipments Energy Summary")
df = pd.DataFrame(custom_appliances)
df['Energy (Wh)'] = df['power'] * df['hours']
df['Battery Capacity Used (Ah)'] = df['Energy (Wh)'] / BATTERY_VOLTAGE

total_row = pd.DataFrame({
    "name": ["**TOTAL**"],
    "power": [df['power'].sum()],
    "hours": ["-"],
    "Energy (Wh)": [df['Energy (Wh)'].sum()],
    "Battery Capacity Used (Ah)": [df['Battery Capacity Used (Ah)'].sum()]
})

df = pd.concat([df, total_row], ignore_index=True)
st.dataframe(df.rename(columns={"name": "Device", "power": "Power (W)", "hours": "Hours"}))

# 🔹 Help Section 4: Gauges Descriptions
with st.expander("📊 How to interpret the chart gauges"):
    st.markdown("""
                The Battery Autonomy gauge estimates how long your system can run just on the battery power before requiring recharging. 
                The System Efficiency gauge reflects how effectively methanol fuel is converted into usable electrical energy across the system.
                """)
# 📊 Gauges
fig_batt = go.Figure(go.Indicator(
    mode="gauge+number",
    value=battery_hours,
    title={'text': "Battery Autonomy (h)",'font': {'size': 22,'color': "black"}},
    gauge={
        'axis': {'range': [0, 24]},
        'bar': {'color': "black"},
        'steps': [
            {'range': [0, 2.4], 'color': "gray"},
            {'range': [2.4, 7.2], 'color': "red"},
            {'range': [7.2, 12], 'color': "orange"},
            {'range': [12, 19.2], 'color': "yellow"},
            {'range': [19.2, 24], 'color': "green"},
        ]
    }))
fig_eff = go.Figure(go.Indicator(
    mode="gauge+number",
    value=efficiency_pct * 100,
    title={'text': "System Efficiency (%)",'font': {'size': 22,'color': "black"}},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': "black"},
        'steps': [
            {'range': [0, 20], 'color': "red"},
            {'range': [20, 50], 'color': "orange"},
            {'range': [50, 80], 'color': "yellow"},
            {'range': [80, 100], 'color': "green"},
        ]
    }))

colg1, colg2 = st.columns(2)
colg1.plotly_chart(fig_batt, use_container_width=True)
colg2.plotly_chart(fig_eff, use_container_width=True)

# Create safely temp files and save them for the PDF report
tmp_batt = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
tmp_eff = tempfile.NamedTemporaryFile(suffix=".png", delete=False)

fig_batt.write_image(tmp_batt.name)
fig_eff.write_image(tmp_eff.name)


# PDF Report
st.markdown("### 📄 Export Report as PDF")
if st.button("Generate PDF Performance Report"):
    import os
    #from PIL import Image --this line is commented on 24.06.2025 due to conflicts.
    import io

    # Descargar logo del dashboard
    logo_url = "https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.PNG"
    logo_path = "/tmp/dashboard_logo.png"
    try:
        response = requests.get(logo_url)
        response.raise_for_status()
        with open(logo_path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        st.error(f"❌ No se pudo descargar el logo del dashboard: {e}")
        logo_path = None

    # Descargar y convertir el wiring diagram a PNG válido
    diagram_url = "https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/wiring_diagram_1.png"
    diagram_path = "/tmp/wiring_diagram_1_converted.png"
    diagram_downloaded = False
    try:
        response = requests.get(diagram_url)
        response.raise_for_status()
        with open(diagram_path, "wb") as f:
            f.write(response.content)
        diagram_downloaded = True
    except Exception as e:
        st.error(f"❌ Error al descargar el wiring diagram: {e}")
    # Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=5)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(10, 10, "Fuel Cell & Battery System Performance Report", ln=0)
    if logo_path and os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=166, y=5, w=40)
        except Exception as e:
            st.warning(f"⚠️ No se pudo insertar el logo: {e}")
    pdf.ln(12)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 6, "System KPIs", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 6, f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 6, f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 6, f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 6, f"Battery Autonomy: {battery_hours:.1f} h", ln=True)
    pdf.cell(200, 6, f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(200, 6, f"Battery Charge Time: {charge_time:.1f} h", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 6, "Equipments Energy Summary", ln=True)
    pdf.set_font("Arial", size=10)
    for _, row in df[:-1].iterrows():
        pdf.cell(200, 6, f"{row['name']}: {row['power']}W x {row['hours']}h = {row['Energy (Wh)']:.0f}Wh | {row['Battery Capacity Used (Ah)']:.1f}Ah", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 6, "System Constants", ln=True)
    pdf.set_font("Arial", size=10)
    for i, row in constants_df.iterrows():
        pdf.cell(200, 6, f"{row['Parameter']}: {row['Value']}", ln=True)

    pdf.ln(4)
    pdf.image(tmp_batt.name, x=0, y=pdf.get_y(), w=110)
    pdf.image(tmp_eff.name, x=103, y=pdf.get_y(), w=110)


    pdf.ln(62)
    pdf.set_font("Arial", size=8)
    pdf.cell(200, 6, "The gauges show key metrics for system autonomy and energy conversion efficiency.", ln=True)

    # Insertar wiring diagram convertido
    if diagram_downloaded and os.path.exists(diagram_path):
        try:
            pdf.ln(10)
            pdf.image(diagram_path, x=110, y=110, w=90)
        except Exception as e:
            st.warning(f"⚠️ No se pudo insertar el wiring diagram en el PDF: {e}")

    pdf.ln(12)
    pdf.set_font("Arial","B", size=8)
    pdf.cell(200, 3, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Values strictly estimated for academic purposes", ln=True)
    pdf.cell(200, 3, "Coder: Victor Alvarez Melendez", ln=True)
    pdf.cell(200, 3, "Master Student in Hydrogen Technology", ln=True)
    pdf.cell(200, 3, "Technische Hochschule Rosenheim - Campus Burghausen", ln=True)
    pdf.cell(200, 35, "Thanks for using our App. Servus and enjoy your camping days in the Alps!.", ln=True)

    # Descargar PDF final
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    st.download_button("📥 Download PDF Report", data=pdf_bytes, file_name="kpi_report.pdf", mime="application/pdf")
