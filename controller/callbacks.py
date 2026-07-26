import sys
from datetime import datetime
from typing import Dict, List, Optional

ENERGYPLUS_PATH = r"C:\EnergyPlusV26-1-0"
sys.path.insert(0, ENERGYPLUS_PATH)

from pyenergyplus.api import EnergyPlusAPI


class BuildingCallbacks:

    def __init__(self, data_logger=None, controller=None):
        self.api = EnergyPlusAPI()
        self.data_logger = data_logger
        self.controller = controller

        self.zone_temp_handle = -1
        self.outdoor_temp_handle = -1
        self.initialized = False
        self.fan_power_handle = -1
        self.chiller_power_handle = -1
        self.pump_power_handle = -1
        self.hvac_power_handle = -1
        self.cooling_rate_handle = -1
        self.heating_rate_handle = -1

        # Actuator handles for control
        self.cooling_setpoint_handle = -1
        self.heating_setpoint_handle = -1

        # Current simulation time
        self.current_time = 0

    def callback(self, state):

        if not self.initialized:

            # Try different zone names for 5ZoneAirCooled building
            zone_names = ["SPACE1-1", "SPACE2-1", "SPACE3-1", "SPACE4-1", "SPACE5-1", "PLENUM-1"]
            for zone_name in zone_names:
                self.zone_temp_handle = self.api.exchange.get_variable_handle(
                    state,
                    "Zone Mean Air Temperature",
                    zone_name
                )
                if self.zone_temp_handle >= 0:
                    print(f"Found zone: {zone_name}")
                    self.zone_name = zone_name
                    break

            self.outdoor_temp_handle = self.api.exchange.get_variable_handle(
                state,
                "Site Outdoor Air Drybulb Temperature",
                "Environment"
            )

            # Try different fan names for 5ZoneAirCooled building
            fan_names = ["Supply Fan 1", "Main Supply Fan", "Fan"]
            for fan_name in fan_names:
                self.fan_power_handle = self.api.exchange.get_variable_handle(
                    state,
                    "Fan Electricity Rate",
                    fan_name
                )
                if self.fan_power_handle >= 0:
                    print(f"Found fan: {fan_name}")
                    break

            # Try different chiller names for 5ZoneAirCooled building
            chiller_names = ["Central Chiller", "Chiller", "Chiller 1"]
            for chiller_name in chiller_names:
                self.chiller_power_handle = self.api.exchange.get_variable_handle(
                    state,
                    "Chiller Electricity Rate",
                    chiller_name
                )
                if self.chiller_power_handle >= 0:
                    print(f"Found chiller: {chiller_name}")
                    break

            # Try different pump names for 5ZoneAirCooled building
            pump_names = ["CW Circ Pump", "Pump", "Condenser Water Pump"]
            for pump_name in pump_names:
                self.pump_power_handle = self.api.exchange.get_variable_handle(
                    state,
                    "Pump Electricity Rate",
                    pump_name
                )
                if self.pump_power_handle >= 0:
                    print(f"Found pump: {pump_name}")
                    break

            self.cooling_rate_handle = self.api.exchange.get_variable_handle(
                state,
                "Cooling Coil Total Cooling Rate",
                "Main Cooling Coil 1"
            )

            self.heating_rate_handle = self.api.exchange.get_variable_handle(
                state,
                "Heating Coil Heating Rate",
                "Main Heating Coil 1"
            )

            self.hvac_power_handle = self.api.exchange.get_variable_handle(
                state,
                "Facility Total HVAC Electricity Demand Rate",
                "Environment"
            )

            # Get actuator handles for setpoint control
            if hasattr(self, 'zone_name'):
                self.cooling_setpoint_handle = self.api.exchange.get_actuator_handle(
                    state,
                    "Zone Temperature Control",
                    "Cooling Setpoint",
                    self.zone_name
                )

                self.heating_setpoint_handle = self.api.exchange.get_actuator_handle(
                    state,
                    "Zone Temperature Control",
                    "Heating Setpoint",
                    self.zone_name
                )

            print("Zone Handle         :", self.zone_temp_handle)
            print("Outdoor Handle      :", self.outdoor_temp_handle)
            print("Fan Handle          :", self.fan_power_handle)
            print("Chiller Handle      :", self.chiller_power_handle)
            print("Pump Handle         :", self.pump_power_handle)
            print("HVAC Handle         :", self.hvac_power_handle)
            print("Cooling Handle      :", self.cooling_rate_handle)
            print("Heating Handle      :", self.heating_rate_handle)
            print("Cooling Setpoint    :", self.cooling_setpoint_handle)
            print("Heating Setpoint    :", self.heating_setpoint_handle)

            self.initialized = True

        if self.zone_temp_handle >= 0 and self.outdoor_temp_handle >= 0:

            # Get current simulation time
            self.current_time = self.api.exchange.current_time(state)

            # Collect sensor data
            zone_temp = self.api.exchange.get_variable_value(
                state,
                self.zone_temp_handle
            )

            outdoor_temp = self.api.exchange.get_variable_value(
                state,
                self.outdoor_temp_handle
            )

            fan_power = 0.0
            if self.fan_power_handle >= 0:
                fan_power = self.api.exchange.get_variable_value(
                    state,
                    self.fan_power_handle
                )

            chiller_power = 0.0
            if self.chiller_power_handle >= 0:
                chiller_power = self.api.exchange.get_variable_value(
                    state,
                    self.chiller_power_handle
                )

            pump_power = 0.0
            if self.pump_power_handle >= 0:
                pump_power = self.api.exchange.get_variable_value(
                    state,
                    self.pump_power_handle
                )

            hvac_power = 0.0
            if self.hvac_power_handle >= 0:
                hvac_power = self.api.exchange.get_variable_value(
                    state,
                    self.hvac_power_handle
                )

            cooling = 0.0
            if self.cooling_rate_handle >= 0:
                cooling = self.api.exchange.get_variable_value(
                    state,
                    self.cooling_rate_handle
                )

            heating = 0.0
            if self.heating_rate_handle >= 0:
                heating = self.api.exchange.get_variable_value(
                    state,
                    self.heating_rate_handle
                )

            # Create data dictionary
            sensor_data = {
                'timestamp': self.current_time,
                'zone_temp': zone_temp,
                'outdoor_temp': outdoor_temp,
                'fan_power': fan_power,
                'chiller_power': chiller_power,
                'pump_power': pump_power,
                'hvac_power': hvac_power,
                'cooling_rate': cooling,
                'heating_rate': heating
            }

            # Log data if logger is available
            if self.data_logger:
                self.data_logger.log_data(sensor_data)

            # Get control actions from controller if available
            control_actions = None
            if self.controller:
                control_actions = self.controller.compute_control_actions(sensor_data)

                # Apply control actions
                if control_actions and self.cooling_setpoint_handle >= 0:
                    if 'cooling_setpoint' in control_actions:
                        self.api.exchange.set_actuator_value(
                            state,
                            self.cooling_setpoint_handle,
                            control_actions['cooling_setpoint']
                        )

                    if 'heating_setpoint' in control_actions and self.heating_setpoint_handle >= 0:
                        self.api.exchange.set_actuator_value(
                            state,
                            self.heating_setpoint_handle,
                            control_actions['heating_setpoint']
                        )

            print(
                f"""
    Indoor Temp : {zone_temp:.2f} °C
    Outdoor Temp: {outdoor_temp:.2f} °C

    Fan Power   : {fan_power:.2f} W
    Chiller     : {chiller_power:.2f} W
    Pump        : {pump_power:.2f} W
    HVAC Total  : {hvac_power:.2f} W

    Cooling     : {cooling:.2f} W
    Heating     : {heating:.2f} W
    """
            )

            if control_actions:
                print(f"Control Actions: {control_actions}")