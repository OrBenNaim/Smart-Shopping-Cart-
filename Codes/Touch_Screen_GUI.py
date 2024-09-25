import tkinter as tk
import re
from functions_file import *
from bidi.algorithm import get_display
import time
from threading import Thread, Event
import json

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This class will represent the customer and his attributes during the shopping"""


class Customer:

    def __init__(self):
        # Variable to store the customer's email as string:
        self.email_address = None

        # The total price the customer has to pay in the end of the acquisition:
        self.price_to_pay = 0

        # The total weight that should be in the cart according to the groceries reported by the customer.
        # (This variable should be compared with the weight actually measured inside the cart):
        self.total_weight = 0

        # Variable to store the customer's credit card number:
        self.credit_card_number = None

        # Dictionary to store the whole groceries the customer bought, while each key it's the product barcode and value
        # it's a list that conatins: product name (index = 0), product price (index = 1), product weight (index = 2)
        # and the quantity of each product (index = 3) -> [product_name, product_price, product_weight, quantity_of_each_product]
        self.groceries_dict = {}

        # This string will display the groceries the customer bought as:
        # רסק עגבניות (2 יחידות) - 5 ש"ח
        # קוקה קולה (1 יחידות) - 7.13 ש"ח
        self.groceries_content_list = ""  # This groceries_content_list show inside the email recipt the customer will after he pay.


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This class will manage the entire shopping app """


class ShoppingApp(tk.Tk):  # ShoppingApp will inherit the attributes of Tk class and act like an instance of Tk.

    def __init__(self, excel_file_path, width_frame=790, height_frame=410,
                 backGround_color="gray23"):  # 3 default parameters

        # Initialize parent constructor and create the main application window (root window):
        tk.Tk.__init__(self)

        # initialize the weight scale and store the hx variable for later usages:
        self.hx = init_weight_scale()

        # Define variables that will hold the "old" weight and the current weight inside the wagon:
        self.old_weight = 0
        self.current_weight = 0

        # Create a Customer object:
        self.customer = Customer()

        # Variable to describe the application status:
        self.app_status = None  # app_status can be change to "opened" or "closed" values

        # Variable to store the application status::
        self.app_data = {"Application status": self.app_status, "Customer email": self.customer.email_address,
                         "Price to pay": self.customer.price_to_pay,
                         "Total weight": self.customer.total_weight,
                         "Credit card number": self.customer.credit_card_number,
                         "Groceries dictionary": self.customer.groceries_dict,
                         "Groceries content list": self.customer.groceries_content_list}

        # Store the excel file path for later usages:
        self.excel_file_path = excel_file_path

        # Create variable that update automatically after adding/removing product:
        self.purchase_amount_var = tk.StringVar()

        # Set the title window:
        self.title("Smart shopping cart")

        self.font = ('Arial', 24, 'bold')

        # Store the window screen resolution:
        self.width_frame = width_frame
        self.height_frame = height_frame

        # Place the window at the center of the screen:
        self.place_window_at_center()

        # Save background value for later usages.
        self.bg_color = backGround_color  # bg = background

        # Dictionary for storing each page instance:
        self.frames = {}
        self.current_frame = None  # Variable to store the current frame object that being display, except TheftWarningFrame which is not included.

        # Create an instance of each class -> call to constructor which is __init__.
        for Class in (StartingFrame, RegistrationFrame, HomeFrame, AskForQuantityFrame,
                      ShowGroceriesFrame, PaymentFrame, ProductsWithOutBarcodeFrame, TheftWarningFrame):
            frame = Class(root=self, customer=self.customer)  # call to the class constructor.
            frame_name = Class.__name__  # Get the name of the class in each iteration.

            self.frames[frame_name] = frame  # Store the instance in dictionary.

            # put all the pages in the same location,
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")
            frame.pack_propagate(False)  # Prevent from the child label to modifying the parent frame (frame2).

        # When this event is set, the comparing_thread will be terminated.
        self.stop_event = Event()

        # When this event is set, the comparing_thread will be paused.
        self.pause_event = Event()  # Usually the comparing_thread will be paused when customer is trying to add vegetables or fruits.
        self.pause_event.set()  # Pause the comparing_thread in the beginning:

        # Create a Thread that checks in infinite loop the actual weight in the cart by the measurement of the weight scale.
        # This Thread works in "parallel" to the gui app.
        self.comparing_thread = Thread(target=self.measure_weight)
        self.comparing_thread.start()

    def run(self):

        # Show the StartingFrame first if the app wasn't crashed:
        if self.app_status == 'closed':
            self.app_status = 'opened'

            self.current_frame = "StartingFrame"
            self.show_page("StartingFrame")

        # Show the HomeFrame first if the app was crashed:
        elif self.app_status == 'opened':
            self.load_data()

            self.current_frame = "HomeFrame"

            # Resume the comparing_thread when the customer finished to register:
            self.pause_event.clear()
            print("\nThe comparing_thread is resumed...")

            self.show_page("HomeFrame")

    def measure_weight(self):
        deviation_range = 0.02  # Define a maximum deviation of 20 grams (0.02 Kg), in case of the Weight Scale isn't accurate.
        TheftWarningFrame_is_display = False

        while not self.stop_event.is_set():

            # Measuring weight and convert its unit to Kg,
            # measured_weight is the real weight inside the cart, measured by the Load Cell + HX711 module.
            measured_weight = self.hx.get_weight_mean(readings=15) / 1000

            if measured_weight < 0:
                measured_weight = 0

            # Check if the customer isn't trying to add vegetables or fruits:
            if not self.pause_event.is_set():

                self.current_weight = round(measured_weight, 3)
                self.customer.total_weight = round(self.customer.total_weight, 3)

                # customer.total_weight is the total weight that should be in the cart according to the groceries reported by the customer.
                if measured_weight - deviation_range > self.customer.total_weight:  # If true, means the system detected a theft
                    print("\nThe system detected a theft\n")
                    print(
                        f"\nThe measured weight is: {round(measured_weight, 3)} Kg\nThe customer.total_weight is: {self.customer.total_weight} Kg")

                    # Check if the TheftWarningFrame isn't display yet:
                    if not TheftWarningFrame_is_display:
                        self.show_page("TheftWarningFrame")
                        TheftWarningFrame_is_display = True

                        play_audio('over_weight_warning.wav')


                else:  # The measured_weight is within the legal range.
                    print(
                        f"\nThe measured weight is: {round(measured_weight, 3)} Kg\nThe total weight that should be in the cart is: {self.customer.total_weight} Kg")

                    # Check if the TheftWarningFrame is currently display:
                    if TheftWarningFrame_is_display:
                        TheftWarningFrame_is_display = False

                        # Display the last frame was display before TheftWarningFrame:
                        self.show_page(self.current_frame)

    def save_data(self):

        self.app_data["Application status"] = self.app_status
        self.app_data["Customer email"] = self.customer.email_address
        self.app_data["Price to pay"] = round(self.customer.price_to_pay, 2)
        self.app_data["Total weight"] = round(self.customer.total_weight, 3)
        self.app_data["Credit card number"] = self.customer.credit_card_number
        self.app_data["Groceries dictionary"] = self.customer.groceries_dict
        self.app_data["Groceries content list"] = self.customer.groceries_content_list

        with open('app_data.json', 'w') as file:
            json.dump(self.app_data, file)

        file.close()

    def load_data(self):
        try:
            with open('app_data.json', 'r') as file:
                self.app_data = json.load(file)

                # Restore the customer data:
                self.customer.email_address = self.app_data["Customer email"]
                self.customer.price_to_pay = self.app_data["Price to pay"]
                self.customer.total_weight = self.app_data["Total weight"]
                self.customer.credit_card_number = self.app_data["Credit card number"]
                self.customer.groceries_dict = self.app_data["Groceries dictionary"]
                self.customer.groceries_content_list = self.app_data["Groceries content list"]

                # Update the purchase_amount label on the HomeFrame:
                self.purchase_amount_var.set(get_display(f'סכום הקנייה: {round(self.customer.price_to_pay, 2)} ש"ח'))

                # Update the ListBox (סל הקניות):
                ShowGroceriesFrame = self.frames["ShowGroceriesFrame"]

                for barcode_number in self.customer.groceries_dict.keys():
                    product_name = self.customer.groceries_dict[barcode_number][0]
                    product_weight = self.customer.groceries_dict[barcode_number][2]
                    product_quantity = self.customer.groceries_dict[barcode_number][3]

                    if barcode_number == "תפוח" or barcode_number == "תפוז" or barcode_number == "מלפפון":
                        ShowGroceriesFrame.insert_product(barcode_number, product_name, product_quantity,
                                                          product_weight)

                    else:
                        ShowGroceriesFrame.insert_product(barcode_number, product_name, product_quantity)

                # Update the amount_to_pay_text and email_address_text variables inside PaymentFrame:
                PaymentFrame = self.frames["PaymentFrame"]
                PaymentFrame.email_address_text.set(get_display(f"המייל שלך הוא: {self.customer.email_address}"))
                PaymentFrame.amount_to_pay_text.set(
                    get_display(f'סכום לתשלום: {round(self.customer.price_to_pay, 2)} ש"ח'))

            file.close()

        except FileNotFoundError:
            raise Exception("JSON file not found")

    def show_page(self, frame_name):
        frame = self.frames[frame_name]

        # Raise frame above the others in the stacking order, the top frame will be visible.
        frame.tkraise()

    def place_window_at_center(self):
        # Get the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate the center coordinates for the window
        x = (screen_width - self.width_frame) // 2
        y = (screen_height - self.height_frame) // 2

        # Set the window's position
        self.geometry(f"{self.width_frame}x{self.height_frame}+{x - 10}+{y + 10}")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" StartingFrame will inherit the attributes of Tk class and act like an instance of Tk.Frame """


