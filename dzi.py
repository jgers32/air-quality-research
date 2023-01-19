#pm2.5 sensor libraries
import time
import board
import serial
import adafruit_sgp30
from adafruit_pm25.uart import PM25_UART
#sgp30 libraries
import busio
import adafruit_sgp30
import requests
import datetime

# TODO: All of these config values should be read from a config file
config_interval = 60
config_read_pm = True
config_read_voc = False

print("Starting DZI Service")

# Setup sgp30 sensor
if config_read_voc:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
    sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
    sgp30.iaq_init()
    

    # Print out startup info
    print("SGP30 serial #", [hex(i) for i in sgp30.serial])


def get_pm_data():

    # Setup PM sensor
    uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=0.25)
    pm25 = PM25_UART(uart, None)

    print("Read PM data")

    reading_count = 0

    while True:
        time.sleep(1)

        try:
            aqdata = pm25.read()
            #print(aqdata)
        except RuntimeError:
            print("Unable to read from PM sensor, retrying...")
            continue

        return aqdata


def warmup():
    for i in range(100):
        aqdata = get_pm_data()
        time.sleep(0.1)


def dump_sensor_data(aqdata):
    now = datetime.datetime.now()
    print("%s\tPM 1.0: %d\tPM2.5: %d\tPM10: %d" % (now.strftime('%Y-%m-%d %H:%M:%S'), aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"]))
    if config_read_voc:
        print("%s\teCO2 = %d ppm \t TVOC = %d ppb" % (now.strftime('%Y-%m-%d %H:%M:%S'), sgp30.eCO2, sgp30.TVOC))

def post_data(aqdata):
    print("Sending Data")
    try:
        json_data = {"sensor_id" : 5,
                     "pm25": aqdata["pm25 env"],
                     "pm1" : aqdata["pm10 env"],
                     "pm10": aqdata["pm100 env"]
                     }

        if config_read_voc:
            json_data["tvoc"] = sgp30.TVOC
            json_data["eco2"] = sgp30.eCO2

        r = requests.post('took url out for security while repo is public for MLH fellowship application :)', json=json_data)
        if (int(r.status_code) != 200):
            print("Response from server: ", r.status_code, r.text)
        else:
            print("Response from server: ", r.status_code, r.text)
    except Exception:
        print("Unable to send data to server, will attempt on next reading")
    print("Done Sending Data")


if config_read_voc:
    print("Performing Warmup")
    warmup()
    print("Done Warmup")

# Normal Operation
elapsed_sec = 0
while True:
    aqdata = get_pm_data()
    dump_sensor_data(aqdata)
    post_data(aqdata)

    if config_read_voc:
        elapsed_sec += 1
        if elapsed_sec > 10:
            elapsed_sec = 0
            print("\t**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x" % (sgp30.baseline_eCO2, sgp30.baseline_TVOC))

    time.sleep(config_interval)
