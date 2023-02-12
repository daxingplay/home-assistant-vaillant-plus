"""Constants for vaillant-plus tests."""

from custom_components.vaillant_plus.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DID,
    CONF_TOKEN,
)

# Mock config data to be used across multiple tests
MOCK_USERNAME = "test_username"
MOCK_PASSWORD = "test_password"
MOCK_DID = "1"
MOCK_INPUT = {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD}
MOCK_CONFIG_ENTRY_DATA = {
    CONF_DID: MOCK_DID,
    CONF_TOKEN: "eyJhcHBfaWQiOiAiMSIsICJ1c2VybmFtZSI6ICJ0ZXN0X3VzZXJuYW1lIiwgInBhc3N3b3JkIjogInRlc3RfcGFzc3dvcmQiLCAidG9rZW4iOiAidGVzdF90b2tlbiIsICJ1aWQiOiAidTEifQ==",
}
MOCK_DEVICE_ATTRS_WHEN_CONNECT = {
    "Brand": "vaillant on desk",
    "Time_slot_type": "CH",
    "Heating_System_Setting": "radiator",
    "DHW_Function": "none",
    "Mode_Setting_DHW": "Cruising",
    "Mode_Setting_CH": "Cruising",
    "Weather_compensation": True,
    "BMU_Platform": True,
    "Enabled_DHW": True,
    "Enabled_Heating": False,
    "WarmStar_Tank_Loading_Enable": True,
    "Heating_Enable": False,
    "Circulation_Enable": False,
    "Heating_Curve": 1,
    "Max_NumBer_Of_Timeslots_DHW": 0,
    "Slot_current_DHW": 0,
    "Max_NumBer_Of_Timeslots_CH": 0,
    "Slot_current_CH": 0,
    "Room_Temperature_Setpoint_Comfort": 1,
    "Room_Temperature_Setpoint_ECO": 15,
    "Outdoor_Temperature": 1,
    "Room_Temperature": 20.5,
    "DHW_setpoint": 45,
    "Lower_Limitation_of_CH_Setpoint": 30,
    "Upper_Limitation_of_CH_Setpoint": 75,
    "Lower_Limitation_of_DHW_Setpoint": 35,
    "Upper_Limitation_of_DHW_Setpoint": 65,
    "Current_DHW_Setpoint": 45,
    "RF_Status": 3,
    "Flow_Temperature_Setpoint": 0,
    "Flow_temperature": 26,
    "return_temperature": 0,
    "DSN": 1500,
    "Tank_temperature": 127.5,
}

MOCK_DEVICE_ATTRS_WHEN_UPDATE = {
    "Brand": "vaillant on desk",
    "Time_slot_type": "CH",
    "Heating_System_Setting": "radiator",
    "DHW_Function": "none",
    "Mode_Setting_DHW": "Cruising",
    "Mode_Setting_CH": "Cruising",
    "Weather_compensation": True,
    "BMU_Platform": True,
    "Enabled_DHW": True,
    "Enabled_Heating": True,
    "WarmStar_Tank_Loading_Enable": True,
    "Heating_Enable": True,
    "Circulation_Enable": False,
    "Heating_Curve": 1,
    "Max_NumBer_Of_Timeslots_DHW": 0,
    "Slot_current_DHW": 0,
    "Max_NumBer_Of_Timeslots_CH": 0,
    "Slot_current_CH": 0,
    "Room_Temperature_Setpoint_Comfort": 18.5,
    "Room_Temperature_Setpoint_ECO": 15,
    "Outdoor_Temperature": 10,
    "Room_Temperature": 11.5,
    "DHW_setpoint": 46,
    "Lower_Limitation_of_CH_Setpoint": 30,
    "Upper_Limitation_of_CH_Setpoint": 75,
    "Lower_Limitation_of_DHW_Setpoint": 35,
    "Upper_Limitation_of_DHW_Setpoint": 65,
    "Current_DHW_Setpoint": 46,
    "RF_Status": 3,
    "Flow_Temperature_Setpoint": 0,
    "Flow_temperature": 75,
    "return_temperature": 0,
    "DSN": 1500,
    "Tank_temperature": 127.5,
}

CONF_HOST = "https://appapi.vaillant.com.cn"
CONF_HOST_API = "https://api.vaillant.com.cn"
