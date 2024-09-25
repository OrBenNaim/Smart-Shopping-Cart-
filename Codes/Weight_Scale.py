from hx711 import HX711
import RPi._GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

hx = HX711(dout_pin=5, pd_sck_pin=6)

hx.zero()

input("\nPlace the known weight on the scale and press Enter: ")
reading = hx.get_data_mean(readings=50)
print(f"\nreading = {reading}")

known_weight_kg = input("\nEnter the known weight in grams and press Enter: ")
value = float(known_weight_kg)

ratio = abs(reading)/value
print(f"\nratio = {ratio}")

hx.set_scale_ratio(ratio)

while True:
    measured_weight = hx.get_weight_mean(readings=50)

    if measured_weight < 0:
        measured_weight = 0

    print(f"{round(measured_weight, 2)} grams")

