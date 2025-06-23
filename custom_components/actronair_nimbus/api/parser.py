import json
from dataclasses import dataclass
from typing import List, Any
from datetime import timedelta, datetime, timezone


@dataclass
class FirmwareVersions:
    indoor: str
    controller: str
    outdoor: str


@dataclass
class Outdoor:
    capacity: int
    chasing_temperature: float
    live_temperature: float
    mode: str
    pwm: int
    rpm: int
    defrost: bool
    drm: bool
    ambient_temperature: float
    coil_temperature: float
    power: int
    speed: int
    compressor_on: bool
    discharge_temperature: float
    reverse_valve_position: str
    model_number: str
    family: str


@dataclass
class CommonHumidityTemperature:
    humidity: float
    temperature: float


@dataclass
class Limits:
    min: int
    max: int


@dataclass
class Zone:
    title: str
    position: int
    humidity: float
    temperature: float
    connected: bool
    serial_number: str
    rssi: str
    battery: str
    temperature_setpoint_cool: float
    temperature_setpoint_heat: float


@dataclass
class VFT:
    airflow: int
    static_pressure: int
    max_static_pressure: int


@dataclass
class TouchScreen:
    last_touch_time: datetime
    controller_model: str
    screen_active: bool


@dataclass
class QuietMode:
    enabled: bool
    active: bool


@dataclass
class TemperatureSetpoints:
    cool: float
    heat: float
    variance: float


@dataclass
class LEDIndicators:
    wall_glow: bool
    on_off_button: bool


