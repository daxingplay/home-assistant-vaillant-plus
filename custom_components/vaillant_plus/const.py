"""Constants for the Vaillant Plus integration."""

DOMAIN = "vaillant_plus"
API_CLIENT = "client"
DISPATCHERS = "dispatchers"


CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_TOKEN = "token"
CONF_DID = "did"
CONF_UID = "uid"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_MAC = "mac"
CONF_PRODUCT_NAME = "product_name"
CONF_GAS_UNIT = "gas_unit"
CONF_GAS_CALORIFIC_VALUE = "gas_calorific_value"

GAS_UNIT_KWH = "kwh"
GAS_UNIT_CUBIC_METERS = "m3"
DEFAULT_GAS_UNIT = GAS_UNIT_KWH
# kWh per m³. Typical for natural gas; the supplier's bill gives the local figure.
DEFAULT_GAS_CALORIFIC_VALUE = 10.0

EVT_DEVICE_CONNECTED = "vaillant_plus_device.{}.connected"
EVT_DEVICE_UPDATED = "vaillant_plus_device.{}.updated"
EVT_TOKEN_UPDATED = "vaillant_plus_token.{}.updated"

WATER_HEATER_ON = "on"
WATER_HEATER_OFF = "off"