class StartingFrame(tk.Frame):
    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        # Create a welcome_label:
        self.welcome_label = tk.Label(self, text=get_display("ברוכים הבאים!"), bg=root.bg_color, fg="white",
                                      font=('Arial', 24, 'bold'))

        self.welcome_label.grid(row=0, column=0, padx=(280, 0), pady=(150, 0))

        # Create a start_shopping:
        self.start_shopping_button = tk.Button(self, text=get_display("התחל קנייה"), font=('Arial', 24, 'bold'),
                                               bg="#473CBB", fg="white",
                                               cursor="hand2",
                                               activebackground="#badee2", activeforeground="black",
                                               command=lambda: root.show_page("RegistrationFrame"))

        self.start_shopping_button.grid(row=1, column=0, padx=(280, 0), pady=(10, 0))


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This class creates the registration Frame where the customer enter his phone number. """


class RegistrationFrame(
    tk.Frame):  # RegistrationFrame will inherit the attributes of Tk class and act like an instance of Tk.Frame
    def __init__(self, root, customer):
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        # Create a prompt of email label:
        self.email_label = tk.Label(self, text=get_display("רשום את המייל שלך:"), bg=root.bg_color, fg="white",
                                    font=("Arial", 20, "bold"))
        self.email_label.grid(row=0, column=0, padx=(100, 0), pady=(5, 5))

        # Create an Entry widget for text input:
        self.email_address = tk.StringVar()

        self.email_entry = tk.Entry(self, textvariable=self.email_address, font=('Arial', 20), width=40, bd=3)
        self.email_entry.grid(row=1, column=0, padx=(60, 0))

        # Create a prompt of InValid email label:
        self.invalidEmail_label = tk.Label(self, text=get_display("כתובת המייל אינה תקינה!\nאנא נסה שנית!"),
                                           bg=self.root.bg_color,
                                           fg="white",
                                           font=("Arial", 18, 'bold'))

        # Set the buttons for the keyboard:
        keyboard_buttons = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l',
            'z', 'x', 'c', 'v', 'b', 'n', 'm', '@', '.'
        ]

        # Set the starting row and column:
        row_cnt = 2  # counter to count the number of rows.
        x_space = 0  # Space between each button in the same row.
        col_cnt = 0  # counter to count the number of buttons in one row.

        # Create each button:
        for button_text in keyboard_buttons:
            button = tk.Button(self, text=button_text, font=("Arial", 14, "bold"),
                               width=3, height=2, activebackground="#badee2",
                               command=lambda b=button_text: self.handle_button_click(b))
            button.grid(row=row_cnt, column=0, sticky='w', padx=(5 + x_space, 0), pady=5)

            # Adjust the grid position:
            if col_cnt < 9:
                col_cnt += 1
                x_space += 75
            else:
                col_cnt = 0
                x_space = 0
                row_cnt += 1

        # Create submit button:
        self.submit_button = tk.Button(self, text=get_display("אישור")
                                       , font=("Arial", 18, "bold"), bg="#308014", fg="white",
                                       cursor="hand2",
                                       activebackground="#badee2", activeforeground="black",
                                       command=lambda: self.check_email())

        self.submit_button.grid(row=7, column=0, sticky='w', padx=(300, 0), pady=(15, 0))

        # Create delete button:
        self.delete_button = tk.Button(self, text=get_display("מחיקה")
                                       , font=("Arial", 18, "bold"), bg="red4", fg="white",
                                       cursor="hand2",
                                       activebackground="#badee2", activeforeground="black",
                                       command=lambda: self.handle_button_click("מחיקה"))

        self.delete_button.grid(row=7, column=0, sticky='w', padx=(400, 0), pady=(15, 0))

    def handle_button_click(self, button_text):

        if button_text == "מחיקה":
            current_email = self.email_address.get()
            self.email_address.set(current_email[:-1])

        else:
            # Add the pressed button's text to the current email:
            self.email_address.set(self.email_address.get() + button_text)

    def check_email(self):
        # Check the address email the user entered, the user not allowed to write special character as the first
        # character of the email address.

        email_str = self.email_entry.get()
        match = re.search(r'^\w([\w.-]+)@([\w\\.]+)(\.co\.il$|\.com$|\.ac\.il$)',
                          email_str)  # '\\' -> Back Slash       # '\-' -> Hyphen        # '.' -> Any character
        if match:
            self.customer.email_address = email_str  # Store the customer email address for later usages.
            PaymentFrame = self.root.frames["PaymentFrame"]
            PaymentFrame.email_address_text.set(get_display(f"המייל שלך הוא: {email_str}"))

            self.invalidEmail_label.grid_forget()

            # Resume the comparing_thread when the customer finished to register:
            self.root.pause_event.clear()
            print("\nThe comparing_thread is resumed...")

            # Store the application data inside "app_data.json" file:
            self.root.save_data()

            # Save the current frame being display:
            self.root.current_frame = "HomeFrame"

            # Display the next frame:
            self.root.show_page("HomeFrame")

        else:
            # Repostion the submit and delete buttons:
            self.submit_button.grid(row=7, column=0, sticky='w', padx=(500, 0), pady=(15, 0))
            self.delete_button.grid(row=7, column=0, sticky='w', padx=(600, 0), pady=(15, 0))

            # Show the Invalid Email Label:
            self.invalidEmail_label.grid(row=7, column=0, sticky='w', padx=(50, 0))

            self.after(100, self.play_audio_if_email_address_is_invalid)

    def play_audio_if_email_address_is_invalid(self):
        play_audio("Invalid_email_address.wav")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" The HomeFrame will show all the main features for the customer such as Add_Product or End_of_purchase, etc. """