@dataclass
class ParsedData:
    """
    Data class to hold parsed data from JSON.
    """
    cloud_connected: str
    uptime: timedelta
    firmware_versions: FirmwareVersions
    outdoor: Outdoor
    common_humidity_temperature: CommonHumidityTemperature
    clean_filter: bool
    defrosting: bool
    fan_running: bool
    coil_inlet_temperature: float
    limits: Limits
    vft: VFT
    turbo_mode: bool
    away_mode: bool
    fan_mode: str
    quiet_mode: QuietMode
    last_status_update: datetime
    time_since_last_contact: str
    zones: List[Zone]
    touchscreen: TouchScreen
    master_wc_model: str
    indoor_model_number: str
    is_on: bool
    temperature_setpoints: TemperatureSetpoints
    system_name: str
    led_indicators: LEDIndicators
    mode: str

    @staticmethod
    def from_json(file_path: str) -> 'ParsedData':
        """
        Parse JSON file and return a ParsedData object.

        :param file_path: Path to the JSON file.
        :return: ParsedData object.
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        return ParsedData._parse_data(data)
    
    @staticmethod
    def from_state(state):
        status = {
            'isOnline': True,
            'timeSinceLastContact': '',
            'lastStatusUpdate': state._timestamp,
            'lastKnownState': state._state,
        }
        return ParsedData._parse_data(status)

    @staticmethod
    def _parse_data(data: dict) -> 'ParsedData':
        """
        Parse data dictionary and return a ParsedData object.

        :param data: Data dictionary.
        :return: ParsedData object.
        """
        # Get the aircon ID dynamically
        aircon_id = next(iter(data["lastKnownState"]))
        aircon_id_no_brackets = aircon_id.strip('<>')

        # Create a mapping of serial numbers to peripherals for quick lookup
        peripherals = {p["SerialNumber"]: p for p in data["lastKnownState"]["AirconSystem"]["Peripherals"]}

        zones = []
        for zone in data["lastKnownState"]["RemoteZoneInfo"]:
            if zone["NV_Exists"]:
                title = zone["NV_Title"]
                sensor_data = zone["Sensors"].get(aircon_id_no_brackets, {})
                serial_number = sensor_data.get("NV_Kind", "").split(": ")[-1]
                peripheral_data = peripherals.get(serial_number, {})
                battery = peripheral_data.get("RemainingBatteryCapacity_pc", "N/A")
                zones.append(Zone(
                    title=title,
                    position=zone["ZonePosition"],
                    humidity=zone["LiveHumidity_pc"],
                    temperature=zone["LiveTemp_oC"],
                    connected=sensor_data.get("Connected"),
                    serial_number=serial_number,
                    rssi=sensor_data.get("lastRssi"),
                    battery=battery,
                    temperature_setpoint_cool=zone["TemperatureSetpoint_Cool_oC"],
                    temperature_setpoint_heat=zone["TemperatureSetpoint_Heat_oC"]
                ))

        return ParsedData(
            cloud_connected=data["lastKnownState"][aircon_id]["Cloud"]["ConnectionState"],
            uptime=timedelta(seconds=data["lastKnownState"][aircon_id]["SystemStatus_Local"]["Uptime_s"]),
            firmware_versions=FirmwareVersions(
                indoor=data["lastKnownState"]["AirconSystem"]["IndoorUnit"]["IndoorFW"],
                controller=data["lastKnownState"][aircon_id]["SystemState"]["WCFirmwareVersion"],
                outdoor=data["lastKnownState"]["AirconSystem"]["OutdoorUnit"]["SoftwareVersion"]
            ),
            outdoor=Outdoor(
                capacity=data["lastKnownState"]["LiveAircon"]["CompressorCapacity"],
                chasing_temperature=data["lastKnownState"]["LiveAircon"]["CompressorChasingTemperature"],
                live_temperature=data["lastKnownState"]["LiveAircon"]["CompressorLiveTemperature"],
                mode=data["lastKnownState"]["LiveAircon"]["CompressorMode"],
                pwm=data["lastKnownState"]["LiveAircon"]["FanPWM"],
                rpm=data["lastKnownState"]["LiveAircon"]["FanRPM"],
                defrost=data["lastKnownState"]["LiveAircon"]["Defrost"],
                drm=data["lastKnownState"]["LiveAircon"]["DRM"],
                ambient_temperature=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["AmbTemp"],
                coil_temperature=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["CoilTemp"],
                power=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["CompPower"],
                speed=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["CompSpeed"],
                compressor_on=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["CompressorOn"],
                discharge_temperature=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["DischargeTemp"],
                reverse_valve_position=data["lastKnownState"]["LiveAircon"]["OutdoorUnit"]["ReverseValvePosition"],
                model_number=data["lastKnownState"]["AirconSystem"]["OutdoorUnit"]["ModelNumber"],
                family=data["lastKnownState"]["AirconSystem"]["OutdoorUnit"]["Family"]
            ),
            common_humidity_temperature=CommonHumidityTemperature(
                humidity=data["lastKnownState"]["MasterInfo"]["LiveHumidity_pc"],
                temperature=data["lastKnownState"]["MasterInfo"]["LiveTemp_oC"]
            ),
            clean_filter=data["lastKnownState"]["Alerts"]["CleanFilter"],
            defrosting=data["lastKnownState"]["Alerts"]["Defrosting"],
            fan_running=data["lastKnownState"]["LiveAircon"]["AmRunningFan"],
            coil_inlet_temperature=data["lastKnownState"]["LiveAircon"]["CoilInlet"],
            limits=Limits(
                min=data["lastKnownState"]["NV_Limits"]["UserSetpoint_oC"]["setCool_Min"],
                max=data["lastKnownState"]["NV_Limits"]["UserSetpoint_oC"]["setCool_Max"]
            ),
            vft=VFT(
                airflow=data["lastKnownState"]["UserAirconSettings"]["VFT"]["Airflow"],
                static_pressure=data["lastKnownState"]["UserAirconSettings"]["VFT"]["StaticPressure"],
                max_static_pressure=data["lastKnownState"]["UserAirconSettings"]["VFT"]["SelfLearn"]["MaxStaticPressure"]
            ),
            turbo_mode=data["lastKnownState"]["UserAirconSettings"]["TurboMode"]["Enabled"],
            away_mode=data["lastKnownState"]["UserAirconSettings"]["AwayMode"],
            fan_mode=data["lastKnownState"]["UserAirconSettings"]["FanMode"],
            quiet_mode=QuietMode(
                enabled=data["lastKnownState"]["UserAirconSettings"]["QuietModeEnabled"],
                active=data["lastKnownState"]["UserAirconSettings"]["QuietModeActive"]
            ),
            last_status_update=data["lastStatusUpdate"],
            time_since_last_contact=data["timeSinceLastContact"],
            zones=zones,
            touchscreen=TouchScreen(
                last_touch_time=datetime.fromisoformat(data["lastKnownState"][aircon_id]["SystemStatus_Local"]["TouchScreen"]["LastTouchTime"]).astimezone(timezone.utc),
                controller_model=data["lastKnownState"][aircon_id]["SystemStatus_Local"]["TouchScreen"]["ControllerModel"],
                screen_active=data["lastKnownState"][aircon_id]["SystemStatus_Local"]["GUI"]["ActiveScreen"] != "DISPLAY OFF"
            ),
            master_wc_model=data["lastKnownState"]["AirconSystem"]["MasterWCModel"],
            indoor_model_number=data["lastKnownState"]["AirconSystem"]["IndoorUnit"]["NV_ModelNumber"],
            is_on=data["lastKnownState"]["UserAirconSettings"]["isOn"],
            temperature_setpoints=TemperatureSetpoints(
                cool=data["lastKnownState"]["UserAirconSettings"]["TemperatureSetpoint_Cool_oC"],
                heat=data["lastKnownState"]["UserAirconSettings"]["TemperatureSetpoint_Heat_oC"],
                variance=data["lastKnownState"]["UserAirconSettings"]["ZoneTemperatureSetpointVariance_oC"]
            ),
            system_name=data["lastKnownState"]["NV_SystemSettings"]["SystemName"],
            led_indicators=LEDIndicators(
                wall_glow=data["lastKnownState"]["NV_SystemSettings"]["LEDIndicators"]["WallGlow"]["Enabled"],
                on_off_button=data["lastKnownState"]["NV_SystemSettings"]["LEDIndicators"]["OnOffButton"]["Enabled"]
            ),
            mode=data["lastKnownState"]["UserAirconSettings"]["Mode"]
        )
