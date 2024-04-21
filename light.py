import json
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Light, LightInfo
from paho.mqtt.client import Client, MQTTMessage

# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host="homeassistant.lan", username="Kevin", password="Kevin629")

# Information about the light
light_info = LightInfo(
    name="Staircase Lighting",
    brightness=True,
    color_mode=True,
    supported_color_modes=["rgb"],
    effect=True,
    effect_list=["blink", "my_cusom_effect"])

settings = Settings(mqtt=mqtt_settings, entity=light_info)

# To receive state commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):

    # Make sure received payload is json
    try:
        payload = json.loads(message.payload.decode())
    except ValueError as error:
        print("Ony JSON schema is supported for light entities!")
        return

    # Parse received dictionary
    if "color" in payload:
        # set_color_of_my_light()
        my_light.color("rgb", payload["color"])
    elif "brightness" in payload:
        # set_brightness_of_my_light()
        my_light.brightness(payload["brightness"])
    elif "effect" in payload:
        # set_effect_of_my_light()
        my_light.effect(payload["effect"])
    elif "state" in payload:
        if payload["state"] == light_info.payload_on:
            # turn_on_my_light()
            my_light.on()
        else:
            # turn_off_my_light()
            my_light.off()
    else:
        print("Unknown payload")

# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Instantiate the switch
my_light = Light(settings, my_callback, user_data)

# Set the initial state of the light, which also makes it discoverable
my_light.off()