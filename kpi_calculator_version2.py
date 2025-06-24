# kpi_calculator.py
from typing import List, Dict

# Constants
METHANOL_CONSUMPTION_PER_KWH = 0.9  # liters per kWh for EFOY Pro 2800
BATTERY_CAPACITY_AH = 105
BATTERY_VOLTAGE = 12.8  # V
BATTERY_CAPACITY_WH = BATTERY_CAPACITY_AH * BATTERY_VOLTAGE
FUEL_CELL_OUTPUT_W = 125  # constant power output
FUEL_CELL_EFFICIENCY = 0.35  # typical value
METHANOL_ENERGY_DENSITY = 5.5 / 5  # approx. 1.1 kWh/l
BATTERY_EFFICIENCY = 0.90  # lithium battery round-trip efficiency (90%)

def calculate_daily_energy_demand(appliances: List[Dict]) -> float:
    return sum(app['power'] * app['hours'] for app in appliances)  # Wh

def calculate_methanol_consumption(energy_wh: float) -> float:
    return (energy_wh / 1000) * METHANOL_CONSUMPTION_PER_KWH

def calculate_tank_autonomy(liters_available: float, daily_consumption_l: float) -> float:
    if daily_consumption_l == 0:
        return float('inf')
    return liters_available / daily_consumption_l

def battery_discharge_time(energy_wh: float) -> float:
    if energy_wh == 0:
        return float('inf')
    return BATTERY_CAPACITY_WH / energy_wh * 24  # convert to hours assuming daily energy demand

def fuel_cell_efficiency(useful_energy_kwh: float, methanol_used_l: float) -> float:
    if methanol_used_l == 0:
        return 0
    chemical_energy = methanol_used_l * METHANOL_ENERGY_DENSITY  # kWh
    return useful_energy_kwh / chemical_energy

def peak_load_coverage(peak_power_w: float) -> float:
    peak_current = peak_power_w / BATTERY_VOLTAGE
    if peak_current <= 200:  # peak battery limit
        return 100.0
    return round((200 * BATTERY_VOLTAGE) / peak_power_w * 100, 1)

def global_system_efficiency(battery_energy_wh: float, fuel_cell_energy_wh: float, methanol_used_l: float) -> float:
    """
    Eficiencia global del sistema: energía útil real entregada al sistema
    incluyendo pérdidas por batería, dividida por la energía química del metanol.
    """
    if methanol_used_l == 0:
        return 0.0

    # Energía útil neta considerando eficiencia de batería (kWh)
    net_energy_kwh = (fuel_cell_energy_wh / 1000) * BATTERY_EFFICIENCY

    # Energía química total disponible a partir del metanol (kWh)
    chemical_energy_kwh = methanol_used_l * METHANOL_ENERGY_DENSITY

    return net_energy_kwh / chemical_energy_kwh

def battery_charge_time_needed(energy_to_charge_wh: float, fuel_cell_output_w: float = FUEL_CELL_OUTPUT_W) -> float:
    return energy_to_charge_wh / fuel_cell_output_w

def system_efficiency(energy_delivered_kwh: float, methanol_liters: float) -> float:
    if methanol_liters == 0:
        return 0.0
    chemical_energy_kwh = methanol_liters * METHANOL_ENERGY_DENSITY
    return energy_delivered_kwh / chemical_energy_kwh