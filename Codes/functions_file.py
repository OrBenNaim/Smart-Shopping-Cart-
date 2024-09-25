import csv
from csv import DictReader
import cv2 as cv
import pandas as pd
import random
import numpy as np
from pyzbar.pyzbar import decode
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sys
import serial
import ssl
import smtplib
from email.message import EmailMessage
import logging
from datetime import datetime
import time
from hx711 import HX711
import statistics
import requests
import pygame
import pyaudio
import wave
import socket

""" This code run on Raspberry Pi 4 Model B with Webcam on Linux os. """
# ---------------------------------------------------------------------------------------------------------------

""" This script will turn on the camera and take a photo of one product at a time.  """


def detect_barCode():
    # Create a VideoCapture instance once at the beginning of the main code.
    cap = cv.VideoCapture(0)  # Take a photo with my webcam, 0 it's the default camera port.

    if not cap.isOpened():
        raise Exception("Error! Unable to open the camera.")

    # Set resolution
    cap.set(3, 640)  # Default Width
    cap.set(4, 360)  # Default Height

    # Create the window camera:
    cv.namedWindow("Camera window")

    # Set camera window position
    cv.moveWindow("Camera window", 30, 30)

    while True:
        # Capture a frame from the camera module
        result, frame = cap.read()

        if result:  # It will be True if an image was read successfully.

            # Display the frame:
            cv.imshow("Camera window", frame)

            barcode = decode(frame)  # decode() returns list.

            # Wait until the camera detect the barcode which it's happened when the barcode list isn't empty.
            if barcode:
                barcode_num = barcode[0].data.decode('utf-8')

                cv.destroyAllWindows()
                # Release the camera and close the window.
                cap.release()
                return int(barcode_num)

            # waitkey() function of Python OpenCV allows users to display a window for given milliseconds or until any key is pressed.
            # It takes time in milliseconds as a parameter and waits for the given time to destroy the window,
            key = cv.waitKey(1)
            if key == 27 or key == 32:  # 27 is the ASCII code of Esc key on keyboard and 32 is the ASCII code of Space key on keyboard.

                cv.destroyAllWindows()
                # Release the camera and close the window.
                cap.release()
                return 'close camera window'

        else:  # It will be False if there was an issue, such as the camera not being available or not responding.
            raise Exception("No image detected. Please! try again")


# ---------------------------------------------------------------------------------------------------------------
""" This function can open excel file and read its content.
    The target is to find the given barCode number if exist."""


def find_barcode_in_excel_file(excel_file_path, barcode_num):
    product_name = None
    product_price = 0
    product_weight = 0

    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(excel_file_path)

        # Check if the barcode number exists in the 'מספר ברקוד' column
        barcode_exists = df['מספר ברקוד'].eq(barcode_num).any()

        if barcode_exists:

            # Extract information based on the barcode number:
            product_info = \
            df.loc[df['מספר ברקוד'] == barcode_num, ['שם המוצר', 'מחיר המוצר [ש"ח]', 'משקל המוצר [ק"ג]']].iloc[0]

            product_name = str(product_info['שם המוצר'])
            product_price = float(product_info['מחיר המוצר [ש"ח]'])
            product_weight = float(product_info['משקל המוצר [ק"ג]'])

        else:
            print(f"\nBarcode number: {barcode_num}, {type(barcode_num)} doesn't exist in the Excel file.\n")
            result = {"product_name": None, "product_price": 0, "product_weight": 0}

    except FileNotFoundError:
        print(f"\nExcel file not found at: {excel_file_path}\n")
        result = {"product_name": None, "product_price": 0, "product_weight": 0}

    return product_name, product_price, product_weight


# ---------------------------------------------------------------------------------------------------------------

""" This function reads the customer's credit card 
    with RFID-RC522 module """


def scan_credit_card(scan_credit_card_is_done):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    reader = SimpleMFRC522()

    credit_card_num = None

    try:
        print("\nHold a tag near the reader:\n")

        credit_card_num, _ = reader.read()

        print("The credit card number: ", credit_card_num)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        scan_credit_card_is_done(credit_card_num)  # credit_card_num is a callback function.


