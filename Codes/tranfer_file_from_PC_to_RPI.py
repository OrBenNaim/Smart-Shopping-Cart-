import paramiko

""" This file should to execute from PC and Not from Raspberry Pi. 
    The goal of this python file is to send a Excel file (Or other file such as py file, etc.) from PC 
    to several Raspberry Pi in parallel via ssh connection. """


# Define the IP addresses of your Raspberry Pi devices and the path to your Excel file.
raspberry_pi_ips = ["172.20.10.8"]     # 172.20.10.8 is the IP of my RPI when connected to "Or's IPhone" presonal hotspot network.

excel_file_path = r'C:\Electrical and Electronics Engineering\Semester 9\Engineering Design B\Final_Project\Groceries_Info.xlsx'

# SSH credentials for the Raspberry Pi (replace with your own username and password).
ssh_username = "orbennaim1"
ssh_password = "Or208019703"

# Loop through each Raspberry Pi and transfer the CSV file.
for pi_ip in raspberry_pi_ips:
    try:
        # Create an SSH client
        ssh_client = paramiko.SSHClient()

        # Automatically add the Raspberry Pi to the list of known hosts (disable in production).
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the Raspberry Pi.
        ssh_client.connect(pi_ip, username=ssh_username, password=ssh_password)

        # SFTP (Secure File Transfer Protocol) to the Raspberry Pi.
        with ssh_client.open_sftp() as sftp:
            # Define the destination path on the Raspberry Pi.
            destination_path = '/home/orbennaim1/Desktop/Final_Project/Groceries_Info.xlsx'

            # Transfer the Excel file.
            sftp.put(excel_file_path, destination_path)
            print(f"Transferred {excel_file_path} to {pi_ip}:{destination_path}")

        # Close the SSH connection.
        ssh_client.close()

    except Exception as e:
        print(f"Failed to transfer to {pi_ip}: {str(e)}")

print("\nAll transfers completed.\n")
