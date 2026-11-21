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
# Set once a gateway reports `indoor_temperature` as 255: no room sensor.
CONF_NO_ROOM_SENSOR = "no_room_sensor"

EVT_DEVICE_CONNECTED = "vaillant_plus_device.{}.connected"
EVT_DEVICE_UPDATED = "vaillant_plus_device.{}.updated"
EVT_TOKEN_UPDATED = "vaillant_plus_token.{}.updated"

WATER_HEATER_ON = "on"
WATER_HEATER_OFF = "off"
