import mysql.connector
conn = mysql.connector.connect(
    user="root",
    password="abcd1234",
    host="localhost",
    database="ginie_bet",
    port="3306"
)
mycur = conn.cursor()
game_name = 'Fantasy league'
def entry_fee(entry_fee_key):
    return entry_fee_key


# Initialize user balance
def check_balance(balance):
    if balance >= entry_fee:
        return True


def greet_user():
    rules = [
        "You will be deducted 1000 points from your balance.",
        "Answer a series of questions correctly to win points.",
        "Each correct answer earns you 1000 points.",
        "If you answer all the questions correctly, you win!",
        "If you answer incorrectly, you lose and can try again."
    ]
    return rules


def check_answers(answers, correct_answers, user_name, match_name_correct):
    correct_count = 0
    pass_count = 0
    void_count = 0
    correct_answer_number_void = 1
    correct_answer_number_pass = 1
    correct_answer_number_yes = 1
    attempt_count = len(answers)
    result = []
    for user_answer, correct_answer in zip(answers, correct_answers):
        if user_answer == 'Pass':
            pass_count += 1
            mycur.execute(
                f"UPDATE check_answer_ginie_bet SET answer_{correct_answer_number_pass} = 'Pass' where user_name = "
                f"'{user_name}' and match_name = '{match_name_correct}'")
            conn.commit()
            print(user_name, match_name_correct, correct_answer_number_pass, "PASS")
        elif user_answer.lower() == correct_answer.lower():
            result.append([user_answer, correct_answer])
            correct_count += 1
            mycur.execute(
                f"UPDATE check_answer_ginie_bet SET answer_{correct_answer_number_yes} = 'yes' where user_name = "
                f"'{user_name}' and match_name = '{match_name_correct}'")
            conn.commit()
            print(user_name, match_name_correct, correct_answer_number_yes, "YES")
        else:
            mycur.execute(
                f"UPDATE check_answer_ginie_bet SET answer_{correct_answer_number_yes} = 'no' where user_name = "
                f"'{user_name}' and match_name = '{match_name_correct}'")
            conn.commit()
        correct_answer_number_yes += 1
        correct_answer_number_pass += 1
    mycur.execute(
        f"UPDATE check_answer_ginie_bet SET void_count = '{void_count}' where user_name = "
        f"'{user_name}' and match_name = '{match_name_correct}'")
    conn.commit()
    for correct_answer in correct_answers:
        if correct_answer == "NULL AND VOID":
            correct_count += 1
            void_count += 1
            mycur.execute(
                f"UPDATE check_answer_ginie_bet SET answer_{correct_answer_number_void} = 'void' where user_name = "
                f"'{user_name}' and match_name = '{match_name_correct}'")
            conn.commit()
            print(user_name, match_name_correct, correct_answer_number_void)
        correct_answer_number_void += 1
    return correct_count, pass_count, void_count, attempt_count


from datetime import datetime, timedelta
import time

def time_count():# Define the target date and time
    target_date = datetime(2023, 9, 24, 17, 0)  # 24th September 2023, 5 PM

    while True:
        # Get the current date and time
        current_date = datetime.now()

        # Calculate the time difference
        time_left = target_date - current_date

        # Break the loop if the target date has passed
        if time_left.total_seconds() <= 0:
            print("Countdown reached!")
            break

        # Extract days, hours, minutes, and seconds
        days_left = time_left.days
        hours_left = time_left.seconds // 3600
        minutes_left = (time_left.seconds % 3600) // 60
        seconds_left = time_left.seconds % 60

        print(f"Countdown: {days_left} days, {hours_left} hours, {minutes_left} minutes, {seconds_left} seconds")

        # Wait for one second before the next update
        time.sleep(1)
