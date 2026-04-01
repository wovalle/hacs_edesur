"""Sensor platform for Edesur."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EdesurCoordinator

SENSORS: list[tuple[str, str, str, str | None, str | None, str | None]] = [
    # (key, name, icon, unit, device_class, state_class)
    ("month_total_kwh", "Monthly Total", "mdi:flash", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    ("last_day_kwh", "Daily Consumption", "mdi:flash", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    ("daily_avg_kwh", "Daily Average", "mdi:chart-line", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    ("weekday_avg_kwh", "Weekday Average", "mdi:chart-line", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    ("weekend_avg_kwh", "Weekend Average", "mdi:chart-line", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    ("current_bill_kwh", "Current Bill Consumption", "mdi:receipt-text-clock", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    ("current_bill_amount", "Current Bill Amount", "mdi:currency-usd", "DOP", None, SensorStateClass.MEASUREMENT),
    ("last_bill_kwh", "Last Bill Consumption", "mdi:receipt-text-check", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    ("last_bill_amount", "Last Bill Amount", "mdi:currency-usd", "DOP", None, SensorStateClass.MEASUREMENT),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Edesur sensors from a config entry."""
    coordinator: EdesurCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EdesurSensor(coordinator, entry, key, name, icon, unit, device_class, state_class)
        for key, name, icon, unit, device_class, state_class in SENSORS
    ]
    async_add_entities(entities)


class EdesurSensor(CoordinatorEntity[EdesurCoordinator], SensorEntity):
    """Representation of an Edesur sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EdesurCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        unit: str | None,
        device_class: str | None,
        state_class: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": f"Edesur ({entry.unique_id})",
            "manufacturer": "Edesur",
            "model": "Smart Meter",
        }

    @property
    def native_value(self):
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        if self.coordinator.data is None:
            return None
        if self._key == "last_day_kwh":
            return {"date": self.coordinator.data.get("last_day_date")}
        if self._key == "month_total_kwh":
            return {"daily_history": self.coordinator.data.get("daily_history", [])}
        return None
