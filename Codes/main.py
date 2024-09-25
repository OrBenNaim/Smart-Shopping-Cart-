#! /home/orbennaim1/Desktop/Final_Project/venv/bin/python3

# The above line tells the system to use python3 interpreter via the virtual environment (venv) I created.

# from functions_file import *
from Touch_Screen_GUI import ShoppingApp
import atexit
import json

if __name__ == '__main__':

    # --------------- Initialization all the necessary variables at the beginning of the main program -----------------------

    # Specify the path to your Excel file where all the Groceries are located.
    excel_file_path = '/home/orbennaim1/Desktop/Final_Project/Groceries_Info.xlsx'

    # Display the ShoppingApp():
    app = ShoppingApp(excel_file_path)

    # Try to open the app_data.json file:
    try:
        with open('app_data.json', 'r') as file:
            data = json.load(file)

    except FileNotFoundError:
        raise Exception("JSON file not found")

    # Check if the app closed properly or it crashed:
    if data["Application status"] == "opened":
        app.app_status = "opened"

    else:
        app.app_status = "closed"

    file.close()

    # Run my GUI application:
    app.run()

    app.mainloop()

    # Terminate the thread before the whole program is terminated:
    app.stop_event.set()

    # Save the entire application data before the whole program is terminated:
    app.app_status = "closed"
    app.app_data["Application status"] = app.app_status
    app.save_data()


