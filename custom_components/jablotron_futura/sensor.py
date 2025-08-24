from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, UnitOfPower, CONCENTRATION_PARTS_PER_MILLION, UnitOfVolumeFlowRate

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaSimpleSensor(FuturaEntity, SensorEntity):
    def __init__(self, coordinator: FuturaCoordinator, key: str, name: str, unit: str | None = None, device_class=None, icon: str | None = None, state_class=None):
        super().__init__(coordinator, name, key)
        self.key = key
        if unit is not None:
            self._attr_native_unit_of_measurement = unit
        if device_class is not None:
            self._attr_device_class = device_class
        if icon is not None:
            self._attr_icon = icon
        if state_class is not None:
            self._attr_state_class = state_class

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key)


async def async_setup_entry(hass, entry, async_add_entities):
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]

    ents = []

    # Temperatures
    ents.append(FuturaSimpleSensor(coord, "temp_outdoor", "Teplota venku", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
    ents.append(FuturaSimpleSensor(coord, "temp_supply",  "Teplota do domu", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
    ents.append(FuturaSimpleSensor(coord, "temp_extract", "Teplota z domu", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
    ents.append(FuturaSimpleSensor(coord, "temp_exhaust", "Teplota odtah", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
    ents.append(FuturaSimpleSensor(coord, "temp_outdoor_ntc", "Teplota NTC venku", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))

    # Humidity
    for k, n in (("humi_outdoor","Vlhkost venku"),("humi_supply","Vlhkost do domu"),("humi_extract","Vlhkost z domu"),("humi_exhaust","Vlhkost odtah"),("alfa_humi_1","ALFA – vlhkost")):
        ents.append(FuturaSimpleSensor(coord, k, n, PERCENTAGE, SensorDeviceClass.HUMIDITY))

    # ALFA
    ents.append(FuturaSimpleSensor(coord, "alfa_temp_1", "ALFA – teplota", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
    ents.append(FuturaSimpleSensor(coord, "alfa_co2_1", "ALFA – CO₂", CONCENTRATION_PARTS_PER_MILLION))

    # Performance
    ents.append(FuturaSimpleSensor(coord, "filter_wear", "Zanesení filtrů", PERCENTAGE))
    ents.append(FuturaSimpleSensor(coord, "power", "Příkon", UnitOfPower.WATT))
    ents.append(FuturaSimpleSensor(coord, "heat_recovering", "Zpětně získávané teplo", UnitOfPower.WATT))
    ents.append(FuturaSimpleSensor(coord, "heating_power", "Výkon topení dohřevu", UnitOfPower.WATT))
    ents.append(FuturaSimpleSensor(coord, "air_flow", "Vzduchové množství", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR))

    # Config / helpers
    ents.append(FuturaSimpleSensor(coord, "mode_raw", "Režim (raw)"))
    ents.append(FuturaSimpleSensor(coord, "mode_text", "Režim větrání (text)"))
    ents.append(FuturaSimpleSensor(coord, "temp_set_raw", "Požadovaná teplota (raw)", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
    ents.append(FuturaSimpleSensor(coord, "humi_set_raw", "Požadovaná vlhkost (raw)", PERCENTAGE, SensorDeviceClass.HUMIDITY))

    # Times
    ents.append(FuturaSimpleSensor(coord, "boost_remaining_s", "Boost – zbývá (s)"))
    ents.append(FuturaSimpleSensor(coord, "boost_remaining_min", "Boost – zbývá (min)"))
    ents.append(FuturaSimpleSensor(coord, "circulation_remaining_s", "Cirkulace – zbývá (s)"))
    ents.append(FuturaSimpleSensor(coord, "circulation_remaining_min", "Cirkulace – zbývá (min)"))
    ents.append(FuturaSimpleSensor(coord, "night_remaining_s", "Noc – zbývá (s)"))
    ents.append(FuturaSimpleSensor(coord, "night_remaining_h", "Noc – zbývá (h)"))
    ents.append(FuturaSimpleSensor(coord, "party_remaining_s", "Party – zbývá (s)"))
    ents.append(FuturaSimpleSensor(coord, "party_remaining_h", "Party – zbývá (h)"))
    ents.append(FuturaSimpleSensor(coord, "overpressure_remaining_s", "Přetlak – zbývá (s)"))
    ents.append(FuturaSimpleSensor(coord, "away_begin_ts", "Dovolená – začátek (unix)"))
    ents.append(FuturaSimpleSensor(coord, "away_end_ts", "Dovolená – konec (unix)"))
    ents.append(FuturaSimpleSensor(coord, "away_begin_text", "Dovolená – začátek"))
    ents.append(FuturaSimpleSensor(coord, "away_end_text", "Dovolená – konec"))

    async_add_entities(ents, True)