class HomeFrame(tk.Frame):

    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        # Create a cancel button:
        self.canceling_purchase = tk.Button(self, text=get_display("לביטול הקנייה"), font=('Arial', 14, 'bold'),
                                            bg='red4', fg="white", cursor="hand2", activebackground="#badee2",
                                            activeforeground="black", command=lambda: self.resetAll())

        self.canceling_purchase.grid(row=0, column=0, sticky='w', padx=(5, 0), pady=(10, 0))

        # Create an add_product_withOut_barcode button:
        self.add_product_withOut_barcode_button = tk.Button(self,
                                                            text=get_display("הוספת מוצר ללא ברקוד\nפירות וירקות"),
                                                            font=('Arial', 18, 'bold'),
                                                            bg="#FF8C00", fg="white",
                                                            cursor="hand2", activebackground="#badee2",
                                                            activeforeground="black",
                                                            command=lambda: self.manage_buttons(
                                                                "add product without barcode"))

        self.add_product_withOut_barcode_button.grid(row=1, column=0, sticky='w', padx=(80, 40), pady=(30, 0))

        # Create an add_product_with_barcode button:
        self.add_product_with_barcode_button = tk.Button(self, text=get_display("הוספת מוצר עם ברקוד\n"),
                                                         font=('Arial', 18, 'bold'), bg="#473CBB", fg="white",
                                                         cursor="hand2", activebackground="#badee2",
                                                         activeforeground="black",
                                                         command=lambda: self.root.show_page("AskForQuantityFrame"))

        self.add_product_with_barcode_button.grid(row=1, column=1, sticky='e', padx=(40, 80), pady=(30, 0))

        # Create a show_groceries_list button:
        self.show_groceries_list = tk.Button(self, text=get_display('להצגת סל הקניות'), font=('Arial', 18, 'bold'),
                                             bg="white", fg="green",
                                             cursor="hand2", activebackground="#badee2",
                                             activeforeground="black",
                                             command=lambda: self.manage_buttons("show groceries frame"))

        self.show_groceries_list.grid(row=2, column=0, columnspan=2, padx=(0, 0), pady=(40, 0))

        # Initialize the variable to 0 at the beginning:
        self.root.purchase_amount_var.set(get_display('סכום הקנייה: 0 ש"ח'))

        # Create a purchase_amount label:
        self.purchase_amount_label = tk.Label(self, textvariable=self.root.purchase_amount_var,
                                              bg=self.root.bg_color, fg="white", font=self.root.font)

        self.purchase_amount_label.grid(row=3, column=0, columnspan=2, padx=(0, 0), pady=(40, 0))

        # Create an end_purchase button:
        self.end_purchase_button = tk.Button(self, text=get_display('לסיום קנייה ותשלום'), font=('Arial', 18, 'bold'),
                                             bg="#308014", fg="white",
                                             cursor="hand2", activebackground="#badee2",
                                             activeforeground="black",
                                             command=lambda: self.manage_buttons("payment frame"))

        self.end_purchase_button.grid(row=4, column=0, columnspan=2, padx=(0, 0), pady=(40, 0))

    def manage_buttons(self, button_name):

        if button_name == "add product without barcode":

            # Save the current frame being display:
            self.root.current_frame = "ProductsWithOutBarcodeFrame"
            self.root.show_page("ProductsWithOutBarcodeFrame")

        elif button_name == "show groceries frame":

            # Save the current frame being display:
            self.root.current_frame = "ShowGroceriesFrame"
            self.root.show_page("ShowGroceriesFrame")

        elif button_name == "payment frame":
            # Save the current frame being display:
            self.root.current_frame = "PaymentFrame"
            self.root.show_page("PaymentFrame")

    def resetAll(self):

        # Pause the comparing_thread when the after the customer succssfully payed:
        self.root.pause_event.set()
        print("\nThe comparing_thread is paused...")

        # Reset all the customer fields:
        self.customer.email_address = None
        self.customer.price_to_pay = 0
        self.customer.total_weight = 0
        self.credit_card_number = None
        self.customer.groceries_dict = {}
        self.customer.groceries_content_list = ""

        # Reset all the necessary ShoppingApp variables:
        self.root.purchase_amount_var.set(get_display('סכום הקנייה: 0 ש"ח'))
        self.root.old_weight = 0
        self.root.current_weight = 0
        self.root.save_data()

        # Reset all the necessary RegistrationFrame variables:
        RegistrationFrame = self.root.frames["RegistrationFrame"]
        RegistrationFrame.email_entry.delete(0, tk.END)  # Reset the tk.Entry() for customer's email address:

        # Reset all the ShowGroceriesFrame variables:
        ShowGroceriesFrame = self.root.frames["ShowGroceriesFrame"]
        ShowGroceriesFrame.list_box.delete(0, tk.END)
        ShowGroceriesFrame.groceries_as_rows = []
        ShowGroceriesFrame.barcode_number = None
        ShowGroceriesFrame.product_name = None
        ShowGroceriesFrame.price_per_one_Kg = None
        ShowGroceriesFrame.product_price = None
        ShowGroceriesFrame.product_weight = None
        ShowGroceriesFrame.product_quantity = None
        ShowGroceriesFrame.added_weight = 0
        ShowGroceriesFrame.reduced_weight = 0

        # Reset all the PaymentFrame variables:
        PaymentFrame = self.root.frames["PaymentFrame"]
        PaymentFrame.credit_card_message_text.set("")
        PaymentFrame.amount_to_pay_text.set(get_display(f'סכום לתשלום: {0} ש"ח'))

        # Reset all the ProductsWithOutBarcodeFrame variables:
        ProductsWithOutBarcodeFrame = self.root.frames["ProductsWithOutBarcodeFrame"]
        ProductsWithOutBarcodeFrame.product_name = None
        ProductsWithOutBarcodeFrame.product_price_per_one_Kg = None
        ProductsWithOutBarcodeFrame.excel_file_handler = None

        # Save the current frame being display:
        self.root.current_frame = "StartingFrame"

        # Display the StartingFrame again:
        self.root.show_page("StartingFrame")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This Frame will appear immediately after the customer scan a new product, the user will enter the desired entity of each product """


class AskForQuantityFrame(tk.Frame):

    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        self.current_text = None

        # Create a prompt of phone label:
        self.quantity_label = tk.Label(self, text=get_display("בחר כמות יחידות רצויה:"), bg=root.bg_color, fg="white",
                                       font=("Arial", 18, 'bold'))
        self.quantity_label.grid(row=0, column=0, sticky='n', padx=(250, 0), pady=(10, 0))

        self.product_quantity = tk.StringVar()
        self.current_number = tk.StringVar()

        # Create a purchase_amount entry:
        self.quantity_entry = tk.Entry(self, textvariable=self.current_number, font=("Arial", 18))
        self.quantity_entry.grid(row=0, column=0, sticky='n', padx=(250, 0), pady=(50, 0))

        # Create button for each digit between 1-10:
        x_space = 0

        for digit in range(1, 10):
            self.button = tk.Button(self, text=str(digit), font=("Arial", 14), width=3, height=2,
                                    command=lambda num=digit: self.digit_pressed(str(num)))
            self.button.grid(row=1 + ((digit - 1) // 3), column=0, padx=(100 + x_space, 0), pady=(20, 0))

            # Each row has 3 digits, so after digit number: 3, 6, 9 we create a new row
            if digit % 3 == 0:
                x_space = 0

            else:
                x_space += 150

        # Create a button for 0 digit:
        self.button_0 = tk.Button(self, text="0", font=("Arial", 14), width=4, height=2,
                                  command=lambda: self.digit_pressed("0"))
        self.button_0.grid(row=4, column=0, padx=(250, 0), pady=(20, 0))

        # Create a backSpace button:
        self.delete_button = tk.Button(self, text=get_display("מחיקה"), font=("Arial", 16, 'bold'), width=10, height=2,
                                       bg="red4", fg="white", command=self.delete_pressed)
        self.delete_button.grid(row=1, column=1, padx=(20, 0), pady=(20, 0))

        # Create a confirm button:
        self.confirm_button = tk.Button(self, text=get_display("אישור"), font=("Arial", 16, 'bold'), width=10, height=2,
                                        bg="#308014", fg="white", command=self.confirm_pressed)
        self.confirm_button.grid(row=2, column=1, padx=(20, 0), pady=(20, 0))

        # Create a back button:
        self.back_button = tk.Button(self, text=get_display("חזור"), font=("Arial", 16, 'bold'), width=10, height=2,
                                     bg="orange", fg="white", command=self.back_pressed)
        self.back_button.grid(row=3, column=1, padx=(20, 0), pady=(20, 0))

    def digit_pressed(self, digit):
        self.current_number.set(self.current_number.get() + digit)

    def delete_pressed(self):
        self.current_text = self.current_number.get()
        self.current_number.set(self.current_text[:-1])

    def back_pressed(self):

        # Clean entry field before the next product:
        self.quantity_entry.delete(0, 'end')

        # Save the current frame being display:
        self.root.current_frame = "HomeFrame"

        self.root.show_page("HomeFrame")

    # After the customer selected the desired quantity the camera will open and starts to scan the barcode:
    def confirm_pressed(self):
        self.product_quantity = int(self.current_number.get())

        # Clean entry field before the next product:
        self.quantity_entry.delete(0, 'end')

        # Minimize GUI window before camera window will be opened:
        self.root.withdraw()

        product_name = None

        # Stay in the camera window until an existing product is scanned:
        while product_name is None:

            # Open camera and detect the product barCode:
            barcode_number = detect_barCode()

            if barcode_number == 'close camera window':
                # Maximize GUI window after camera window closed after the SPACE or ESC keyboards are pressed:
                self.root.deiconify()
                break

            # Check if the barcode exits inside the excel file and calculate the total price and total weight :
            product_name, product_price, product_weight = find_barcode_in_excel_file(self.root.excel_file_path,
                                                                                     barcode_number)

            if product_name is None:
                continue

            else:  # If the product_name is not None, the product is existing in our excel file.

                # Maximize GUI window after camera window closed and the product is existing inside excel file:
                self.root.deiconify()

                """ Add product to the groceries' dictionary and
                check if the customer already add this product before, if so increase the quantity of this product by self.product_quantity: """
                if barcode_number in self.customer.groceries_dict.keys():
                    self.customer.groceries_dict[barcode_number][3] += self.product_quantity

                # If the product not added before, update groceries_dict now:
                else:
                    self.customer.groceries_dict[barcode_number] = [product_name, product_price, product_weight,
                                                                    self.product_quantity]

                # Update the total price to pay:
                self.customer.price_to_pay += round(product_price * float(self.product_quantity), 2)

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight += round(product_weight * float(self.product_quantity), 3)

                # Update the purchase_amount label in the HomeFrame:
                self.root.purchase_amount_var.set(
                    get_display(f'סכום הקנייה: {round(self.customer.price_to_pay, 2)} ש"ח'))

                # Update the amount_to_pay_text variable inside PaymentFrame:
                PaymentFrame = self.root.frames["PaymentFrame"]
                PaymentFrame.amount_to_pay_text.set(
                    get_display(f'סכום לתשלום: {round(self.customer.price_to_pay, 2)} ש"ח'))

                # Insert product into ListBox (סל הקניות) if product exists:
                ShowGroceriesFrame = self.root.frames["ShowGroceriesFrame"]
                ShowGroceriesFrame.insert_product(barcode_number, product_name,
                                                  self.customer.groceries_dict[barcode_number][3])

                # Save the current frame being display:
                self.root.current_frame = "HomeFrame"

                # Store the application data inside "app_data.json" file:
                self.root.save_data()

        # Save the current frame being display:
        self.root.current_frame = "HomeFrame"

        # Back to the Home frame:
        self.root.show_page("HomeFrame")
        self.after(100, self.Display_Home_Screen_and_play_audio_later)

    def Display_Home_Screen_and_play_audio_later(self):
        play_audio("scanned_product.wav")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This Frame will show all the groceries the customer already scanned """