# ----------------------------------------------------------------------------------------------------------------
""" This function sends email to the customer with his receipt """


def send_email(email_receiver, credit_card_number, price_to_pay, groceries_content_list):
    email_sender = "orbennaim123@gmail.com"
    email_password = "tski omki krvp emck"  # the password to my 2-step verification on Google account
    # (Link to understand: https://www.youtube.com/watch?v=g_j6ILT-X0k)

    email_receiver = email_receiver

    subject = "Super market receipt"
    body = f"""
    מספר חשבונית: {random.randint(10000, 99999)}
    בתאריך {datetime.now().strftime("%d/%m/%Y")} בוצע חיוב בכרטיס האשראי שלך שמספרו {credit_card_number} על סך {round(price_to_pay, 1)} ש"ח

    :סל הקניות שלך הוא
    {groceries_content_list}

    !תודה שקנית בסופר שלנו
    """

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    logging.basicConfig(level=logging.INFO)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.send_message(em)

        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Failed to send email. Error: {e}")


# ----------------------------------------------------------------------------------------------------------------
""" This function initialize the weight scale """


def init_weight_scale():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    hx = HX711(dout_pin=5, pd_sck_pin=6)

    hx.zero()

    ratio = 422.865
    hx.set_scale_ratio(ratio)

    return hx


# ----------------------------------------------------------------------------------------------------------------

""" This function calculates the median weight inside the cart and returns it as the measured weight [Kg] """


def calc_weight(hx):
    measured_weight = 0
    values_list = []

    for _ in range(3):

        # Measuring weight and convert its unit to Kg:
        weight_in_Kg = hx.get_weight_mean(readings=15) / 1000

        if weight_in_Kg < 0:
            weight_in_Kg = 0

        values_list.append(weight_in_Kg)

    measured_weight = round(statistics.median(values_list), 3)

    return measured_weight


# ----------------------------------------------------------------------------------------------------------------

""" This function try to access the server which is established on the main Computer (Or PC), 
    and sends all the products the customer bought as dictionary (Customer.groceries_dict)  """


def Send_Data_To_MainComputer(groceries_dict):
    # 192.168.7.14 is the IP address of Or's PC, the port number can be any number within the range: 1024-49151.
    # 192.168.7.6 is the IP address of Or's laptop when connected to ORNA64 wifi network.

    # !!!!!!!!!!! needs to change the ip when connected to Braude wifi !!!!!!!!!!!!!

    # Or_PC_IP_with_ORNA64 = '192.168.7.14'
    # Or_Laptop_IP_with_ORNA64= '192.168.7.6'
    Or_Laptop_IP_with_IPhone_HotSpot = '172.20.10.9'  # !!! needs to change the ip when connected to Braude wifi !!!

    print("\nBefore the while loop")
    server_url = f'http://{Or_Laptop_IP_with_IPhone_HotSpot}:12345/receive_data'

    failed_attempts = 0

    while True:
        print("\nInside the while loop")
        try:
            print("\nInside the try option")
            response = requests.post(server_url, json=groceries_dict)

            # Print the response from the server (optional)
            print(f'\nServer response: {response.json()}')

        except requests.ConnectionError:
            print("\nInside the except option")
            print(f'\nUnable to connect to the server: {server_url}')

            # failed_attempts += 1

            # if failed_attempts == 1:
            #     server_url = f'http://{Or_Laptop_IP_with_ORNA64}:12345/receive_data'

            # elif failed_attempts == 2:
            #     server_url = f'http://{Or_PC_IP_with_ORNA64}:12345/receive_data'

            # elif failed_attempts == 3:
            #     print("\nNone of the 3 IP option not match")
            #     break   # Exit the while loop
            
        # Execute if no exception occurred:
        else:
            break  # Exit the while loop

    print("\nOutside the while loop")


def play_audio(audio_file_path):
    pygame.init()
    pygame.mixer.init()
    sound = pygame.mixer.Sound(audio_file_path)

    # Play the sound:
    sound.play()

    # Wait for the sound to finish playing (optional)
    while pygame.mixer.get_busy():
        pygame.time.delay(100)

    # Clean up
    pygame.quit()
