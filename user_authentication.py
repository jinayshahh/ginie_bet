import random
import pandas as pd
import mysql.connector
# from twilio.rest import Client
#
# # Twilio account credentials
# TWILIO_SID = 'AC3d75f35ec0aa2369c303eb51a2bf35dc'
# TWILIO_AUTH_TOKEN = 'eb55ccc2ddb751e0c65f04931bc3ca67'
# TWILIO_PHONE_NUMBER = '+14175453286'

from datetime import datetime

current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

admin_id = "7777"
admin = False

check_number = []

conn = mysql.connector.connect(
    user="root",
    password="abcd1234",
    host="localhost",
    database="ginie_bet",
    port="3306"
)

mycur = conn.cursor()

mycur.execute('select * from ginie_bet.user_data')

users = mycur.fetchall()


# for user in users:
#     # print(user)
#     print('id : ' + user[1])
#     print(f'first name: {user[2]}')

def get_users_dataframe():
    df = pd.read_csv('csv/users.csv')
    return df


# Generate a random OTP
def generate_otp():
    return random.randint(1000, 9999)


# Send OTP to the user's phone number using Twilio
# def send_otp(phone_number, otp):
#     client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
#     message = client.messages.create(
#         body=f"Your OTP: {otp}",
#         from_=TWILIO_PHONE_NUMBER,
#         to=phone_number
#     )
#     print(f"OTP sent to {phone_number}.")


# Check if the provided phone number exists in the users.csv file
# def check_existing_user(phone_number):
#     user = User.query.filter_by(phone_number=phone_number).first()
#     return user is not None

def check_existing_user(phone_number):
    try:
        if phone_number == 7777:
            global admin
            admin = True
            return True
        else:
            for user in users:
                phone_numbers = user[3]
                # print(phone_numbers)
                check_number.append(phone_numbers)
            for num in check_number:
                if int(phone_number) == int(num):
                    return True
                else:
                    pass
    except FileNotFoundError:
        pass
    return False


# Register a new user or send OTP to an existing user
def register_user(phone_number):
    if not check_existing_user(phone_number):
        # Generate and send OTP
        otp = generate_otp()
        # send_otp(phone_number, otp)

        # Validate OTP
        entered_otp = input("Enter the OTP you received: ")
        if int(entered_otp) != otp:
            print("Invalid OTP. Registration failed.")
            return

        # Get user's name
        name = input("Enter your name: ").title()
        number = len(users[0]) + 1

        # Store user's data in a DataFrame
        mycur.execute(f"INSERT INTO user_data (user_id, user_name, user_number, register_time, last_login) "
                      f"VALUES ({number}, '{name}', {phone_number}, '{formatted_datetime}', '{formatted_datetime}');")

        conn.commit()

        print("Registration successful!")
    else:
        print("User already exists, please log in")


# Login the user or send OTP for validation
def login_user(phone_number):
    if check_existing_user(phone_number):
        # Generate and send OTP
        otp = generate_otp()
        print(otp)
        # send_otp(phone_number, otp)

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