class ShowGroceriesFrame(tk.Frame):

    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        self.barcode_number = None
        self.product_name = None
        self.price_per_one_Kg = None  # Meant for products that havn't a barcode only and their price is per one Kg.
        self.product_price = None  # Meant for products that have a barcode only and their price is per one unit.
        self.product_weight = None  # Meant for products that havn't a barcode only and their price is per one Kg.
        self.product_quantity = None  # Meant for products that have a barcode only and their price is per one unit.

        self.added_weight = 0  # Variable to store the weight the customer added.
        self.reduced_weight = 0  # Variable to store the weight the customer reduced.

        # Create a list_box for display all the groceries the customer bought (the groceries in this list box will be):
        self.list_box = tk.Listbox(self, font=('Arial', 14, 'bold'), width=90, height=14)
        self.list_box.grid(row=0, column=0)

        """ Each product will be display inside the list_box on separate row,
            so the line number (starts from 0) will be the index of each barcode number 
            in self.groceries_as_rows which is a list. """
        self.groceries_as_rows = []

        # Create a delete button:
        self.delete_button = tk.Button(self, text=get_display("מחק"),
                                       font=('Arial', 20, 'bold'), bg="red4", fg="white",
                                       cursor="hand2", activebackground="#badee2",
                                       activeforeground="black",
                                       command=lambda: self.delete_product())

        self.delete_button.grid(row=1, column=0, sticky='w', padx=(20, 0), pady=(10, 0))

        # Create an increase_quantity button:
        self.increase_quantity_button = tk.Button(self, text=get_display("הגדל כמות"),
                                                  font=('Arial', 20, 'bold'), bg="blue", fg="white",
                                                  cursor="hand2", activebackground="#badee2",
                                                  activeforeground="black",
                                                  command=lambda: self.increase_quantity())

        self.increase_quantity_button.grid(row=1, column=0, sticky='w', padx=(200, 0), pady=(10, 0))

        # Create an decrease_quantity button:
        self.decrease_quantity_button = tk.Button(self, text=get_display("הקטן כמות"),
                                                  font=('Arial', 20, 'bold'), bg="orange", fg="white",
                                                  cursor="hand2", activebackground="#badee2",
                                                  activeforeground="black",
                                                  command=lambda: self.decrease_quantity())

        self.decrease_quantity_button.grid(row=1, column=0, sticky='w', padx=(400, 0), pady=(10, 0))

        # Create a back button:
        self.back_button = tk.Button(self, text=get_display("חזור"),
                                     font=('Arial', 20, 'bold'), bg="#308014", fg="white",
                                     cursor="hand2", activebackground="#badee2",
                                     activeforeground="black",
                                     command=lambda: self.back_button_is_pressed())

        self.back_button.grid(row=1, column=0, sticky='w', padx=(650, 0), pady=(10, 0))

    def back_button_is_pressed(self):
        # Save the current frame being display:
        self.root.current_frame = "HomeFrame"
        self.root.show_page("HomeFrame")

    """ This function increases the quantity of the selected product by one inside the List Box """

    def increase_quantity(self):
        selected_index = self.list_box.curselection()

        if selected_index != ():
            row_index = selected_index[0]

            # Extract the barcode number from frame.groceries_as_rows:
            self.barcode_number = self.groceries_as_rows[row_index]

            # Check if this product has barcode or not:
            if self.customer.groceries_dict[self.barcode_number][
                3] != None:  # if True means this product has a barcode.

                # Increase the quantity of the selected product by one:
                self.customer.groceries_dict[self.barcode_number][3] += 1

                self.product_price = self.customer.groceries_dict[self.barcode_number][1]

                # Update the total price that the customer needs to pay:
                self.customer.price_to_pay += self.product_price

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight += self.customer.groceries_dict[self.barcode_number][2]
                round(self.customer.total_weight, 3)

            else:  # If we get to the 'else' option it means that this product hasn't a barcode.

                # Pause the comparing_thread while the customer is trying to add his product without a barcode:
                self.root.pause_event.set()
                print("\nThe comparing_thread is paused")

                print(f"\nThe weight before the customer increase his product is: {self.root.current_weight} Kg")

                measured_weight = 0
                deviation_range = 0.02  # Define maximum deviation of 20 grams (0.02 Kg), in case of the Weight Scale isn't accurate.

                # Wait until the customer will increase the product quantity:
                while measured_weight - deviation_range <= self.root.current_weight:

                    # Measuring weight and convert its unit to Kg:
                    measured_weight = self.root.hx.get_weight_mean(readings=15) / 1000

                    if measured_weight < 0:
                        measured_weight = 0

                    print("\nInside while loop...")
                    print(f"The measured_weight is: {round(measured_weight, 3)} Kg")

                self.added_weight = round(measured_weight - self.root.current_weight,
                                          3)  # The actual weight minus the weigth that was in the cart before the customer increase the product quantity.

                # Increase the "total" weight of the selected product by self.added_weight:
                self.customer.groceries_dict[self.barcode_number][2] += self.added_weight

                # Update the total price that the customer needs to pay:
                self.product_price_per_one_Kg = self.customer.groceries_dict[self.barcode_number][1]
                self.customer.price_to_pay += self.product_price_per_one_Kg * self.added_weight

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight += self.added_weight
                round(self.customer.total_weight, 3)

                # Resume the comparing_thread when the customer finished to add his product without a barcode:
                self.root.pause_event.clear()
                print("\nThe comparing_thread is resumed")

            # Update the purchase_amount label on the HomeFrame:
            self.root.purchase_amount_var.set(get_display(f'סכום הקנייה: {round(self.customer.price_to_pay, 2)} ש"ח'))

            # Update the amount_to_pay_text variable inside PaymentFrame:
            PaymentFrame = self.root.frames["PaymentFrame"]
            PaymentFrame.amount_to_pay_text.set(get_display(f'סכום לתשלום: {round(self.customer.price_to_pay, 2)} ש"ח'))

            # Delete the product from the list_box:
            self.list_box.delete(selected_index)

            self.product_name = self.customer.groceries_dict[self.barcode_number][0]
            self.product_price = self.customer.groceries_dict[self.barcode_number][1]
            self.product_weight = self.customer.groceries_dict[self.barcode_number][2]
            self.product_quantity = self.customer.groceries_dict[self.barcode_number][3]

            # In case of product without barcode:
            if self.product_quantity is None:
                self.list_box.insert(selected_index, get_display(
                    f'{self.product_name} ({round(self.product_weight, 3)} ק"ג) - {round(self.product_price_per_one_Kg * self.product_weight, 2)} ש"ח').rjust(
                    120))  # Adjust the width as needed

            else:  # In case of product with barcode:

                # Add the product to the list_box in the same row it was with the updated quantity:
                self.list_box.insert(selected_index, get_display(
                    f'{self.product_name} ({self.product_quantity} יחידות) - {round(self.product_price * self.product_quantity, 2)} ש"ח').rjust(
                    120))  # Adjust the width as needed

            # Update the groceries_content list:
            converted_text = [get_display(line) for line in self.list_box.get(0,
                                                                              tk.END)]  # convert each line in the list box from BidiDiplay type into regular type.
            self.customer.groceries_content_list = '\n'.join(
                converted_text)  # self.list_box.get(0, tk.END) returns the whole content inside the list_box.

            # Store the application data inside "app_data.json" file:
            self.root.save_data()

    """ This function decreases the quantity of the selected product by one inside the List Box """

    def decrease_quantity(self):
        selected_index = self.list_box.curselection()

        # Check if the selected row is not empty:
        if selected_index != ():
            row_index = selected_index[0]

            # Extract the barcode number from frame.groceries_as_rows:
            self.barcode_number = self.groceries_as_rows[row_index]

            # Pause the comparing_thread while the customer is trying to decrease the selected product quantity:
            self.root.pause_event.set()
            print("\nThe comparing_thread is paused")

            print(
                f"\nThe total weight inside the cart before the customer decrease his product is: {self.root.current_weight} Kg")

            measured_weight = self.root.current_weight
            deviation_range = 0.02  # Define maximum deviation of 20 grams (0.02 Kg), in case of the Weight Scale isn't accurate.

            # Wait until the customer will Decrease the product quantity:
            while measured_weight + deviation_range >= self.root.current_weight:

                # Measuring weight and convert its unit to Kg:
                measured_weight = self.root.hx.get_weight_mean(readings=15) / 1000

                if measured_weight < 0:
                    measured_weight = 0

                print("\nInside while loop...")
                print(f"The measured_weight is: {round(measured_weight, 3)}")

            # Resume the comparing_thread when the customer finished to decrease his product:
            self.root.pause_event.clear()
            print("\nThe comparing_thread is resumed")

            # Check if this product has barcode or not:
            if self.customer.groceries_dict[self.barcode_number][
                3] != None:  # if True means this product has a barcode.

                # Decrease the quantity of the selected product by one:
                self.customer.groceries_dict[self.barcode_number][3] -= 1
                self.product_price = self.customer.groceries_dict[self.barcode_number][1]

                # Update the total price that the customer needs to pay:
                self.customer.price_to_pay -= self.product_price

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight -= self.customer.groceries_dict[self.barcode_number][
                    2]  # Subtract the weight of the product.
                round(self.customer.total_weight, 3)


            else:  # If we get here it means this product hasn't a barcode:

                self.reduced_weight = round(self.root.current_weight - measured_weight, 3)
                print(f"\nThe reduced weight is: {self.reduced_weight}")

                # Decrease the "total" weight of the selected product by self.reduced_weight:
                self.customer.groceries_dict[self.barcode_number][2] -= self.reduced_weight

                # Set the "total" product weight to zero in case the weight scale has measured a negative weight:
                if self.customer.groceries_dict[self.barcode_number][2] < 0.0:
                    self.customer.groceries_dict[self.barcode_number][2] = 0.0

                # Update the total price that the customer needs to pay:
                self.product_price_per_one_Kg = self.customer.groceries_dict[self.barcode_number][1]
                self.customer.price_to_pay -= round(self.product_price_per_one_Kg * self.reduced_weight, 2)
                if self.customer.price_to_pay < 0.0:
                    self.customer.price_to_pay = 0.0

                round(self.customer.price_to_pay, 2)
                print(
                    f"\nAfter the customer pressed on 'decrease quantity' button, he has to pay: {round(self.customer.price_to_pay, 2)}")

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight -= self.reduced_weight

                if self.customer.total_weight < 0.0:
                    self.customer.total_weight = 0.0

                round(self.customer.total_weight, 3)
                print(
                    f"\nAfter the customer pressed on 'decrease quantity' button, the total weight is: {round(self.customer.total_weight, 3)}")

            # Update the purchase_amount label on the HomeFrame:
            self.root.purchase_amount_var.set(get_display(f'סכום הקנייה: {round(self.customer.price_to_pay, 2)} ש"ח'))

            # Update the amount_to_pay_text variable inside PaymentFrame:
            PaymentFrame = self.root.frames["PaymentFrame"]
            PaymentFrame.amount_to_pay_text.set(get_display(f'סכום לתשלום: {round(self.customer.price_to_pay, 2)} ש"ח'))

            # Delete the product from the list_box:
            self.list_box.delete(selected_index)

            self.product_name = self.customer.groceries_dict[self.barcode_number][0]
            self.product_price = self.customer.groceries_dict[self.barcode_number][1]
            self.product_weight = self.customer.groceries_dict[self.barcode_number][2]
            self.product_quantity = self.customer.groceries_dict[self.barcode_number][3]

            # Check if the product has a barcode or not:
            if self.product_quantity is not None:

                # If after the decrease_quantity_button is pressed the quantity of the
                # selected product is 0 we have to delete the entire product from self.groceries_as_rows:
                if self.product_quantity == 0:
                    del self.groceries_as_rows[row_index]

                elif self.product_quantity > 0:
                    # Add the product to the list_box in the same row it was with the updated quantity:
                    self.list_box.insert(selected_index, get_display(
                        f'{self.product_name} ({self.product_quantity} יחידות) - {round(self.product_price * self.product_quantity, 2)} ש"ח').rjust(
                        120))  # Adjust the width as needed

            else:  # The product hasn't a barcode.

                if self.product_weight >= 0.02:  # The "total" weight of this specific product only is > 20 grams (20 grams is the threshold weight)
                    self.list_box.insert(selected_index, get_display(
                        f'{self.product_name} ({round(self.product_weight, 3)} ק"ג) - {round(self.product_price_per_one_Kg * self.product_weight, 2)} ש"ח').rjust(
                        120))  # Adjust the width as needed


                else:  # The "total" weight of this specific product only is ~0 (almost 0, Let's say less then 20 grams) so delete it:
                    del self.groceries_as_rows[row_index]

            # Update the groceries_content list:
            converted_text = [get_display(line) for line in self.list_box.get(0,
                                                                              tk.END)]  # convert each line in the list box from BidiDiplay type into regular type.
            self.customer.groceries_content_list = '\n'.join(
                converted_text)  # self.list_box.get(0, tk.END) returns the whole content inside the list_box.

        # Store the application data inside "app_data.json" file:
        self.root.save_data()

    """ This function deletes product from the List Box """

    def delete_product(self):
        selected_index = self.list_box.curselection()

        if selected_index != ():
            row_index = selected_index[0]

            # Pause the comparing_thread while the customer is trying to remove the selected product:
            self.root.pause_event.set()
            print("\nThe comparing_thread is paused")

            print(
                f"\nThe total weight inside the cart before the customer remove his product is: {self.root.current_weight} Kg")

            measured_weight = self.root.current_weight
            deviation_range = 0.02  # Define maximum deviation of 20 grams (0.02 Kg), in case of the Weight Scale isn't accurate.

            # Wait until the customer will remove the product:
            while measured_weight + deviation_range >= self.root.current_weight:

                # Measuring weight and convert its unit to Kg:
                measured_weight = self.root.hx.get_weight_mean(readings=15) / 1000

                if measured_weight < 0:
                    measured_weight = 0

                print("\nInside while loop...")
                print(f"The measured_weight is: {round(measured_weight, 3)}")

            # Delete the product from the list_box:
            self.list_box.delete(selected_index)

            # Update the groceries_content list:
            converted_text = [get_display(line) for line in self.list_box.get(0,
                                                                              tk.END)]  # convert each line in the list box from BidiDiplay type into regular type.
            self.customer.groceries_content_list = '\n'.join(
                converted_text)  # self.list_box.get(0, tk.END) returns the whole content inside the list_box.

            # Extract the barcode number from frame.groceries_as_rows before frame.current_row will be decreased.
            self.barcode_number = self.groceries_as_rows[row_index]

            # Delete this product from self.groceries_as_rows:
            del self.groceries_as_rows[row_index]

            # Update the total price that the customer needs to pay:
            if self.barcode_number == "תפוח" or self.barcode_number == "תפוז" or self.barcode_number == "מלפפון":

                self.price_per_one_Kg = self.customer.groceries_dict[self.barcode_number][1]
                self.product_weight = self.customer.groceries_dict[self.barcode_number][2]

                # Update the total price the customer needs to pay:
                self.customer.price_to_pay -= (self.price_per_one_Kg * self.product_weight)
                self.customer.price_to_pay = round(self.customer.price_to_pay, 2)

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight -= self.product_weight
                self.customer.total_weight = round(self.customer.total_weight, 3)

            else:
                self.product_price = self.customer.groceries_dict[self.barcode_number][1]
                self.product_quantity = self.customer.groceries_dict[self.barcode_number][3]

                # Update the total price the customer needs to pay:
                self.customer.price_to_pay -= (self.product_price * self.product_quantity)
                self.customer.price_to_pay = round(self.customer.price_to_pay, 2)

                # Update the total weight that should be in the cart according to the groceries reported by the customer:
                self.customer.total_weight -= self.customer.groceries_dict[self.barcode_number][
                                                  2] * self.product_quantity  # Subtract the weight of the product multiplied by product quantity.
                self.customer.total_weight = round(self.customer.total_weight, 3)

            if self.customer.price_to_pay < 0.0:
                self.customer.price_to_pay = 0.0

            # Update the purchase_amount label on the HomeFrame:
            self.root.purchase_amount_var.set(get_display(f'סכום הקנייה: {round(self.customer.price_to_pay, 2)} ש"ח'))

            # Delete this product from self.customer.groceries_dict:
            del self.customer.groceries_dict[self.barcode_number]

        # Update the amount_to_pay_text variable inside PaymentFrame:
        PaymentFrame = self.root.frames["PaymentFrame"]
        PaymentFrame.amount_to_pay_text.set(get_display(f'סכום לתשלום: {round(self.customer.price_to_pay, 2)} ש"ח'))

        # Store the application data inside "app_data.json" file:
        self.root.save_data()

        # Resume the comparing_thread when the customer finished to decrease his product:
        self.root.pause_event.clear()
        print("\nThe comparing_thread is resumed")

    """ This function inserts product into the List Box """

    def insert_product(self, barcode_number, product_name, product_quantity, product_weight=None):

        if product_weight is None:  # Means that this product has a barcode:
            self.product_price = self.customer.groceries_dict[barcode_number][
                1]  # Price per one unit from this product.

        else:  # Means that this product hasn't a barcode:
            self.product_price_per_one_Kg = self.customer.groceries_dict[barcode_number][
                1]  # Price per one Kg from this product.

        # First, check if this product already exist in self.groceries_as_rows:
        if barcode_number in self.groceries_as_rows:
            # Search the appropriate row (index) to this product:
            for row_index in range(len(self.groceries_as_rows)):
                if self.groceries_as_rows[row_index] == barcode_number:
                    selected_index = (row_index,)

                    # Delete the product from the list_box and then add it again with the updated quantity:
                    self.list_box.delete(selected_index)

                    # Add the product again with the updated quantity,
                    # Check first if this product has barcode or not:
                    if barcode_number == "תפוח" or barcode_number == "תפוז" or barcode_number == "מלפפון":
                        self.list_box.insert(selected_index, get_display(
                            f'{product_name} ({product_weight} ק"ג) - {round(self.product_price_per_one_Kg * product_weight, 2)} ש"ח').rjust(
                            120))  # Adjust the width as needed

                    else:
                        self.list_box.insert(selected_index, get_display(
                            f'{product_name} ({product_quantity} יחידות) - {round(self.product_price * product_quantity, 2)} ש"ח').rjust(
                            120))  # Adjust the width as needed

                    # Update the groceries_content list:
                    converted_text = [get_display(line) for line in self.list_box.get(0,
                                                                                      tk.END)]  # convert each line in the list box from BidiDiplay type into regular type.
                    self.customer.groceries_content_list = '\n'.join(
                        converted_text)  # self.list_box.get(0, tk.END) returns the whole content inside the list_box.

        # If the product wasn't exist before, add it now:
        else:
            self.groceries_as_rows.append(barcode_number)
            selected_index = len(self.groceries_as_rows) - 1

            if barcode_number == "תפוח" or barcode_number == "תפוז" or barcode_number == "מלפפון":
                self.list_box.insert(selected_index, get_display(
                    f'{product_name} ({product_weight} ק"ג) - {round(self.product_price_per_one_Kg * product_weight, 2)} ש"ח').rjust(
                    120))  # Adjust the width as needed

            else:
                self.list_box.insert(tk.END, get_display(
                    f'{product_name} ({product_quantity} יחידות) - {round(self.product_price * product_quantity, 2)} ש"ח').rjust(
                    120))  # Adjust the width as needed

            # Update the groceries_content list:
            converted_text = [get_display(line) for line in self.list_box.get(0,
                                                                              tk.END)]  # convert each line in the list box from BidiDiplay type into regular type.
            self.customer.groceries_content_list = '\n'.join(
                converted_text)  # self.list_box.get(0, tk.END) returns the whole content inside the list_box.

        # Store the application data inside "app_data.json" file:
        self.root.save_data()


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This frame will handle the payment process by credit card """


class PaymentFrame(tk.Frame):
    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        # Create an email_address label:
        self.email_address_text = tk.StringVar()

        self.email_address_label = tk.Label(self, textvariable=self.email_address_text, bg=self.root.bg_color,
                                            fg="white",
                                            font=("Arial", 24, 'bold'))

        self.email_address_label.grid(row=0, column=0, padx=(100, 0), pady=(10, 0))

        # Create an StringVar object:
        self.amount_to_pay_text = tk.StringVar()
        self.amount_to_pay_text.set(get_display(f'סכום לתשלום: {0} ש"ח'))

        # Create an amount to pay label:
        self.amount_to_pay_label = tk.Label(self, textvariable=self.amount_to_pay_text, bg=self.root.bg_color,
                                            fg="white",
                                            font=("Arial", 24, 'bold'))

        self.amount_to_pay_label.grid(row=1, column=0, padx=(80, 0), pady=(50, 0))

        # Create an StringVar object:
        self.credit_card_message_text = tk.StringVar()
        self.credit_card_message_text.set("")

        # Create an credit_card_message label:
        self.credit_card_message_label = tk.Label(self, textvariable=self.credit_card_message_text,
                                                  bg=self.root.bg_color, fg="white",
                                                  font=("Arial", 24, 'bold'))

        self.credit_card_message_label.grid(row=2, column=0, padx=(100, 0), pady=(50, 0))

        # Create a pay button:
        self.pay_button = tk.Button(self, text=get_display("שלם"),
                                    font=('Arial', 24, 'bold'), bg="#308014", fg="white",
                                    cursor="hand2", activebackground="#badee2",
                                    activeforeground="black",
                                    command=lambda: self.payment_with_credit_card())

        self.pay_button.grid(row=3, column=0, padx=(0, 100), pady=(80, 0))

        # Create a back button:
        self.back_button = tk.Button(self, text=get_display("חזור"),
                                     font=('Arial', 24, 'bold'), bg="orange", fg="white",
                                     cursor="hand2", activebackground="#badee2",
                                     activeforeground="black",
                                     command=lambda: self.back_button_is_pressed())

        self.back_button.grid(row=3, column=0, padx=(200, 0), pady=(80, 0))

    def back_button_is_pressed(self):
        # Save the current frame being display:
        self.root.current_frame = "HomeFrame"
        self.root.show_page("HomeFrame")

    def payment_with_credit_card(self):
        # ----------------------------------------------- First internal function ----------------------------------------------
        def scan_credit_card_is_done(credit_card_num):
            if credit_card_num is not None:
                self.customer.credit_card_number = credit_card_num

                # Store the application data inside "app_data.json" file:
                self.root.save_data()

                send_email(self.customer.email_address, self.customer.credit_card_number, self.customer.price_to_pay,
                           self.customer.groceries_content_list)

                self.credit_card_message_text.set(get_display("התשלום בוצע בהצלחה\nקבלה נשלחה למייל"))

                self.after(100, restart_app)

        # ----------------------------------------------------------------------------------------------------------------

        # ----------------------------------------------- Second internal function ----------------------------------------------
        def restart_app():
            # Pause the comparing_thread when the after the customer successfully paid:
            self.root.pause_event.set()

            play_audio('payment_approval.wav')
            Send_Data_To_MainComputer(self.customer.groceries_dict)

            # Get the HomeFrame instance:
            HomeFrame = self.root.frames["HomeFrame"]

            # Reset the whole customer's parameters before the next client and display the Starting Frame again:
            HomeFrame.resetAll()

        # ----------------------------------------------------------------------------------------------------------------

        self.credit_card_message_text.set(get_display("הצמד את כרטיס האשראי אל הסורק"))

        # call to the function that handle the RFID-RC522 after 0.1 second:
        self.after(100, scan_credit_card,
                   scan_credit_card_is_done)  # tk.Frame.after() behave like time.sleep() if pass to her only the time parameter.)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This frame will allow to add fruits and vegetables and handle the products without barcode """


