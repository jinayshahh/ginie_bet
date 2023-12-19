import random
from twilio.rest import Client

# Twilio account credentials
TWILIO_SID = 'AC3d75f35ec0aa2369c303eb51a2bf35dc'
TWILIO_AUTH_TOKEN = 'eb55ccc2ddb751e0c65f04931bc3ca67'
TWILIO_PHONE_NUMBER = '+14175453286'


# Generate a random OTP
def generate_otp():
    return random.randint(1000, 9999)


# Send OTP to the user's phone number using Twilio
def send_otp(phone_number, otp):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your OTP: {otp}",
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    print(f"OTP sent to {phone_number}.")


# Check if the provided phone number exists in the users.csv file
import pandas as pd

def check_existing_user(phone_number):
    try:
        df = pd.read_csv('csv/users.csv')
        phone_numbers = df['Phone Number'].tolist()
        for num in phone_numbers:
            if phone_number == '+' + str(num):
                return True
    except FileNotFoundError:
        pass
    return False




# Register a new user or send OTP to an existing user
def login_user():
    # Get user's phone number
    phone_number = input("Enter your phone number: ")

    # Check if the phone number exists in the users.csv file
    if check_existing_user(phone_number):
        # Generate and send OTP
        otp = generate_otp()
        send_otp(phone_number, otp)

        # Validate OTP
        entered_otp = input("Enter the OTP you received: ")
        if int(entered_otp) != otp:
            print("Invalid OTP. Login failed.")
            return
        df = pd.read_csv('csv/users.csv')
        user_name = str(df['Name'].values[0])
        print(f"OTP validated. Login successful! Welcome {user_name}")

    else:
        print("Phone number not found. Registration required.")


# Register a new user or send OTP to an existing user
login_user()



