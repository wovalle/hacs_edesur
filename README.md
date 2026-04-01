# Edesur - Home Assistant Integration

Custom Home Assistant integration for [Edesur](https://ov.edesur.com.do) (Dominican Republic) electricity consumption monitoring.

Fetches daily and monthly electricity consumption data from Edesur's Oficina Virtual API.

## Sensors

| Sensor | Description | Unit |
|---|---|---|
| Monthly Total | Total kWh consumed this billing period (includes `daily_history` attribute) | kWh |
| Daily Consumption | Last day's consumption | kWh |
| Daily Average | Average daily consumption | kWh |
| Weekday Average | Average weekday consumption | kWh |
| Weekend Average | Average weekend consumption | kWh |
| Current Bill Consumption | Current (in-progress) billing cycle consumption | kWh |
| Current Bill Amount | Current (in-progress) billing cycle amount | DOP |
| Last Bill Consumption | Last completed bill's total consumption | kWh |
| Last Bill Amount | Last completed bill's amount | DOP |

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots menu → **Custom repositories**
4. Add `https://github.com/wovalle/hacs_edesur` with category **Integration**
5. Search for "Edesur" and install
6. Restart Home Assistant

### Manual

1. Copy `custom_components/edesur/` to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Edesur**
3. Enter your Oficina Virtual credentials:
   - **Username**: Your Edesur Oficina Virtual username
   - **Password**: Your password
   - **Contract Number (NIC)**: Your contract/NIC number (found on your bill)

## Daily Consumption Chart

The **Monthly Total** sensor includes a `daily_history` attribute with daily kWh data for the current billing period. To visualize it as a bar chart:

### Prerequisites

Install [ApexCharts Card](https://github.com/RomRider/apexcharts-card) via HACS (Frontend section).

### Dashboard Card

Add a Manual card with this YAML:

```yaml
type: custom:apexcharts-card
header:
  title: Daily Consumption (kWh)
  show: true
graph_span: 31d
span:
  end: now
series:
  - entity: sensor.edesur_7405433_monthly_total
    type: column
    data_generator: |
      const history = entity.attributes.daily_history || [];
      return history.map(d => [new Date(d.date).getTime(), d.kwh]);
    name: kWh
    color: "#f9a825"
```

> Replace `7405433` with your NIC if different.

## Requirements

- An active Edesur account at [ov.edesur.com.do](https://ov.edesur.com.do)
- A smart meter (telemedido) installed at your property

## Data refresh

Consumption data is fetched every 6 hours. Edesur typically updates daily consumption with a 1-day delay.
