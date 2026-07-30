import network
import time
import ujson
from machine import Pin, PWM, SoftI2C
from umqtt.simple import MQTTClient
from i2c_lcd import I2cLcd

# Configuration

WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ESP32_MicroPython_EntryExit"
SUB_TOPIC = b"iot/car_parking/slot/set"
PUB_TOPIC = b"iot/car_parking/status"

# Hardware Setup

led_green = Pin(18, Pin.OUT)
led_red = Pin(19, Pin.OUT)

btn_entry = Pin(16, Pin.IN, Pin.PULL_UP)
btn_exit = Pin(17, Pin.IN, Pin.PULL_UP)

servo_pwm = PWM(Pin(15), freq=50)

def set_barrier_angle(angle):
    duty = int(26 + (angle / 90.0) * 51)
    servo_pwm.duty(duty)

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
I2C_ADDR = 0x27
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# Setting Slots to 0 (1 = Occupied)
slots = {1: 0, 2: 0, 3: 0, 4: 0}

def update_system_state(client, event_msg=None, force_open_gate=False):
    occupied_count = sum(slots.values())
    available_count = 4 - occupied_count

    lcd.clear()

    if force_open_gate:
        set_barrier_angle(90)
        led_green.value(1)
        led_red.value(0)

    elif occupied_count == 4:
        set_barrier_angle(0)
        led_green.value(0)
        led_red.value(1)
        
    else:
        set_barrier_angle(0)
        led_green.value(1)
        led_red.value(0)

    # LCD Writings
    status_str = "PARKING FULL" if occupied_count == 4 else "AVAILABLE"

    lcd.move_to(0, 0)
    if event_msg:
        lcd.putstr(event_msg)
    elif occupied_count == 4:
        lcd.putstr("PARKING FULL!")
    else:
        lcd.putstr(f"Free Slots: {available_count}/4")

    lcd.move_to(0, 1)
    lcd.putstr("Gate: OPEN" if force_open_gate else "Gate: CLOSED")

    # Publish status payload to MQTT/Node-RED
    payload = {
        "slot1": "Occupied" if slots[1] else "Free",
        "slot2": "Occupied" if slots[2] else "Free",
        "slot3": "Occupied" if slots[3] else "Free",
        "slot4": "Occupied" if slots[4] else "Free",
        "occupied": occupied_count,
        "available": available_count,
        "status": status_str
    }

    json_payload = ujson.dumps(payload)
    print("Publishing State Update:", json_payload)
    client.publish(PUB_TOPIC, json_payload)

# Entry/Exit

def handle_entry(client):

    for s in range(1, 5):
        if slots[s] == 0:
            slots[s] = 1
            print(f"Entry Triggered: Allocated Slot {s}")
            
            update_system_state(client, event_msg="CAR ENTERED", force_open_gate=True)
            time.sleep(2)
            
            update_system_state(client)
            return

    # In Full Case
    print("Entry Rejected: Parking Full")
    update_system_state(client, event_msg="FULL! NO ENTRY")

def handle_exit(client):

    for s in range(4, 0, -1):
        if slots[s] == 1:
            slots[s] = 0
            print(f"Exit Triggered: Freed Slot {s}")

            update_system_state(client, event_msg="CAR EXITED", force_open_gate=True)
            time.sleep(2)
            
            update_system_state(client)
            return

    print("Exit Triggered: Parking already empty")

# MQTT Callback
def mqtt_callback(topic, msg):
    print(f"Received MQTT Command: {msg.decode()}")
    try:
        data = ujson.loads(msg)
        slot_num = data.get("slot")
        state = data.get("state")

        if slot_num in slots and state in (0, 1):
            slots[slot_num] = state
            update_system_state(client)
    except Exception as e:
        print("Error parsing MQTT command:", e)

# Wi Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi", end="")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("\nWi-Fi Connected")

def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(mqtt_callback)
    print("Connecting to MQTT Broker")
    client.connect()
    client.subscribe(SUB_TOPIC)
    print(f"Subscribed")
    return client

#Sterting the Conncectuions
connect_wifi()
client = connect_mqtt()

update_system_state(client)

last_entry_press = 0
last_exit_press = 0

print("System is ready\nPress ENTRY or EXIT buttons")

while True:
    try:
        client.check_msg()

        # Check Entry Button
        if btn_entry.value() == 0 and (time.ticks_ms() - last_entry_press > 1000):
            last_entry_press = time.ticks_ms()
            handle_entry(client)

        # Check Exit Button
        if btn_exit.value() == 0 and (time.ticks_ms() - last_exit_press > 1000):
            last_exit_press = time.ticks_ms()
            handle_exit(client)

        time.sleep(0.05)
    except Exception as e:
        print("Error in loop, reconnecting MQTT...", e)
        time.sleep(2)
        client = connect_mqtt()