class ProductsWithOutBarcodeFrame(tk.Frame):
    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        self.product_name = None
        self.product_price_per_one_Kg = None

        self.excel_file_handler = None

        # Create a button for apple:
        self.apple_button = tk.Button(self, text=get_display("תפוח"),
                                      font=('Arial', 24, 'bold'), bg="#308014", fg="white",
                                      cursor="hand2", activebackground="#badee2",
                                      activeforeground="black",
                                      command=lambda: self.manage_products_selection("תפוח"))
        self.apple_button.grid(row=0, column=0, sticky='w', padx=(250, 0), pady=(50, 0))

        # Create a button for orange:
        self.orange_button = tk.Button(self, text=get_display("תפוז"),
                                       font=('Arial', 24, 'bold'), bg="orange", fg="white",
                                       cursor="hand2", activebackground="#badee2",
                                       activeforeground="black",
                                       command=lambda: self.manage_products_selection("תפוז"))
        self.orange_button.grid(row=0, column=0, sticky='w', padx=(500, 0), pady=(50, 0))

        # Create a button for cucumber:
        self.cucumber_button = tk.Button(self, text=get_display("מלפפון"),
                                         font=('Arial', 24, 'bold'), bg="#836FFF", fg="white",
                                         cursor="hand2", activebackground="#badee2",
                                         activeforeground="black",
                                         command=lambda: self.manage_products_selection("מלפפון"))
        self.cucumber_button.grid(row=1, column=0, sticky='w', padx=(350, 0), pady=(50, 0))

        # Create label message:
        self.text_msg = tk.StringVar()

        self.label_msg = tk.Label(self, textvariable=self.text_msg, bg=self.root.bg_color, fg="white",
                                  font=("Arial", 24, 'bold'))
        self.label_msg.grid(row=2, column=0, sticky='w', padx=(25, 0), pady=(50, 0))

        # Create a back button:
        self.back_button = tk.Button(self, text=get_display("חזור"),
                                     font=('Arial', 24, 'bold'), bg="red4", fg="white",
                                     cursor="hand2", activebackground="#badee2",
                                     activeforeground="black",
                                     command=lambda: self.back_button_pressed())

        self.back_button.grid(row=3, column=0, sticky='w', padx=(365, 0), pady=(25, 0))

        # Create a finish button:
        self.finish_button = tk.Button(self, text=get_display("סיום"),
                                       font=('Arial', 24, 'bold'), bg="#4876FF", fg="white",
                                       cursor="hand2", activebackground="#badee2",
                                       activeforeground="black",
                                       command=lambda: self.finish_button_pressed())

    def back_button_pressed(self):
        self.text_msg.set("")  # Clear the label content for the next time.
        self.product_price_per_one_Kg = None  # Reset this variable for the next time.

        # Make the buttons responsive:
        self.apple_button['state'] = self.orange_button['state'] = self.cucumber_button['state'] = tk.NORMAL

        # Resume the comparing_thread when the customer finished to weight his product:
        if self.root.pause_event.is_set():
            self.root.pause_event.clear()
            print("\nThe comparing_thread is resumed")

        self.root.current_frame = "HomeFrame"
        self.root.show_page("HomeFrame")

    def manage_products_selection(self, product_name):

        # Make the buttons unresponsive:
        self.apple_button['state'] = self.orange_button['state'] = self.cucumber_button['state'] = tk.DISABLED

        self.product_name = product_name

        # Store the weight inside the cart before the customer insert his products:
        self.root.old_weight = self.root.current_weight

        self.excel_file_handler = pd.read_excel(self.root.excel_file_path)

        # Find the price per one Kg of this specific product:
        self.product_price_per_one_Kg = \
        self.excel_file_handler.loc[self.excel_file_handler['מספר ברקוד'] == product_name, 'מחיר המוצר [ש"ח]'].iloc[0]

        self.back_button.grid(row=3, column=0, sticky='w', padx=(300, 0), pady=(25, 0))

        # Unhide the "סיום" button:
        self.finish_button.grid(row=3, column=0, sticky='w', padx=(450, 0), pady=(25, 0))

        # self.excel_file_handler.close()
        self.text_msg.set(get_display("הנח את המוצרים בתוך העגלה ולחץ סיום לאחר מכן.\nהמתן בזמן שהמוצר נשקל..."))

        self.after(100, self.play_audio_for_weight_scale)

        # Pause the comparing_thread while the customer is trying to add his product without a barcode:
        self.root.pause_event.set()
        print("\nThe comparing_thread is paused...")

    def play_audio_for_weight_scale(self):
        # Play recording:
        play_audio("put_your_products_on_weight_scale.wav")

    def finish_button_pressed(self):

        # Measuring the current weight after the customer add his product to the cart:
        self.root.current_weight = self.root.hx.get_weight_mean(readings=15) / 1000

        # Calc the weight that added to the cart (For example 0.5 Kg of apples):
        added_weight = round(self.root.current_weight - self.root.old_weight, 3)

        # Calc the cost of the specific product by his weight (For example the cost of 0.5 Kg of apples is 6.5 ש"ח)
        product_cost = round(added_weight * self.product_price_per_one_Kg, 2)

        # Update the total price to pay for the customer:
        self.customer.price_to_pay += product_cost

        # Update the total weight that should be in the cart:
        self.customer.total_weight += added_weight
        round(self.customer.total_weight, 3)

        # Update the purchase_amount label in the HomeFrame:
        self.root.purchase_amount_var.set(get_display(f'סכום הקנייה: {round(self.customer.price_to_pay, 2)} ש"ח'))

        # Update the amount_to_pay_text variable inside PaymentFrame:
        PaymentFrame = self.root.frames["PaymentFrame"]
        PaymentFrame.amount_to_pay_text.set(get_display(f'סכום לתשלום: {round(self.customer.price_to_pay, 2)} ש"ח'))

        """ Add product to the groceries' dictionary and
                check if the customer already add this product before, if so increase the quantity of this product by self.product_quantity: """
        if self.product_name in self.customer.groceries_dict.keys():
            # Reminder - products without a barcode, the barcode number and the product name are the same.

            # The quantity of product like apple or orange doesn't matter,
            # what is matter is the price per Kg and the added weight of this product.
            self.customer.groceries_dict[self.product_name][3] = None

            self.customer.groceries_dict[self.product_name][
                2] += added_weight  # Update the weight of this product inside the customer.groceries_dict.

        # If the product not added before, update groceries_dict now:
        else:
            self.customer.groceries_dict[self.product_name] = [self.product_name, self.product_price_per_one_Kg,
                                                               added_weight, None]

            # If some reason the added_weight is 0 Kg, there is no need to insert the product into ListBox.
        if added_weight > 0:
            # Insert product into ListBox (סל הקניות) if product exists:
            ShowGroceriesFrame = self.root.frames["ShowGroceriesFrame"]

            # Reminder - products without a barcode, the barcode number and the product name are the same.
            ShowGroceriesFrame.insert_product(self.product_name, self.product_name,
                                              self.customer.groceries_dict[self.product_name][3],
                                              self.customer.groceries_dict[self.product_name][2])

        # Resume the comparing_thread when the customer finished to add his product without a barcode:
        self.root.pause_event.clear()
        print("\nThe comparing_thread is resumed...")

        # Hide the "סיום" button:
        self.finish_button.grid_forget()

        # Move the "חזור" button back to the center of the frame:
        self.back_button.grid(row=3, column=0, sticky='w', padx=(365, 0), pady=(25, 0))

        # Make the buttons responsive:
        self.apple_button['state'] = self.orange_button['state'] = self.cucumber_button['state'] = tk.NORMAL

        # Clean the label:
        self.text_msg.set("")

        # Store the application data inside "app_data.json" file:
        self.root.save_data()

        # Go back to the HomeFrame:
        self.root.show_page("HomeFrame")


# ----------------------------------------------------------------------------------------------------------------------------------------------------------

""" This frame will alert about theft attemption """


class TheftWarningFrame(tk.Frame):
    def __init__(self, root, customer):
        # Initialize parent constructor (tk.Frame)
        tk.Frame.__init__(self, root, width=root.width_frame, height=root.height_frame,
                          bg=root.bg_color)

        self.root = root
        self.customer = customer

        # Create a warning label:
        self.text_msg = tk.StringVar()
        self.text_msg.set(get_display("המערכת זיהתה עודף מושקל!\nאנא הסר את המוצר שהוספסת"))

        self.warning_label = tk.Label(self, textvariable=self.text_msg, bg=self.root.bg_color, fg="white",
                                      font=("Arial", 26, 'bold'))

        self.warning_label.grid(row=0, column=0, padx=150, pady=150)