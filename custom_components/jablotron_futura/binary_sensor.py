from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaBitBinarySensor(FuturaEntity, BinarySensorEntity):
    def __init__(self, coordinator: FuturaCoordinator, source_key: str, bit: int, name: str, icon: str | None = None):
        super().__init__(coordinator, name, f"{source_key}_bit_{bit}")
        self.source_key = source_key
        self.bit = bit
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        if icon:
            self._attr_icon = icon

    @property
    def is_on(self):
        raw = int(self.coordinator.data.get(self.source_key, 0) or 0)
        return ((raw >> self.bit) & 1) == 1


class FuturaDerivedBinary(FuturaEntity, BinarySensorEntity):
    def __init__(self, coordinator: FuturaCoordinator, name: str, key: str):
        super().__init__(coordinator, name, key)
        self.key = key
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self.key, 0))


async def async_setup_entry(hass, entry, async_add_entities):
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]

    ents = []
    # Any error/warning summary
    ents.append(FuturaDerivedBinary(coord, "Futura – je nějaká chyba", "errors_bits_raw"))
    ents.append(FuturaDerivedBinary(coord, "Futura – je nějaké varování", "warnings_bits_raw"))

    # Error bits 0..12
    error_names = {
        0: "Chyba senzoru (ambient)",
        1: "Chyba senzoru (indoor)",
        2: "Chyba senzoru (fresh)",
        3: "Chyba senzoru (waste)",
        4: "Chyba přívodního ventilátoru",
        5: "Chyba odtahového ventilátoru",
        6: "Chyba komunikace s výměníkem",
        7: "Chyba polohy klapek výměníku",
        8: "Chyba komunikace s IO deskou",
        9: "Zablokovaný přívodní ventilátor",
        10: "Zablokovaný odtahový ventilátor",
        11: "Chyba komunikace s CoolBreeze",
        12: "Chyba venkovní jednotky CoolBreeze",
    }
    for b, n in error_names.items():
        ents.append(FuturaBitBinarySensor(coord, "errors_bits_raw", b, n))

    # Warning bits 0..31
    warn_names = {
        0: "Neinicializovaný filtr",
        1: "Filtr je příliš zanesený",
        2: "Filtr se používá příliš dlouho",
        3: "Nízké napětí RTC baterie",
        4: "Příliš vysoké otáčky přívodního ventilátoru",
        5: "Příliš vysoké otáčky odtahového ventilátoru",
        8: "Příliš nízká venkovní teplota",
        9: "Nesprávná konfigurace zón – přívod",
        10: "Nesprávná konfigurace zón – odtah",
        11: "Nouzové vypnutí",
        12: "Chyba komunikace se SuperBreeze",
        13: "Obecná chyba SuperBreeze",
        # Others undocumented
    }
    for b in range(0, 32):
        name = warn_names.get(b, f"Varování – bit {b} (nezadokumentováno)")
        ents.append(FuturaBitBinarySensor(coord, "warnings_bits_raw", b, name))

    # Antiradon active (from raw inverted in your YAML: raw==0 -> active)
    class AntiRadonBinary(FuturaEntity, BinarySensorEntity):
        def __init__(self, coordinator: FuturaCoordinator):
            super().__init__(coordinator, "Protiradon – aktivní", "antiradon_active")

        @property
        def is_on(self):
            # YAML: state: "{{ states('sensor.futura_antiradon_raw')|int(0) == 0 }}"
            return int(self.coordinator.data.get("antiradon_raw", 1)) == 0

        @property
        def device_class(self):
            return BinarySensorDeviceClass.PROBLEM

    ents.append(AntiRadonBinary(coord))

    async_add_entities(ents, True)
