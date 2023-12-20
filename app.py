#
#
#
# begin app
#
#
#
from flask import Flask, request, redirect, session, render_template, jsonify, url_for
import requests
# from twilio.rest import Client
from user_authentication import generate_otp, check_existing_user
# from sport_selection import get_upcoming_matches
import mysql.connector
from sports_creation import sport_number
from datetime import datetime, time
import time
from ginie_bet import greet_user, check_answers, game_name
import random
import re
import os
import secrets
import string

#
#
#
# all functions
#
#
#

current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
current_number = []
sport_options = []
answers = []
asked_questions = []
admin_pool = 0


def admin_password_generator():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password_length = 20  # You can adjust the length as needed
    password = ''.join(secrets.choice(alphabet) for _ in range(password_length))
    return password

admin_password = None
authentication_password_used = False
no_user_exists = False
admin = False
blocked_users = set()  # Initialize an empty set

# # Twilio account credentials
# TWILIO_SID = 'AC3d75f35ec0aa2369c303eb51a2bf35dc'
# TWILIO_AUTH_TOKEN = 'eb55ccc2ddb751e0c65f04931bc3ca67'
# TWILIO_PHONE_NUMBER = '+14175453286'
api_key_google_maps = 'AIzaSyBt6PwymNiwmj7hTXaypG1-aGTAa8I9N8E'  # Replace with your Google Maps API key

conn = mysql.connector.connect(
    user="root",
    password="abcd1234",
    host="localhost",
    database="ginie_bet",
    port="3306"
)
mycur = conn.cursor(buffered=True)
mycur.execute('select * from ginie_bet.user_data')
users = mycur.fetchall()
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Configure the upload folder within the "static" directory
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mycur.execute("SELECT * FROM ginie_bet.sports_creation where soft_delete != 'yes'")
sports = mycur.fetchall()
for sport in sports:
    sport_options.append(sport)

sport_number = sport_number()

mycur.execute("SELECT user_id from user_data where status='BLOCK'")
blocked_users_list = mycur.fetchall()
conn.commit()
print(blocked_users)
# can_play = True
# can_withdraw = True

if blocked_users_list:
    for blocked_user in blocked_users_list:
        blocked_users.add(blocked_user[0])  # Extract the value from the tuple
        print(blocked_user)


def admin_record_pool():
    # for admin pool
    mycur.execute('SELECT id FROM admin_record ORDER BY id DESC LIMIT 1')
    admin_id_tuple = mycur.fetchone()
    if admin_id_tuple:
        admin_id = admin_id_tuple[0] if admin_id_tuple else None
        num_records_admin_current = admin_id + 1
        current_record = admin_id
        mycur.execute(f'SELECT balance FROM admin_record where id="{current_record}"')
        admin_balance = mycur.fetchone()
        if admin_balance:
            admin_pool_str = str(admin_balance[0])
            admin_pool_current = int(admin_pool_str)
            return admin_pool_current, num_records_admin_current
    else:
        admin_pool_current = 0
        num_records_admin_current = 0
        return admin_pool_current, num_records_admin_current
    # end admin pool


admin_pool, num_records_admin = admin_record_pool()


def get_sport_name(sport_id):
    query = f"SELECT sports_name FROM sports_creation WHERE sports_id = {sport_id}"
    mycur.execute(query)
    result_capital = mycur.fetchone()
    if result_capital:
        result = result_capital[0].lower()
        return result
    else:
        return None


def get_match_by_dif(match_dif):
    # Assuming you have a list of matches containing dictionaries
    mycur.execute("select * from ginie_bet_selection")
    matches = mycur.fetchall()
    conn.commit()

    for match_current in matches:
        if match_current[1] == match_dif:
            return match_current

    return None  # Match not found


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}


# Function to get location name from coordinates using Google Maps Geocoding API
def get_location_name(lat, lng):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key_google_maps}'
    response = requests.get(url)
    location_data = response.json()
    if location_data['status'] == 'OK':
        return location_data['results'][0]['formatted_address']
    else:
        return 'Location name not found'

# Function to get location from IP address using Google Maps Geolocation API
def get_location(ip):
    url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={api_key_google_maps}'
    payload = {"considerIp": "true", "wifiAccessPoints": []}  # Consider IP for geolocation
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    location_data = response.json()
    if 'location' in location_data:
        lat = location_data['location']['lat']
        lng = location_data['location']['lng']
        location_name = get_location_name(lat, lng)  # Get location name from coordinates
        return location_name
    else:
        return 'Location not found'


def allowed_file(filename):
    # Check if the file extension is in the set of allowed extensions
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#
#
#
# end all functions
#
#
#

#
#
#
# basic functions
#
#
#

@app.route('/')
def home():
    return render_template("reg_log.html")


@app.route('/index_call', methods=['GET', 'POST'])
def index_call():
    return render_template('index.html', sport_options=sport_options)


@app.route('/soft_delete_sports')
def soft_delete_sports():
    mycur.execute("SELECT * from sports_creation where soft_delete = 'yes'")
    deleted_sports = mycur.fetchall()
    conn.commit()
    return render_template("soft_delete_list_sports.html", deleted_sports=deleted_sports)


@app.route('/soft_delete_multiplier')
def soft_delete_multipliers():
    mycur.execute("SELECT * from multiplier_record where soft_delete = 'yes'")
    deleted_multipliers = mycur.fetchall()
    conn.commit()
    return render_template("soft_delete_list_multiplier.html", deleted_sports=deleted_multipliers)


@app.route('/soft_delete_matches')
def soft_delete_matches():
    mycur.execute("SELECT * from matches_creation where soft_delete = 'yes'")
    deleted_sports = mycur.fetchall()
    conn.commit()
    return render_template("soft_delete_matches.html", deleted_sports=deleted_sports)


@app.route('/soft_delete_questions')
def soft_delete_questions():
    mycur.execute("SELECT * from questions_ginie_bet where soft_delete = 'yes'")
    deleted_questions = mycur.fetchall()
    conn.commit()
    return render_template("soft_delete_questions.html", deleted_sports=deleted_questions)


@app.route('/get_user/<get_user_name>', methods=['GET', 'POST'])
def get_user(get_user_name):
    mycur.execute(f"select user_id from user_data where user_name = '{get_user_name}'")
    user_id_list = mycur.fetchall()
    conn.commit()
    user_id = user_id_list[0][0]
    return redirect(url_for("user_details", userid=user_id))


@app.route('/view_all_match_stats/<match_name_stats>', methods=['GET', 'POST'])
def view_all_match_stats(match_name_stats):
    mycur.execute(f"SELECT * FROM ginie_bet.matches_creation where match_name = '{match_name_stats}'")
    match_selected_current = mycur.fetchall()
    conn.commit()
    mycur.execute(f"SELECT * FROM finances_records WHERE match_name = '{match_name_stats}'")
    current_matches = mycur.fetchall()
    conn.commit()
    return render_template("view_all_match_stats.html", match_selected=match_selected_current,
                           current_matches=current_matches)


#
#
#
# end basic functions
#
#
#

#
#
#
# delete and update function functions
#
#
#

@app.route('/delete_question', methods=['POST'])
def delete_question():
    question_id = request.form['user_id']
    match_id = session.get('match_id')
    mycur.execute(f'Update questions_ginie_bet SET soft_delete = "yes" where question_id = {question_id}')
    conn.commit()
    # Perform deletion logic for the user with the specified user_id

    return redirect(url_for('match_details', match_id=match_id))


@app.route('/delete_match', methods=['POST'])
def soft_delete_match():
    selected_match_id = request.form['user_id']
    selected_sport = session.get('selected_sport')
    mycur.execute(f'select match_name from matches_creation where match_id = {selected_match_id}')
    sport_name = mycur.fetchall()
    conn.commit()
    name_match = sport_name[0][0]
    mycur.execute(f"update ginie_bet.ginie_bet_selection set soft_delete = 'yes' WHERE match_name = '{name_match}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.matches_creation set soft_delete = 'yes' WHERE match_name = '{name_match}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.questions_ginie_bet set soft_delete = 'yes' WHERE match_name = '{name_match}'")
    conn.commit()
    mycur.execute(f"select * from matches_creation where sport_name = '{selected_sport}' AND soft_delete != 'yes'")
    matches_sport = mycur.fetchall()
    conn.commit()
    # Perform deletion logic for the user with the specified user_id
    return render_template("view_matches.html", selected_sport=selected_sport, matches_sport=matches_sport)


@app.route('/revive_match/<revive_sport_id>', methods=['POST', 'GET'])
def revive_match(revive_sport_id):
    session['revive_match_id'] = revive_sport_id
    mycur.execute(f'select match_name from matches_creation where match_id = {revive_sport_id}')
    sport_name = mycur.fetchall()
    conn.commit()
    name_sport = sport_name[0][0]
    mycur.execute(f"UPDATE ginie_bet.matches_creation SET soft_delete = 'no' WHERE match_name = '{name_sport}'")
    conn.commit()
    return redirect(url_for("all_matches"))


@app.route('/revive_question/<revive_question_id>', methods=['POST', 'GET'])
def revive_questions(revive_question_id):
    mycur.execute(f"UPDATE ginie_bet.questions_ginie_bet SET soft_delete = 'no' "
                  f"WHERE question_id = '{revive_question_id}'")
    conn.commit()
    match_id = session.get('match_id')
    return redirect(url_for('match_details', match_id=match_id))


@app.route('/all_matches', methods=['POST', 'GET'])
def all_matches():
    revive_match_id = session.get('revive_match_id')
    mycur.execute(f"select sport_name from matches_creation where match_id = '{revive_match_id}'")
    matches_sport = mycur.fetchall()
    conn.commit()
    matches_sports = matches_sport[0][0]
    mycur.execute(f"select * from matches_creation where sport_name = '{matches_sports}' and soft_delete != 'yes'")
    revived_matches = mycur.fetchall()
    conn.commit()

    # Fetch the sports from the database
    return render_template("view_matches.html", selected_sport=matches_sports, matches_sport=revived_matches)


@app.route('/revive_sport/<revive_sport_id>', methods=['POST', 'GET'])
def revive_sport(revive_sport_id):
    mycur.execute(f'select sports_name from sports_creation where sports_id = {revive_sport_id}')
    sport_name = mycur.fetchall()
    conn.commit()
    name_sport = sport_name[0][0]
    mycur.execute(f"UPDATE ginie_bet.sports_creation SET soft_delete = 'no' WHERE sports_name = '{name_sport}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.ginie_bet_selection SET soft_delete = 'no' WHERE sports_name = '{name_sport}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.matches_creation SET soft_delete = 'no' WHERE sport_name = '{name_sport}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.questions_ginie_bet SET soft_delete = 'no' WHERE name_sport = '{name_sport}'")
    conn.commit()
    # Perform deletion logic for the user with the specified user_id
    return redirect(url_for("all_sports"))


@app.route('/revive_multiplier/<revive_multiplier_id>', methods=['POST', 'GET'])
def revive_multiplier(revive_multiplier_id):
    mycur.execute(f'select multiplier_name from multiplier_record where multiplier_id = {revive_multiplier_id}')
    multiplier_name = mycur.fetchall()
    conn.commit()
    name_multiplier = multiplier_name[0][0]
    mycur.execute(f"UPDATE ginie_bet.multiplier_record SET soft_delete = 'no' "
                  f"WHERE multiplier_name = '{name_multiplier}'")
    conn.commit()
    # Perform deletion logic for the user with the specified user_id
    return redirect(url_for("all_multiplier"))


@app.route('/delete_sport', methods=['POST'])
def soft_delete_sport():
    selected_sport_id = request.form['user_id']
    mycur.execute(f'select sports_name from sports_creation where sports_id = {selected_sport_id}')
    sport_name = mycur.fetchall()
    conn.commit()
    name_sport = sport_name[0][0]
    mycur.execute(f"UPDATE ginie_bet.sports_creation SET soft_delete = 'yes' WHERE sports_name = '{name_sport}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.ginie_bet_selection SET soft_delete = 'yes' WHERE sports_name = '{name_sport}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.matches_creation SET soft_delete = 'yes' WHERE sport_name = '{name_sport}'")
    conn.commit()
    time.sleep(1)
    mycur.execute(f"UPDATE ginie_bet.questions_ginie_bet SET soft_delete = 'yes' WHERE name_sport = '{name_sport}'")
    conn.commit()
    # Perform deletion logic for the user with the specified user_id
    return


@app.route('/delete_multiplier', methods=['POST'])
def soft_delete_multiplier():
    selected_multiplier_id = request.form['user_id']
    mycur.execute(f'select multiplier_name from multiplier_record where multiplier_id = {selected_multiplier_id}')
    multiplier_name = mycur.fetchall()
    conn.commit()
    name_multiplier = multiplier_name[0][0]
    mycur.execute(f"UPDATE ginie_bet.multiplier_record SET soft_delete = 'yes' "
                  f"WHERE multiplier_name = '{name_multiplier}'")
    conn.commit()
    # Perform deletion logic for the user with the specified user_id
    return


@app.route('/update_icon/<sports_updating_id>', methods=['POST'])
def update_icon(sports_updating_id):
    if 'image' in request.files:
        mycur.execute(f"select sports_name from sports_creation where sports_id = '{sports_updating_id}'")
        sports_name_icon = mycur.fetchall()
        conn.commit()
        print(sports_name_icon[0][0])
        image_file = request.files['image']
        if image_file and allowed_file(image_file.filename):
            # Rename the uploaded image to "image_1.jpg" (or any desired format)
            filename = f"image_{sports_updating_id}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

            # Return the image URL (you may need to adjust this URL based on your server setup)
            image_url = f"/{filepath}"
            return jsonify({"url": image_url}), 200

    return jsonify({"message": "Invalid file or file not provided."}), 400


@app.route('/update_open_multiplier/<multiplier_id>', methods=['POST', 'GET'])
def update_open_multiplier(multiplier_id):
    mycur.execute("select * from multiplier_record")
    multiplier_record_update = mycur.fetchall()
    conn.commit()
    multiplier_id_int = int(multiplier_id)
    return render_template('multiplier_update.html', sports=multiplier_record_update, sport_id=multiplier_id_int)


@app.route('/update_open_sport/<sport_id>', methods=['POST', 'GET'])
def update_open_sport(sport_id):
    mycur.execute("select * from sports_creation")
    sports_sports = mycur.fetchall()
    conn.commit()
    sport_id_int = int(sport_id)
    return render_template('sport_icon_update.html', sports=sports_sports, sport_id=sport_id_int)


@app.route('/update_open_match/<sport_id>', methods=['POST', 'GET'])
def update_open_match(sport_id):
    mycur.execute("select * from matches_creation")
    sports_sports = mycur.fetchall()
    conn.commit()
    sport_id_int = int(sport_id)
    return render_template('match_icon_update.html', sports=sports_sports, sport_id=sport_id_int)


@app.route('/update_open_questions/<question_id>', methods=['POST', 'GET'])
def update_open_question(question_id):
    mycur.execute("select * from questions_ginie_bet")
    questions_ginie = mycur.fetchall()
    conn.commit()
    question_id_int = int(question_id)
    return render_template('questions_ginie_bet_update.html', sports=questions_ginie, sport_id=question_id_int)


@app.route('/multiplier_update_form/<multiplier_id>', methods=['POST'])
def update_multiplier(multiplier_id):
    if request.method == 'POST':
        multiplier_name = request.form.get('multiplier_name_update')
        multiplier_1 = request.form.get('multiplier_1_update')
        multiplier_2 = request.form.get('multiplier_2_update')
        multiplier_3 = request.form.get('multiplier_3_update')
        multiplier_4 = request.form.get('multiplier_4_update')
        multiplier_5 = request.form.get('multiplier_5_update')
        multiplier_6 = request.form.get('multiplier_6_update')
        multiplier_7 = request.form.get('multiplier_7_update')
        multiplier_8 = request.form.get('multiplier_8_update')
        multiplier_9 = request.form.get('multiplier_9_update')
        multiplier_10 = request.form.get('multiplier_10_update')
        multiplier_11 = request.form.get('multiplier_11_update')
        multiplier_12 = request.form.get('multiplier_12_update')
        multiplier_13 = request.form.get('multiplier_13_update')
        multiplier_14 = request.form.get('multiplier_14_update')
        multiplier_15 = request.form.get('multiplier_15_update')
        bumper_multiplier = request.form.get('bumper_multiplier_update')

        mycur.execute(f"UPDATE ginie_bet.multiplier_record SET multiplier_name = '{multiplier_name}', "
                      f"multiplier_one = '{multiplier_1}', multiplier_two = '{multiplier_2}', "
                      f"multiplier_three = '{multiplier_3}', multiplier_four = '{multiplier_4}', "
                      f"multiplier_five = '{multiplier_5}', multiplier_six = '{multiplier_6}', "
                      f"multiplier_seven = '{multiplier_7}', multiplier_eight = '{multiplier_8}', "
                      f"multiplier_nine = '{multiplier_9}', multiplier_ten = '{multiplier_10}', "
                      f"multiplier_eleven = '{multiplier_11}', multiplier_twelve = '{multiplier_12}', "
                      f"multiplier_thirteen = '{multiplier_13}', multiplier_fourteen = '{multiplier_14}', "
                      f"multiplier_fifteen = '{multiplier_15}', bumper_question = '{bumper_multiplier}'"
                      f" where multiplier_id = '{multiplier_id}'")

        return redirect(url_for("all_multiplier"))

    return redirect(url_for("all_sports"))


@app.route('/sports_update_form/<sport_id>', methods=['POST'])
def update_sport(sport_id):
    if request.method == 'POST':
        sports_name = request.form.get('sports_name_update')
        primary_description = request.form.get('primary_description_update')
        secondary_description = request.form.get('secondary_description_update')
        # You can now process and save these values as needed
        mycur.execute(f"UPDATE sports_creation SET sports_name = '{sports_name}', primary_description = "
                      f"'{primary_description}', secondary_description = '{secondary_description}' where "
                      f"sports_id = '{sport_id}'")

        return redirect(url_for("all_sports"))

    return redirect(url_for("all_sports"))


@app.route('/matches_update_form/<sport_id>', methods=['POST'])
def update_matches(sport_id):
    if request.method == 'POST':
        team_a = request.form.get('team_a_update')
        team_b = request.form.get('team_b_update')
        league_update = request.form.get('league_update')
        date_update = request.form.get('date_update')
        time_update = request.form.get('time_update')
        ginie_bet_name = request.form.get('ginie_bet')
        primary_description_update = request.form.get('primary_description_update')
        secondary_description_update = request.form.get('secondary_description_update')
        # You can now process and save these values as needed
        mycur.execute(f"UPDATE matches_creation SET match_name = '{team_a} vs {team_b}', team_a = '{team_a}',"
                      f" team_b = '{team_b}', team_a = '{team_a}',date = '{date_update}', time = '{time_update}',"
                      f"ginie_bet = '{ginie_bet_name}', league = '{league_update}' ,"
                      f"primary_description = '{primary_description_update}', "
                      f"secondary_description = '{secondary_description_update}' where match_id = '{sport_id}'")

        mycur.execute(f"select sport_name from matches_creation where match_id = '{sport_id}'")
        matches_sport = mycur.fetchall()
        conn.commit()
        matches_sports = matches_sport[0][0]
        mycur.execute(f"select * from matches_creation where sport_name = '{matches_sports}' and soft_delete != 'yes'")
        revived_matches = mycur.fetchall()
        conn.commit()

        # Fetch the sports from the database
        return render_template("view_matches.html", selected_sport=matches_sports, matches_sport=revived_matches)


@app.route('/question_update_form/<question_id>', methods=['POST'])
def update_question(question_id):
    if request.method == 'POST':
        question_update = request.form.get('question_update')
        option_1 = request.form.get('option_1_update')
        option_2 = request.form.get('option_2_update')
        option_3 = request.form.get('option_3_update')
        option_4 = request.form.get('option_4_update')
        mycur.execute(f"UPDATE questions_ginie_bet SET question = '{question_update}', option_1 = "
                      f"'{option_1}', option_2 = '{option_2}', option_3 = '{option_3}', option_4 = '{option_4}'"
                      f"where question_id = '{question_id}'")
        match_id = session.get('match_id')
        return redirect(url_for('match_details', match_id=match_id))


#
#
#
# end delete and update functions
#
#
#

#
#
#
# funds
#
#
#

@app.route('/generate_password_admin_button', methods=['GET'])
def generate_password_admin_button():
    # Add your Python code here
    global admin_password, authentication_password_used
    admin_password_generated = admin_password_generator()
    admin_password = admin_password_generated
    print(admin_password)
    authentication_password_used = False
    return jsonify({'message': 'Hello printed in Python'})


@app.route('/admin_ledger', methods=['GET', 'POST'])
def admin_ledger():
    mycur.execute('SELECT * FROM admin_record')
    users_record_admin_activity = mycur.fetchall()
    conn.commit()
    mycur.execute('SELECT * FROM admin_record ORDER BY id DESC LIMIT 1')
    current_admin_affairs = mycur.fetchall()
    conn.commit()
    try:
        admin_current_pool = current_admin_affairs[0][1]
    except:
        admin_current_pool = 0
    total_wins = sum(record[2] for record in users_record_admin_activity)
    total_loss = sum(record[3] for record in users_record_admin_activity)
    total_given = sum(record[4] for record in users_record_admin_activity)
    total_received = sum(record[5] for record in users_record_admin_activity)
    return render_template("admin_ledger.html", total_received=total_received, total_given=total_given,
                           total_loss=total_loss, users_record_admin_activity=users_record_admin_activity,
                           admin_pool=admin_current_pool, total_wins=total_wins)


@app.route('/add_admin_funds_page')
def add_admin_funds_page():
    return render_template("add_funds_admin.html")


@app.route('/add_admin_funds', methods=['GET', 'POST'])
def add_admin_funds():
    global admin_pool, num_records_admin
    if request.method == 'POST':
        admin_pool, num_records_admin = admin_record_pool()
        authentication_password = request.form['authentication_password']
        amount = request.form['amount']
        reason = request.form['user_input']
        if authentication_password == f"{admin_password}":
            print(admin_pool)
            new_balance = admin_pool + int(amount)
            # print(new_balance)
            admin_ledger_add = 'Cash A/C To Admin A/C'
            mycur.execute(f'INSERT INTO admin_record (id, balance, admin_ledger, money_added, reason, amount, date) '
                          f'VALUES ("{num_records_admin}", "{new_balance}", "{admin_ledger_add}", '
                          f'"{amount}", "{reason}", "{amount}", "{formatted_datetime}")')
            conn.commit()
        else:
            return "password incorrect"
        return redirect(url_for("admin_ledger"))


@app.route('/withdraw_admin_funds_page')
def withdraw_admin_funds_page():
    return render_template("withdraw_funds_admin.html")


@app.route('/withdraw_admin_funds', methods=['GET', 'POST'])
def withdraw_admin_funds():
    global admin_pool, num_records_admin
    if request.method == 'POST':
        admin_pool, num_records_admin = admin_record_pool()
        authentication_password = request.form['authentication_password']
        amount = request.form['amount']
        reason = request.form['user_input']
        if authentication_password == f"{admin_password}":
            new_balance_withdraw = admin_pool - int(amount)
            if new_balance_withdraw >= 0:
                admin_ledger_deduct = 'Admin A/C To Cash A/C '
                mycur.execute(f'INSERT INTO admin_record (id, balance,admin_ledger, money_withdrawn, reason, '
                              f'amount, date) VALUES ("{num_records_admin}", "{new_balance_withdraw}",'
                              f' "{admin_ledger_deduct}", "{amount}", "{reason}", "{amount}","{formatted_datetime}")')
                conn.commit()
            else:
                return "insufficient funds"
        return redirect(url_for("admin_ledger"))


@app.route('/authentication_admin', methods=['GET', 'POST'])
def authentication_admin():
    global user_ledger_addentry, user_ledger_deductentry, new_balance_admin, admin_ledger_given, \
        admin_ledger_received, admin_pool, num_records_admin, new_balance, new_added_fund, \
        new_bonus_points, authentication_password_used
    if request.method == 'POST':
        admin_pool, num_records_admin = admin_record_pool()
        authentication_password = request.form['authentication_password']
        payment_type = request.form['payment_type']
        action = request.form['action']
        amount = request.form['amount']
        user_name = request.form['user_name']
        reason = request.form['user_input']
        if not authentication_password_used:
            if authentication_password == f"{admin_password}":
                authentication_password_used = True
                mycur.execute('select * from records_user')
                users_record = mycur.fetchall()
                conn.commit()
                record_ids = []
                for users_record in users_record:
                    record_id = users_record[0]
                    record_ids.append(record_id)
                num_records = (len(record_ids) + 1)
                user = None
                mycur.execute("SELECT * FROM ginie_bet.user_data")
                users_data = mycur.fetchall()
                conn.commit()
                for u in users_data:
                    if u[2] == user_name:
                        user = u
                        break
                if action == "add":
                    new_balance = int(user[6]) + int(amount)
                    print(admin_pool, amount)
                    if payment_type == "cash":
                        if int(admin_pool) >= int(amount):
                            new_added_fund = int(user[7]) + int(amount)
                            new_bonus_points = int(user[14])
                            new_balance_admin = admin_pool - int(amount)
                            # new_withdrawn_funds = int(user[8])
                        else:
                            return "insufficient funds"
                    else:
                        new_added_fund = int(user[7])
                        new_bonus_points = int(user[14]) + int(amount)
                        new_balance_admin = admin_pool
                        # new_withdrawn_funds = int(user[8])
                else:
                    try:
                        mycur.execute(f"select balance, fund_added, fund_withdrawn from user_data where user_name = '{user[2]}'")
                        conn.commit()
                        balance_data = mycur.fetchall()
                        if balance_data:
                            balance_current = balance_data[0][0]  # Extract the balance value from the fetched data
                            fund_added_current = balance_data[0][1]
                            fund_withdrawn_current = balance_data[0][2]
                            print(fund_added_current - fund_withdrawn_current)
                            if fund_added_current - fund_withdrawn_current >= int(amount):
                                new_balance = int(user[6]) - int(amount)
                                if payment_type == "cash":
                                    new_added_fund = int(user[7])
                                    new_bonus_points = int(user[14])
                                    new_balance_admin = admin_pool + int(amount)
                                    # new_withdrawn_funds = int(user[8]) + int(amount)
                                else:
                                    return "sorry bonus cant be deducted"
                                    # new_added_fund = int(user[7])
                                    # new_bonus_points = int(user[14])
                                    # new_balance_admin = admin_pool
                                    # new_withdrawn_funds = int(user[8]) + int(amount)
                            else:
                                return "insufficient balance."
                    except Exception:
                        return "insufficient balance."
                if action == 'add':
                    format_old_record_add = (f"The old details for {user[1]}, Balance: {user[6]}, Fund added: {user[7]},"
                                         f" Bonus points: {user[14]}")
                    format_new_record_add = (f"The new details for {user[1]}, Balance: {new_balance}, Fund added"
                                         f": {new_added_fund}, Bonus points: {new_bonus_points}")
                else:
                    format_old_record_deduct = (f"The old details for {user[1]}, Balance: {user[6]}, Fund withdrawn:"
                                                f" {user[8]}")
                    format_new_record_deduct = (f"The new details for {user[1]}, Balance: {new_balance}, Fund withdrawn"
                                                f": {amount}")
                if action == 'add':
                    user_ledger_addentry = f'{payment_type} A/C\nTo {game_name} A/C'
                    admin_ledger_given = f'{user_name} A/C\nTo {payment_type} A/C'
                else:
                    user_ledger_deductentry = f'{game_name} A/C\nTo {payment_type} A/C'
                    admin_ledger_received = f'{payment_type} A/C\nTo {user_name} A/C'
                if action == 'add':
                    try:
                        mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                      f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                      f") VALUES ('{num_records}', '{reason}', '{format_old_record_add}', "
                                      f"'{format_new_record_add}', '{user_name}', '{amount}', '{payment_type}',"
                                      f"'{formatted_datetime}','{new_balance}', '{action}', '{user_ledger_addentry}')")
                        # mycur.execute('DELETE from records_user')
                        conn.commit()
                    except:
                        mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                      f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                      f") VALUES ('{num_records + 1}', '{reason}', '{format_old_record_add}', "
                                      f"'{format_new_record_add}', '{user_name}', '{amount}', '{payment_type}',"
                                      f"'{formatted_datetime}','{new_balance}', '{action}', '{user_ledger_addentry}')")
                        # mycur.execute('DELETE from records_user')
                        conn.commit()
                    try:
                        mycur.execute(
                            f'INSERT INTO admin_record (id, balance, money_given, admin_ledger, reason, amount, date) '
                            f'VALUES ("{num_records_admin}", "{new_balance_admin}", "{amount}",'
                            f' "{admin_ledger_given}", "{reason}", "{amount}", "{formatted_datetime}")')
                        conn.commit()
                    except UnboundLocalError:
                        mycur.execute(
                            f'INSERT INTO admin_record (id, balance, money_given, admin_ledger, reason, amount, date) '
                            f'VALUES ("{num_records_admin}", "{admin_pool}", "{amount}",'
                            f' "{admin_ledger_given}", "{reason}", "{amount}", "{formatted_datetime}")')
                        conn.commit()
                else:
                    try:
                        mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                      f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                      f") VALUES ('{num_records}', '{reason}', '{format_old_record_deduct}', "
                                      f"'{format_new_record_deduct}', '{user_name}', '{amount}', '{payment_type}',"
                                      f"'{formatted_datetime}','{new_balance}', '{action}', '{user_ledger_deductentry}')")
                        # mycur.execute('DELETE from records_user')
                        conn.commit()
                    except:
                        mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                      f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                      f") VALUES ('{num_records + 1}', '{reason}', '{format_old_record_deduct}', "
                                      f"'{format_new_record_deduct}', '{user_name}', '{amount}', '{payment_type}',"
                                      f"'{formatted_datetime}','{new_balance}', '{action}', '{user_ledger_deductentry}')")
                        # mycur.execute('DELETE from records_user')
                        conn.commit()
                    new_balance_admin = admin_pool + int(amount)
                    try:
                        mycur.execute(
                            f'INSERT INTO admin_record (id, balance, money_received, admin_ledger, reason, amount, date) '
                            f'VALUES ("{num_records_admin}", "{new_balance_admin}", "{amount}",'
                            f' "{admin_ledger_received}", "{reason}", "{amount}", "{formatted_datetime}")')
                        conn.commit()
                    except UnboundLocalError:
                        mycur.execute(
                            f'INSERT INTO admin_record (id, balance, money_received, admin_ledger, reason, amount, date) '
                            f'VALUES ("{num_records_admin}", "{admin_pool}", "{amount}",'
                            f' "{admin_ledger_received}", "{reason}", "{amount}", "{formatted_datetime}")')
                        conn.commit()
                if action == 'add':
                    mycur.execute(
                        f"UPDATE user_data SET "
                        f"balance = '{new_balance}', fund_added = '{new_added_fund}', bonus_points = '{new_bonus_points}' "
                        f"WHERE user_name = '{user_name}'"
                    )
                    conn.commit()
                else:
                    mycur.execute(
                        f"UPDATE user_data SET "
                        f"balance = '{new_balance}', fund_withdrawn = '{amount}' WHERE user_name = '{user_name}'"
                    )
                    conn.commit()
                if action == 'add':
                    admin_ledger_current = admin_ledger_given
                else:
                    admin_ledger_current = admin_ledger_received
                mycur.execute('SELECT * FROM records_user WHERE user_name = %s', (user_name,))
                users_record = mycur.fetchall()
                conn.commit()
                mycur.execute("SELECT * FROM ginie_bet.user_data WHERE user_name = %s", (user_name,))
                users_details = mycur.fetchall()
                conn.commit()
                users_detail = users_details[0]
                return render_template("change_details.html", user=users_detail, payment_type=payment_type, reason=reason,
                                       num_records=num_records, amount=amount, new_balance=new_balance,
                                       users_record=users_record, admin_ledger=admin_ledger_current)
            else:
                return "Password incorrect"
        else:
            return "Password already used"
    return redirect(url_for("success_user_funds"))


@app.route('/success_user_funds', methods=['GET', 'POST'])
def success_user_funds():
    return render_template("authentication_admin.html")


@app.route('/funds', methods=['GET', 'POST'])
def funds_user():
    return render_template("funds.html")


@app.route('/view_balance', methods=['GET', 'POST'])
def view_funds():
    global user_balance
    user = session.get('user')
    mycur.execute(f"select balance from user_data where user_name = '{user}'")
    conn.commit()
    balance_data = mycur.fetchall()
    if balance_data:
        user_balance = balance_data[0][0]  # Extract the balance value from the fetched data
    return render_template("view_funds.html", user_balance=user_balance)


@app.route('/fund_manager', methods=['GET', 'POST'])
def fund_manager():
    global status
    if request.method == 'POST':
        user = session.get('user')
        mycur.execute(f'select status from user_data where user_name = "{user}"')
        status_result = mycur.fetchone()  # Use fetchone() instead of fetchall()
        conn.commit()

        if status_result:
            status = status_result[0]  # Extract the string from the tuple

        add = request.form.get('add')
        if status != "BLOCK":
            if add == 'Add':
                fund_added_str = request.form.get('addFunds')
                fund_added = int(fund_added_str)
                mycur.execute(f"select balance from user_data where user_name = '{user}'")
                conn.commit()
                balance_data = mycur.fetchall()
                if balance_data:
                    balance = balance_data[0][0]  # Extract the balance value from the fetched data
                    print(balance)
                    new_balance = fund_added + balance
                    print(new_balance)
                    mycur.execute(f"UPDATE user_data SET balance = {new_balance} WHERE user_name = '{user}'")
                    conn.commit()
                    mycur.execute('SELECT id FROM records_user ORDER BY id DESC LIMIT 1')
                    user_record = mycur.fetchone()  # Use fetchone to get a single result
                    conn.commit()

                    if user_record:
                        num_records = int(user_record[0]) + 1  # Extract the integer from the tuple and add 1
                    else:
                        num_records = 1  # Set a default value if no records are found
                    user_ledger_addentry_funds = f"{game_name} A/C To cash A/C"
                    mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                  f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                  f") VALUES ('{num_records}', 'Funds were added by {user} of amount {fund_added}', "
                                  f"'Old balance: {balance}', 'New balance: {new_balance}', '{user}', '{fund_added}'"
                                  f", 'cash','{formatted_datetime}','{new_balance}', 'add',"
                                  f" '{user_ledger_addentry_funds}')")
                    # mycur.execute('DELETE from records_user where id = "10"')
                    conn.commit()
                return "success"
            else:
                print("check 0")
                fund_subtracted_str = request.form.get('withdrawFunds')
                fund_subtracted = int(fund_subtracted_str)
                mycur.execute(f"select balance from user_data where user_name = '{user}'")
                conn.commit()
                balance_data = mycur.fetchall()
                mycur.execute(f"select bonus_points from user_data where user_name = '{user}'")
                conn.commit()
                bonus_points_data = mycur.fetchall()
                if balance_data:
                    balance_current = balance_data[0][0]  # Extract the balance value from the fetched data
                    bonus = bonus_points_data[0][0]
                    if bonus <= balance_current:
                        print("check 1")
                        if balance_current >= fund_subtracted:
                            mycur.execute(f"select balance from user_data where user_name = '{user}'")
                            conn.commit()
                            balance_data = mycur.fetchall()
                            print("check 2")
                            if balance_data:
                                balance = balance_data[0][0]  # Extract the balance value from the fetched data
                                print("check 3")
                                if balance >= fund_subtracted:
                                    print(fund_subtracted)
                                    new_balance = balance - fund_subtracted
                                    print(new_balance)
                                    mycur.execute(
                                        f"UPDATE user_data SET balance = {new_balance}, fund_withdrawn = "
                                        f"'{fund_subtracted}' WHERE user_name = '{user}'")
                                    conn.commit()
                                    mycur.execute("SELECT id FROM records_user ORDER BY id DESC LIMIT 1")
                                    last_match_id = mycur.fetchone()

                                    if last_match_id:
                                        last_match_id = int(last_match_id[0])
                                    try:
                                        num_records = last_match_id + 1
                                    except:
                                        num_records = 1
                                    print(num_records)
                                    user_ledger_addentry = f"cash A/C To {game_name} A/C"
                                    mycur.execute(
                                        f"INSERT INTO records_user (id, reason_change, old_record_user, "
                                        f"new_record_user, user_name, amount, payment_type, date, balance, action, "
                                        f"user_ledger) VALUES ('{num_records}', 'Funds were withdrew by {user} of amount"
                                        f" {fund_subtracted}', 'Old balance: {balance}', 'New balance: {new_balance}', "
                                        f"'{user}', '{fund_subtracted}', 'cash','{formatted_datetime}','{new_balance}',"
                                        f" 'deduct', '{user_ledger_addentry}')")
                                    # mycur.execute('DELETE from records_user')
                                    conn.commit()
                            return "success"
                        else:
                            return "you do not have sufficient balance to withdraw. please check your balance."
                    else:
                        return "sorry but your amount includes bonus, please check again and try."
        else:
            return "fail"


@app.route('/stats_funds', methods=['GET', 'POST'])
def stats_funds_page():
    mycur.execute('SELECT * FROM records_user')
    users_record = mycur.fetchall()
    conn.commit()
    return render_template("stats_funds.html", users_record=users_record)


@app.route('/general_ledger', methods=['GET', 'POST'])
def general_ledger():
    mycur.execute('SELECT * FROM records_user')
    users_record = mycur.fetchall()
    conn.commit()
    return render_template("general_ledger.html", users_record=users_record)


#
#
#
# end funds
#
#
#

#
#
#
# matches
#
#
#

@app.route('/all_sports', methods=['GET', 'POST'])
def all_sports():
    mycur.execute("select * from sports_creation where soft_delete != 'yes'")
    sports_sports = mycur.fetchall()
    conn.commit()
    # image_urls_list = []
    #
    # for sport_sport in sports_sports:
    #     image_url = sport_sport[4].decode('utf-8')
    #     image_urls_list.append(image_url)

    # Fetch the sports from the database
    return render_template('all_sports.html', sports=sports_sports)


@app.route('/view_matches/<sport_name_click>', methods=['GET', 'POST'])
def total_matches_admin(sport_name_click):
    # Fetch the sports from the database
    selected_sport = sport_name_click
    session['selected_sport'] = selected_sport
    mycur.execute(f"select * from matches_creation where sport_name = '{selected_sport}' and soft_delete != 'yes'")
    matches_sport = mycur.fetchall()
    conn.commit()

    # Fetch the sports from the database
    return render_template("view_matches.html", selected_sport=selected_sport, matches_sport=matches_sport)


@app.route('/match_creation_form', methods=['GET', 'POST'])
def match_creation():
    selected_sport = session.get('selected_sport')
    if request.method == 'POST':

        mycur.execute("SELECT match_id FROM matches_creation ORDER BY match_id DESC LIMIT 1")
        last_match_id = mycur.fetchone()

        if last_match_id:
            last_match_id = int(last_match_id[0])
        try:
            match_id = last_match_id + 1
        except:
            match_id = 1
        team_a = request.form.get('team_a')
        team_b = request.form.get('team_b')
        match_name_current = f"{team_a} vs {team_b}"
        league = request.form.get('league')
        date_match = request.form.get('date')
        time_match = request.form.get('time')
        ginie_bet_name_current = request.form.get('ginie_bet')
        primary_description = request.form.get('primary_description')
        secondary_description = request.form.get('secondary_description')
        mycur.execute("insert into matches_creation (match_id, sport_name, match_name, team_a, team_b, date, time,"
                      f" ginie_bet, league, primary_description, secondary_description) VALUES ('{match_id}', "
                      f"'{selected_sport}', '{match_name_current}',"
                      f" '{team_a}', '{team_b}', '{date_match}', '{time_match}', "
                      f"'{ginie_bet_name_current}', '{league}', '{primary_description}', '{secondary_description}')")
        # mycur.execute('delete from sports_creation where sports_id = "3"')
        conn.commit()
        if ginie_bet_name_current == "with":
            mycur.execute("INSERT INTO ginie_bet.ginie_bet_selection (sports_name, match_name)"
                          f"VALUES ('{selected_sport}', '{match_name_current}')")
            conn.commit()
        return redirect(url_for("total_matches_admin", sport_name_click=selected_sport))

    return redirect(url_for("total_matches_admin", sport_name_click=selected_sport))


@app.route('/total_matches', methods=['GET', 'POST'])
def total_matches():
    # Fetch the sports from the database
    global num_matches
    if request.method == 'POST':
        # Handle the form submission
        selected_sport = request.form['selection']
        if selected_sport in [str(sport_match[0]) for sport_match in sport_options]:
            sport_name = get_sport_name(selected_sport)
            session['sports_name'] = sport_name
            if sport_name:
                mycur.execute(
                    f"select * from matches_creation where sport_name = '{sport_name}' and soft_delete != 'yes'")
                matches = mycur.fetchall()
                conn.commit()
                num_matches = len(matches)
                session['num_matches'] = num_matches
                session['matches'] = matches
                sport_name = sport_name
                session['sportname'] = sport_name
            else:
                matches = []
                sport_name = 'Unknown'

            return render_template('sport_selection.html', sport_name=sport_name, matches=matches,
                                   num_matches=num_matches)

    # Render the template with the dynamic options
    return render_template('all_matches.html', sport_options=sport_options)


@app.route('/match_details/<match_id>', methods=['GET', 'POST'])
def match_details(match_id):
    global target_date, target_time, match_name
    mycur.execute(f'select * from matches_creation where match_id = {match_id}')
    match_selected = mycur.fetchall()
    conn.commit()
    session['match_id'] = match_id

    for match_current in match_selected:
        session['match_name'] = match_current[2]
        input_date = match_current[5]
        input_time = match_current[6]  # Assuming match[6] contains the time like "13:00"

        # Use regular expression to extract the time in "HH:mm" format
        match_time = re.match(r'(\d{2}):(\d{2})', input_time)

        if match_time:
            hours = int(match_time.group(1))
            minutes = int(match_time.group(2))

            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                target_time = f"{hours:02}:{minutes:02}"  # Format the time as "HH:mm"
        target_date = datetime.strptime(input_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        match_name = session.get('match_name')

    mycur.execute(f'select * from questions_ginie_bet where match_name = "{match_name}" AND soft_delete != "yes"')
    ginie_bet_questions = mycur.fetchall()
    conn.commit()
    return render_template("match_details.html", match_selected=match_selected, ginie_bet_questions=ginie_bet_questions,
                           target_date=target_date, target_time=target_time)


@app.route('/match_correct_answer', methods=['POST', 'GET'])
def correct_match_details():
    match_id = session.get('match_id')
    return redirect(url_for("match_details", match_id=match_id))


@app.route('/multiplier', methods=['POST', 'GET'])
def multiplier():
    return render_template("multiplier.html")


@app.route('/all_multiplier', methods=['POST', 'GET'])
def all_multiplier():
    mycur.execute("select * from multiplier_record where soft_delete != 'yes'")
    multiplier_record = mycur.fetchall()
    conn.commit()
    return render_template('all_multipliers.html', sports=multiplier_record)


@app.route('/new_multiplier', methods=['POST', 'GET'])
def add_new_multiplier():
    mycur.execute('SELECT multiplier_id FROM multiplier_record ORDER BY multiplier_id DESC LIMIT 1')
    num_multiplier = mycur.fetchall()
    conn.commit()
    try:
        num_multipliers = int(num_multiplier[0][0]) + 1
    except:
        num_multipliers = 1
    multiplier_name = request.form.get('multiplier_name')
    multiplier_one = request.form.get('multiplier_one')
    multiplier_two = request.form.get('multiplier_two')
    multiplier_three = request.form.get('multiplier_three')
    multiplier_four = request.form.get('multiplier_four')
    multiplier_five = request.form.get('multiplier_five')
    multiplier_six = request.form.get('multiplier_six')
    multiplier_seven = request.form.get('multiplier_seven')
    multiplier_eight = request.form.get('multiplier_eight')
    multiplier_nine = request.form.get('multiplier_nine')
    multiplier_ten = request.form.get('multiplier_ten')
    if multiplier_ten == '':
        multiplier_ten = None
    multiplier_eleven = request.form.get('multiplier_eleven')
    if multiplier_eleven == '':
        multiplier_eleven = None
    multiplier_twelve = request.form.get('multiplier_twelve')
    if multiplier_twelve == '':
        multiplier_twelve = None
    multiplier_thirteen = request.form.get('multiplier_thirteen')
    if multiplier_thirteen == '':
        multiplier_thirteen = None
    multiplier_fourteen = request.form.get('multiplier_fourteen')
    if multiplier_fourteen == '':
        multiplier_fourteen = None
    multiplier_fifteen = request.form.get('multiplier_fifteen')
    if multiplier_fifteen == '':
        multiplier_fifteen = None
    bumper_question = request.form.get('bumper_question')
    mycur.execute(f'insert into multiplier_record (multiplier_id, multiplier_name, multiplier_one, multiplier_two,'
                  f' multiplier_three, multiplier_four, multiplier_five, multiplier_six, multiplier_seven,'
                  f' multiplier_eight, multiplier_nine, multiplier_ten, multiplier_eleven, multiplier_twelve,'
                  f' multiplier_thirteen, multiplier_fourteen, multiplier_fifteen, bumper_question)'
                  f' values ("{num_multipliers}", "{multiplier_name}",'
                  f' "{multiplier_one}", "{multiplier_two}", "{multiplier_three}", "{multiplier_four}",'
                  f'"{multiplier_five}", "{multiplier_six}", "{multiplier_seven}", "{multiplier_eight}",'
                  f' "{multiplier_nine}", "{multiplier_ten}", "{multiplier_eleven}", "{multiplier_twelve}",'
                  f' "{multiplier_thirteen}", "{multiplier_fourteen}", "{multiplier_fifteen}", "{bumper_question}")')
    conn.commit()
    return redirect(url_for("all_multiplier"))


@app.route('/sport_creation_selection_admin', methods=['GET', 'POST'])
def sport_creation_selection():
    mycur.execute("SELECT * FROM ginie_bet.sports_creation where soft_delete != 'yes'")
    # sports = mycur.fetchall()
    # for sport in sports:
    #     sport_options.append(sport)
    return render_template('sport_creation_selection_admin.html')


@app.route('/sports_creation_form', methods=['GET', 'POST'])
def sport_creation():
    if request.method == 'POST':
        mycur.execute("select sports_id from sports_creation")
        total_sports = mycur.fetchall()
        conn.commit()
        num_sports = []
        for sport_current in total_sports:
            num_sports.append(sport_current)
        num_sport = len(num_sports) + 1
        sports_name = request.form.get('sports_name')
        category = request.form.get('category')
        league = request.form.get('league')
        image_sport = request.form.get('image_sport')
        primary_description = request.form.get('primary_description')
        secondary_description = request.form.get('secondary_description')
        try:
            mycur.execute("insert into sports_creation (sports_id, sports_name, category, league, sports_icon, "
                          f" primary_description, secondary_description) VALUES ('{num_sport}', '{sports_name}',"
                          f" '{category}', '{league}', '{image_sport}', '{primary_description}', "
                          f"'{secondary_description}')")
            conn.commit()
        except:
            mycur.execute("SELECT * from sports_creation where soft_delete = 'yes'")
            deleted_sports = mycur.fetchall()
            conn.commit()
            return render_template("soft_delete_list_sports.html", deleted_sports=deleted_sports)

        # You can now process and save these values as needed

        return redirect(url_for("all_sports"))

    return redirect(url_for("all_sports"))


@app.route('/ginie_bet_matches', methods=['POST', 'GET'])
def get_ginie_matches():
    user = session.get('user')
    selected_sport = session.get('sportname')
    mycur.execute(f"SELECT * FROM ginie_bet.matches_creation where sport_name = '{selected_sport}' and"
                  f" roll_out_questions = 'yes' and soft_delete != 'yes'")
    ginie_bet_questions_matches = mycur.fetchall()
    conn.commit()

    ginie_matches = set()  # Create a set to store unique names

    for ginie_bet_questions_match in ginie_bet_questions_matches:
        name_current = ginie_bet_questions_match[2]
        if name_current not in ginie_matches:
            ginie_matches.add(name_current)

    ginie_bet_matches_confirmed = set()

    for ginie_match in ginie_matches:
        mycur.execute(f"SELECT * FROM ginie_bet.check_answer_ginie_bet where match_name = '{ginie_match}' and "
                      f"user_name = '{user}'")
        ginie_bet_user_already_played_check_list = mycur.fetchall()
        conn.commit()
        if ginie_bet_user_already_played_check_list:
            pass
        else:
            ginie_bet_matches_confirmed.add(ginie_match)
    return render_template('ginie_bet_matches.html', matches=ginie_bet_matches_confirmed, selected_sport=selected_sport)


@app.route('/upload', methods=['POST'])
def upload_image():
    mycur.execute("select sports_id from sports_creation where soft_delete != 'yes'")
    total_sports = mycur.fetchall()
    conn.commit()
    num_sports = []
    for sport_current in total_sports:
        num_sports.append(sport_current)
    num_sport = len(num_sports) + 1
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file and allowed_file(image_file.filename):
            # Rename the uploaded image to "image_1.jpg" (or any desired format)
            filename = f"image_{num_sport}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

            # Return the image URL (you may need to adjust this URL based on your server setup)
            image_url = f"/{filepath}"
            return jsonify({"url": image_url}), 200

    return jsonify({"message": "Invalid file or file not provided."}), 400


#
#
#
# end matches
#
#
#

#
#
#
# ginie bet
#
#
#

@app.route('/entry_fee', methods=['GET', 'POST'])
def entry_fee():
    match_name_current = session.get('match_name')
    mycur.execute('select * from multiplier_record')
    multiplier_record = mycur.fetchall()
    conn.commit()
    return render_template("entry_fee.html", match_name=match_name_current, multiplier_record=multiplier_record)
    # return "successful"


@app.route('/entry_fee_details', methods=['GET', 'POST'])
def entry_fee_details():
    match_name_current = session.get('match_name')
    match_id = session.get('match_id')
    mycur.execute('select * from ginie_bet_selection')
    ginie_bet_match_data = mycur.fetchall()
    conn.commit()
    for match_current in ginie_bet_match_data:
        if match_current[1] == match_name_current:
            entry_fee_amount = request.form.get('amount')
            entry_fee_multiplier = request.form.get('multiplier_input')
            mycur.execute(f'UPDATE ginie_bet_selection set entryfee = {entry_fee_amount},'
                          f' multiplier = {entry_fee_multiplier} where match_name = "{match_name_current}"')
            # mycur.execute('delete from ginie_bet_selection')
            conn.commit()

    return redirect(url_for('match_details', match_id=match_id))


@app.route('/ginie_bet_quiz', methods=['GET', 'POST'])
def ginie_bet_quiz():
    match_name_current = session.get('match_name')
    return render_template("ginie_bet_quiz.html", match_name=match_name_current)


@app.route('/ginie_bet_quiz_details', methods=['GET', 'POST'])
def ginie_bet_quiz_details():
    mycur.execute('SELECT question_id FROM questions_ginie_bet ORDER BY question_id DESC LIMIT 1')
    num_questions = mycur.fetchall()
    conn.commit()
    try:
        question_number = int(num_questions[0][0]) + 1
    except:
        question_number = 1
    sport_name = session.get('selected_sport')
    match_name_current = session.get('match_name')
    question = request.form.get('question')
    option_1 = request.form.get('option_1')
    option_2 = request.form.get('option_2')
    option_3 = request.form.get('option_3')
    if option_3 == "":
        option_3 = None
    option_4 = request.form.get('option_4')
    if option_4 == "":
        option_4 = None
    match_id = session.get('match_id')
    mycur.execute(
        f'INSERT INTO questions_ginie_bet (question_id, name_sport, match_name, question, option_1, option_2, option_3,'
        f' option_4, correct_answer_filled) VALUES ("{question_number}", "{sport_name}", "{match_name_current}", '
        f'"{question}", "{option_1}", "{option_2}", "{option_3}", "{option_4}", "no")')
    return redirect(url_for('match_details', match_id=match_id))


@app.route('/correct_answer/<match_name_current>', methods=['GET', 'POST'])
def correct_answer(match_name_current):
    session['match_name_current'] = match_name_current
    mycur.execute(f"SELECT * FROM ginie_bet.questions_ginie_bet where match_name = '{match_name_current}'"
                  f"and soft_delete != 'yes' and correct_answer_filled != 'yes'")
    correct_question_details = mycur.fetchall()
    conn.commit()
    combined_data = []

    for correct_question_detail in correct_question_details:
        new_list = [
            correct_question_detail[4],
            correct_question_detail[5],
            correct_question_detail[6],
            correct_question_detail[7],
            "NULL AND VOID"
        ]
        combined_data.append((correct_question_detail, new_list))
        print(combined_data)

    return render_template("correct_answer.html", combined_data=combined_data)


@app.route('/correct_answer_form/<question_id>', methods=['GET', 'POST'])
def correct_answer_form(question_id):
    correct_answer_current = request.form.get('answer')
    mycur.execute(
        f'Update questions_ginie_bet set correct_answer="{correct_answer_current}", correct_answer_filled = "yes" where'
        f' question_id = "{question_id}"')
    match_name_current = session.get('match_name_current')
    return redirect(url_for('correct_answer', match_name_current=match_name_current))


@app.route('/correct_answer_update/<correct_id>', methods=['GET', 'POST'])
def correct_answer_update(correct_id):
    session['correct_id'] = correct_id
    mycur.execute(f"select * from questions_ginie_bet where question_id = '{correct_id}'")
    question_correct_update = mycur.fetchall()
    conn.commit()
    option_list = []
    for question_correct_options in question_correct_update:
        option_list.append(question_correct_options[4])
        option_list.append(question_correct_options[5])
        option_list.append(question_correct_options[6])
        option_list.append(question_correct_options[7])

    return render_template("correct_answer_update.html", question_correct_update=question_correct_update,
                           option_list=option_list)


@app.route('/correct_answer_form_update', methods=['GET', 'POST'])
def correct_answer_form_update():
    correct_id = session.get('correct_id')
    match_id = session.get('match_id')
    correct_answer_update_current = request.form.get('correct_answer')
    mycur.execute(
        f'Update questions_ginie_bet set correct_answer="{correct_answer_update_current}" '
        f'where question_id = "{correct_id}"')
    return redirect(url_for('match_details', match_id=match_id))


@app.route(f'/ginie_bet/<match_dif>', methods=['POST', 'GET'])
def ginie_bet(match_dif):
    # Get the match details based on the match_id
    match_current = get_match_by_dif(match_dif)
    entry_fee_ginie_bet = (match_current[3])
    session['entry_fees'] = entry_fee_ginie_bet
    if admin:
        return render_template('ginie_bet_qnum.html', match=match_current)
    else:
        return render_template('ginie_bet.html', match=match_current)


@app.route(f'/submit_questions/<match_dif>', methods=['POST', 'GET'])
def submit_questions(match_dif):
    num_questions = session.get('question_number')
    match_submit_question = get_match_by_dif(match_dif)
    questions_sql = request.form.getlist('questions[]')
    options1_sql = request.form.getlist('options1[]')
    options2_sql = request.form.getlist('options2[]')
    options3_sql = request.form.getlist('options3[]')
    questions_data = []

    # Loop through the questions and combine options into a list for each question
    for i in range(num_questions):
        question = questions_sql[i]
        option1 = options1_sql[i]
        option2 = options2_sql[i]
        option3 = options3_sql[i]

        # Create the question-answer pair in the desired format
        question_data = {
            "question": question,
            "options": [option1, option2, option3],
        }

        # Append the question-answer pair to the list
        questions_data.append(question_data)

    # Now, questions_data contains the questions and answers in the desired format
    for q in questions_data:
        game_question = q['question']
        game_options = ", ".join(q["options"])  # Join options into a comma-separated string
        match_name_sport = match_submit_question[1]

        # Use parameterized query to safely insert data
        query = "INSERT INTO questions_ginie_bet (name_sport, question, options) VALUES (%s, %s, %s)"
        values = (match_name_sport, game_question, game_options)

        mycur.execute(query, values)
        conn.commit()

    return render_template("question_sql.html", match=match_submit_question)


@app.route(f'/greetings/<match_dif>', methods=['POST', 'GET'])
def greetings(match_dif):
    match_greetings = get_match_by_dif(match_dif)
    session['current_match'] = match_greetings
    rules = greet_user()  # Call greet_user() and get the rules list
    return render_template('greetings.html', rules=rules, match=match_greetings)


@app.route(f'/ginie_bet_question_list/<match_dif>', methods=['POST', 'GET'])
def ginie_bet_question_list(match_dif):
    mycur.execute(f"SELECT * FROM ginie_bet.questions_ginie_bet where match_name = '{match_dif}'")
    questions = mycur.fetchall()
    conn.commit()
    match_ginie_bet_questions = session.get('current_match')
    return render_template("ginie_bet_question_list.html", questions=questions, match=match_ginie_bet_questions)


@app.route('/game_on/<match_dif>', methods=['POST'])
def the_game(match_dif):
    global balance, entry_fees, match
    match_data = get_match_by_dif(match_dif)
    session['match_data'] = match_data
    if request.method == 'POST':
        response = request.form.get('response').upper()
        if response == 'Y':
            mycur.execute(f'select * from ginie_bet_selection where match_name = "{match_data[1]}"')
            match_info = mycur.fetchall()
            conn.commit()
            for match in match_info:
                entry_fees = match[2]
                session['entryfees'] = entry_fees
            user = session.get('user')
            mycur.execute(f"select balance from user_data where user_name = '{user}'")
            conn.commit()
            balance_data = mycur.fetchall()
            if balance_data:
                balance = balance_data[0][0]
            try:
                if balance >= entry_fees:
                    mycur.execute(f"select balance from user_data where user_name = '{user}'")
                    conn.commit()
                    balance_data = mycur.fetchall()
                    if balance_data:
                        balance = balance_data[0][0]  # Extract the balance value from the fetched data
                        new_balance_current = balance - entry_fees
                        print(new_balance_current)
                        mycur.execute(
                            f"UPDATE user_data SET balance = {new_balance_current} WHERE user_name = '{user}'")
                        conn.commit()
                else:
                    return "do not have sufficient fund"
            except:
                return "sorry the match is still under development"
            questions_dict = {}  # Initialize an empty dictionary
            mycur.execute(f'select * from questions_ginie_bet where match_name = "{match[1]}" AND soft_delete != "yes"')
            questions_info = mycur.fetchall()
            conn.commit()
            # Assuming that 'question_id' is the key and 'question_text' is the value in your database
            for question in questions_info:
                question_id = question[3]  # Assuming question_id is at index 3
                question_text_4 = question[4]  # Assuming question_text at index 4
                question_text_5 = question[5]  # Assuming question_text at index 5
                question_text_6 = question[6]  # Assuming question_text at index 6
                question_text_7 = question[7]  # Assuming question_text at index 6
                questions_dict[question_id] = (question_text_4, question_text_5, question_text_6, question_text_7)
            available_questions = list(questions_dict.keys())
            # Filter out the questions that have already been asked
            remaining_questions = [q for q in available_questions if q not in asked_questions]

            if not remaining_questions:
                adding_answer_sql()
                return "You have answered all the questions. Game Over!"
            # Randomly select a question from the remaining ones
            selected_question = (remaining_questions[0])
            options = questions_dict[selected_question]
            asked_questions.append(selected_question)  # Add the question to the asked_questions list

            return render_template("game.html", options=options, question=selected_question, match=match)

        elif response == 'N':
            adding_answer_sql()
            return "exited"

        else:
            return "Invalid selection. Please enter 'Y' or 'N'."

    return render_template("game.html")


@app.route('/quiz_conti/<match_dif>', methods=['POST'])
def conti_game(match_dif):
    match_conti_game = get_match_by_dif(match_dif)
    answer = request.form.get('answer')
    answers.append(answer)
    return render_template('quiz_conti.html', match=match_conti_game)


def adding_answer_sql():
    user_ip = request.remote_addr  # Get the user's IP address
    user_location = get_location(
        user_ip)
    user = session.get('user')
    match_name_adding_answer = session.get('current_match')
    mycur.execute("SELECT id_check_answer FROM check_answer_ginie_bet ORDER BY id_check_answer DESC LIMIT 1")
    last_id_check_number = mycur.fetchall()
    if not last_id_check_number:
        id_check_answer = "1"
    else:
        last_id_check_number_number = last_id_check_number[0][0]
        id_check_answer = int(last_id_check_number_number) + 1
    conn.commit()
    # Filter out None values and convert to empty strings
    answers_filtered = [str(answer) if answer is not None else "" for answer in answers]
    print(answers_filtered)
    # Now you can safely join the list into a string
    answers_str = ', '.join(answers_filtered)
    mycur.execute(f'INSERT INTO check_answer_ginie_bet (id_check_answer, match_name, user_name, answers, user_ip_match, user_location_match)'
                  f'VALUES ("{id_check_answer}", "{match_name_adding_answer[1]}", "{user}", "{answers_str}", "{user_ip}", "{user_location}")')
    conn.commit()
    # answer_number = 1
    # for answer in answers_filtered:
    #     print(f"yes{answer_number}")
    #     mycur.execute(f"UPDATE check_answer_ginie_bet SET answer_{answer_number} = '{answer}' where id_check_answer = "
    #                   f"'{id_check_answer}'")
    #     conn.commit()
    #     time.sleep(1)
    #     answer_number += 1


@app.route('/game_on_yes', methods=['POST'])
def the_game_yes():
    global balance
    match_data = session.get('match_data')
    match_the_game_yes = match_data[1]
    global correct_count
    if request.method == 'POST':
        yes = request.form.get('yes')
        no = request.form.get('no')
        if yes == 'yes':
            questions_dict = {}  # Initialize an empty dictionary
            mycur.execute(f'select * from questions_ginie_bet where match_name = "{match_the_game_yes}"')
            questions_info = mycur.fetchall()
            conn.commit()

            # Assuming that 'question_id' is the key and 'question_text' is the value in your database
            for question in questions_info:
                question_id = question[3]  # Assuming question_id is at index 3
                question_text_4 = question[4]  # Assuming question_text at index 4
                question_text_5 = question[5]  # Assuming question_text at index 5
                question_text_6 = question[6]  # Assuming question_text at index 6
                question_text_7 = question[7]  # Assuming question_text at index 6
                questions_dict[question_id] = (question_text_4, question_text_5, question_text_6, question_text_7)

            available_questions = list(questions_dict.keys())
            # Filter out the questions that have already been asked
            remaining_questions = [q for q in available_questions if q not in asked_questions]
            print(remaining_questions)
            if not remaining_questions:
                adding_answer_sql()
                return "You have answered all the questions, please wait for the match to get over..."
            else:
                # Randomly select a question from the remaining ones
                selected_question = (remaining_questions[0])
                options = questions_dict[selected_question]
                asked_questions.append(selected_question)  # Add the question to the asked_questions list

                return render_template("game.html", options=options, question=selected_question,
                                       match=match_the_game_yes)
        elif no == 'no':
            adding_answer_sql()
            return "thankyou for participating, you shall know the results after the game is over"


@app.route('/roll_out_clicked_questions', methods=['POST', 'GET'])
def roll_out_clicked_questions():
    match_id = session.get('match_id')
    mycur.execute(f"SELECT match_name from matches_creation where match_id = '{match_id}'")
    match_roll_out_questions = mycur.fetchall()
    conn.commit()
    mycur.execute(f"UPDATE questions_ginie_bet SET roll_out = 'yes' "
                  f"where match_name = '{match_roll_out_questions[0][0]}'")
    conn.commit()
    mycur.execute(f"UPDATE matches_creation SET roll_out_questions = 'yes' "
                  f"where match_name = '{match_roll_out_questions[0][0]}'")
    conn.commit()
    return redirect(url_for('match_details', match_id=match_id))


@app.route('/roll_out_clicked_correct_answer', methods=['POST', 'GET'])
def roll_out_clicked_correct_answer():
    match_id = session.get('match_id')
    mycur.execute(f"SELECT match_name, sport_name from matches_creation where match_id = '{match_id}'")
    match_roll_out_correct = mycur.fetchall()
    conn.commit()
    mycur.execute(f"UPDATE matches_creation SET correct_answers_available = 'yes' "
                  f"where match_name = '{match_roll_out_correct[0][0]}'")
    conn.commit()
    global multiplier_details, points, balance_past, total_points, matches_won, matches_played, match_selected
    entry_fees_current = session.get('entryfees')
    time.sleep(1)
    mycur.execute(f'select correct_answer from questions_ginie_bet where match_name = "{match_roll_out_correct[0][0]}"')
    correct_answers = mycur.fetchall()
    time.sleep(1)
    mycur.execute(f'select multiplier from ginie_bet_selection where match_name = "{match_roll_out_correct[0][0]}"')
    multiplier_number = mycur.fetchone()
    time.sleep(1)
    mycur.execute(f"select * from ginie_bet.check_answer_ginie_bet where match_name = '{match_roll_out_correct[0][0]}'")
    answers_users = mycur.fetchall()
    conn.commit()
    time.sleep(1)
    for answer in answers_users:
        answer_checked = answer[4]
        if answer_checked != 'yes':
            answers_user = answer[3]
            username_check = answer[2]
            match_name_correct = answer[1]
            answers_list = answers_user.split(', ')
            if multiplier_number:
                multiplier_id_str = multiplier_number[0]
                multiplier_id = int(multiplier_id_str)
                mycur.execute(f'select * from multiplier_record where multiplier_id = "{multiplier_id}"')
                multiplier_details = mycur.fetchall()
                conn.commit()
            correct_answer_list = [answer[0] for answer in correct_answers]
            correct_count_quiz, pass_count_quiz, void_count_quiz, attempt_count_quiz = (
                check_answers(answers_list,correct_answer_list, username_check, match_name_correct))
            if correct_count_quiz + pass_count_quiz == attempt_count_quiz:
                total_count_quiz = correct_count_quiz
                if void_count_quiz == 1 and correct_count_quiz == 2:
                    print("match refunded and expelled")
                    mycur.execute(
                        f'UPDATE check_answer_ginie_bet SET won_match = "REFUNDED" where user_name = "{username_check}"')
                    conn.commit()
                    mycur.execute(f"select * from user_data where user_name = '{username_check}'")
                    balance_data = mycur.fetchall()
                    if balance_data:
                        balance_past = balance_data[0][6]
                    mycur.execute(
                        f"UPDATE user_data SET balance = '{balance_past + entry_fees_current}' WHERE user_name"
                        f" = '{username_check}'")
                    conn.commit()
                    mycur.execute(
                        "select id_finances_records from finances_records ORDER BY id_finances_records DESC LIMIT 1")
                    id_finances_records = mycur.fetchall()
                    conn.commit()
                    if id_finances_records:
                        id_finances_record_str = str(id_finances_records[0][0])
                        id_finances_record = int(id_finances_record_str) + 1
                    else:
                        id_finances_record = 1
                    mycur.execute(
                        f'INSERT INTO finances_records (id_finances_records, match_name, user_name, date_match, match_status,'
                        f' amount_won, loss, sports_name, balance, void_count) VALUES ("{id_finances_record}", '
                        f'"{match_roll_out_correct[0][0]}", "{username_check}", "{formatted_datetime}", "REFUNDED",'
                        f' "0", "0", "{match_roll_out_correct[0][1]}", "{balance_past}", '
                        f'"{void_count_quiz}")')
                    conn.commit()
                else:
                    for multiplier_quiz in multiplier_details:
                        if total_count_quiz == len(correct_answer_list):
                            flt_multiplier_bumper = float(multiplier_quiz[17])
                            points = entry_fees_current * float(flt_multiplier_bumper)
                        elif total_count_quiz == 1:
                            flt_multiplier_1 = float(multiplier_quiz[2])
                            points = float(entry_fees_current) * float(flt_multiplier_1)
                        elif total_count_quiz == 2:
                            flt_multiplier_2 = float(multiplier_quiz[3])
                            points = float(entry_fees_current) * float(flt_multiplier_2)
                        elif total_count_quiz == 3:
                            flt_multiplier_3 = float(multiplier_quiz[4])
                            points = float(entry_fees_current) * float(flt_multiplier_3)
                        elif total_count_quiz == 4:
                            flt_multiplier_4 = float(multiplier_quiz[5])
                            points = float(entry_fees_current) * flt_multiplier_4
                            print(points)
                        elif total_count_quiz == 5:
                            flt_multiplier_5 = float(multiplier_quiz[6])
                            points = float(entry_fees_current) * float(flt_multiplier_5)
                        elif total_count_quiz == 6:
                            flt_multiplier_6 = float(multiplier_quiz[7])
                            points = float(entry_fees_current) * float(flt_multiplier_6)
                        elif total_count_quiz == 7:
                            flt_multiplier_7 = float(multiplier_quiz[8])
                            points = float(entry_fees_current) * float(flt_multiplier_7)
                        elif total_count_quiz == 8:
                            flt_multiplier_8 = float(multiplier_quiz[9])
                            points = float(entry_fees_current) * float(flt_multiplier_8)
                        elif total_count_quiz == 9:
                            flt_multiplier_9 = float(multiplier_quiz[10])
                            points = float(entry_fees_current) * float(flt_multiplier_9)
                        elif total_count_quiz == 10:
                            flt_multiplier_10 = float(multiplier_quiz[11])
                            points = float(entry_fees_current) * float(flt_multiplier_10)
                        elif total_count_quiz == 11:
                            flt_multiplier_11 = float(multiplier_quiz[12])
                            points = float(entry_fees_current) * float(flt_multiplier_11)
                        elif total_count_quiz == 12:
                            flt_multiplier_12 = float(multiplier_quiz[13])
                            points = float(entry_fees_current) * float(flt_multiplier_12)
                        elif total_count_quiz == 13:
                            flt_multiplier_13 = float(multiplier_quiz[14])
                            points = float(entry_fees_current) * float(flt_multiplier_13)
                        elif total_count_quiz == 14:
                            flt_multiplier_14 = float(multiplier_quiz[15])
                            points = float(entry_fees_current) * float(flt_multiplier_14)
                        else:
                            flt_multiplier_15 = float(multiplier_quiz[16])
                            points = float(entry_fees_current) * float(flt_multiplier_15)
                    mycur.execute(f"select * from user_data where user_name = '{username_check}'")
                    balance_data = mycur.fetchall()
                    if balance_data:
                        balance_past = balance_data[0][6]
                        matches_won = int(balance_data[0][13]) + 1
                        total_points = int(balance_data[0][9]) + points
                    balance_new_current = points + balance_past
                    mycur.execute(
                        "select id_finances_records from finances_records ORDER BY id_finances_records DESC LIMIT 1")
                    id_finances_records = mycur.fetchall()
                    conn.commit()
                    if id_finances_records:
                        id_finances_record_str = str(id_finances_records[0][0])
                        id_finances_record = int(id_finances_record_str) + 1
                    else:
                        id_finances_record = 1
                    mycur.execute(
                        f'INSERT INTO finances_records (id_finances_records, match_name, user_name, date_match, match_status,'
                        f' amount_won, loss, sports_name, balance, void_count) VALUES ("{id_finances_record}", '
                        f'"{match_roll_out_correct[0][0]}", "{username_check}", "{formatted_datetime}", "WON",'
                        f' "{points}", "{points}", "{match_roll_out_correct[0][1]}", "{balance_past + points}", '
                        f'"{void_count_quiz}")')
                    conn.commit()
                    mycur.execute('select * from records_user')
                    users_record = mycur.fetchall()
                    conn.commit()
                    record_ids = []
                    for users_record in users_record:
                        record_id = users_record[0]
                        record_ids.append(record_id)
                    num_records = (len(record_ids) + 1)
                    try:
                        mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                      f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                      f") VALUES ('{num_records}', 'amount won', 'N/A', "
                                      f"'N/A', '{username_check}', '{points}', 'N/A',"
                                      f"'{formatted_datetime}','{balance_past + points}', 'N/A', 'Points A/C to {username_check} A/C')")
                        # mycur.execute('DELETE from records_user')
                        conn.commit()
                    except:
                        mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                      f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                      f") VALUES ('{num_records + 1}', 'amount won', 'N/A', "
                                      f"'N/A', '{username_check}', '{points}', 'N/A',"
                                      f"'{formatted_datetime}','{balance_past + points}', 'N/A', 'Points A/C to {username_check} A/C')")
                        # mycur.execute('DELETE from records_user')
                        conn.commit()
                    mycur.execute(
                        f'UPDATE check_answer_ginie_bet SET won_match = "yes", void_count = "{void_count_quiz}"'
                        f' where user_name = "{username_check}" and match_name = "{match_roll_out_correct[0][0]}"')
                    conn.commit()
                    mycur.execute(
                        f"UPDATE user_data SET balance = '{balance_new_current}', total_profit = '{total_points}',"
                        f"matches_won = '{matches_won}' WHERE user_name = '{username_check}'")
                    conn.commit()
            else:
                mycur.execute(
                    "select id_finances_records from finances_records ORDER BY id_finances_records DESC LIMIT 1")
                id_finances_records = mycur.fetchall()
                conn.commit()
                if id_finances_records:
                    id_finances_record_str = str(id_finances_records[0][0])
                    id_finances_record = int(id_finances_record_str) + 1
                else:
                    id_finances_record = 1
                mycur.execute(
                    f'INSERT INTO finances_records (id_finances_records, match_name, user_name, date_match, match_status,'
                    f' amount_lost, profit, sports_name, balance, void_count) VALUES ("{id_finances_record}", '
                    f'"{match_roll_out_correct[0][0]}", "{username_check}", "{formatted_datetime}", "LOST",'
                    f' "{entry_fees_current}", "{entry_fees_current}","{match_roll_out_correct[0][1]}",'
                    f' "{balance_past}", "{void_count_quiz}")')
                conn.commit()
                mycur.execute('select * from records_user')
                users_record = mycur.fetchall()
                conn.commit()
                record_ids = []
                for users_record in users_record:
                    record_id = users_record[0]
                    record_ids.append(record_id)
                num_records = (len(record_ids) + 1)
                try:
                    mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                  f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                  f") VALUES ('{num_records}', 'amount Lost', 'N/A', "
                                  f"'N/A', '{username_check}', '{points}', 'N/A',"
                                  f"'{formatted_datetime}','{balance_past}', 'N/A', '{username_check} A/C to Points A/C')")
                    # mycur.execute('DELETE from records_user')
                    conn.commit()
                except:
                    mycur.execute(f"INSERT INTO records_user (id, reason_change, old_record_user, new_record_user, "
                                  f"user_name, amount, payment_type, date, balance, action, user_ledger"
                                  f") VALUES ('{num_records + 1}', 'amount won', 'N/A', "
                                  f"'N/A', '{username_check}', '{points}', 'N/A',"
                                  f"'{formatted_datetime}','{balance_past}', 'N/A', '{username_check} A/C to Points A/C')")
                    # mycur.execute('DELETE from records_user')
                    conn.commit()
            mycur.execute(
                f'UPDATE check_answer_ginie_bet SET checked_user = "yes", void_count = "{void_count_quiz}"'
                f' where user_name = "{username_check}" and match_name = "{match_roll_out_correct[0][0]}"')
            conn.commit()
            mycur.execute(f"select * from user_data where user_name = '{username_check}'")
            balance_data = mycur.fetchall()
            if balance_data:
                matches_played = int(balance_data[0][11]) + 1
            mycur.execute(
                f"UPDATE user_data SET num_matches_played = '{matches_played}' WHERE user_name = '{username_check}'")
            conn.commit()
            time.sleep(1)
    return redirect(url_for('match_details', match_id=match_id))


@app.route('/results_match/<match_name_result>', methods=['POST', 'GET'])
def results_match(match_name_result):
    session['match_name_result'] = match_name_result
    mycur.execute(f"SELECT * FROM ginie_bet.matches_creation where match_name = '{match_name_result}'")
    match_selected_current = mycur.fetchall()
    conn.commit()

    mycur.execute(f"SELECT * FROM ginie_bet.finances_records where match_name = '{match_name_result}'")
    users_data = mycur.fetchall()
    conn.commit()

    user_number_current = len(users_data)

    users_won = [user_data for user_data in users_data if user_data[4] == "WON"]
    users_won_len = len(users_won)

    users_lost = [user_data for user_data in users_data if user_data[4] == "LOST"]
    users_lost_len = len(users_lost)

    users_refunded = [user_data for user_data in users_data if user_data[4] == "REFUNDED"]
    users_refunded_len = len(users_lost)

    total_profit_match = int(sum(user_data[7] for user_data in users_data))
    total_loss_match = int(sum(user_data[8] for user_data in users_data))

    profit_loss_match = total_profit_match - total_loss_match

    mycur.execute(
        f"SELECT * FROM finances_records where match_name = '{match_name_result}' ORDER BY total_answers_correct "
        "DESC LIMIT 5;")
    top_best_players = mycur.fetchall()
    conn.commit()

    mycur.execute(f"select question from questions_ginie_bet where match_name = '{match_name_result}'")
    questions_match = mycur.fetchall()
    conn.commit()

    mycur.execute(f"SELECT SUM(CASE WHEN answer_1 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_1,"
                  f" SUM(CASE WHEN answer_2 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_2,"
                  f" SUM(CASE WHEN answer_3 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_3,"
                  f" SUM(CASE WHEN answer_4 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_4,"
                  f" SUM(CASE WHEN answer_5 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_5,"
                  f" SUM(CASE WHEN answer_6 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_6,"
                  f" SUM(CASE WHEN answer_7 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_7,"
                  f" SUM(CASE WHEN answer_8 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_8,"
                  f" SUM(CASE WHEN answer_9 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_9,"
                  f" SUM(CASE WHEN answer_10 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_10,"
                  f" SUM(CASE WHEN answer_11 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_11,"
                  f" SUM(CASE WHEN answer_12 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_12,"
                  f" SUM(CASE WHEN answer_13 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_13,"
                  f" SUM(CASE WHEN answer_14 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_14,"
                  f" SUM(CASE WHEN answer_15 = 'Yes' THEN 1 ELSE 0 END) AS count_yes_answer_15"
                  f" FROM check_answer_ginie_bet where match_name = '{match_name_result}'")
    questions_yes_count = mycur.fetchall()
    conn.commit()
    formatted_results_yes = [str(item) for sublist in questions_yes_count for item in sublist]

    mycur.execute(f"SELECT SUM(CASE WHEN answer_1 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_1,"
                  f" SUM(CASE WHEN answer_2 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_2,"
                  f" SUM(CASE WHEN answer_3 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_3,"
                  f" SUM(CASE WHEN answer_4 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_4,"
                  f" SUM(CASE WHEN answer_5 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_5,"
                  f" SUM(CASE WHEN answer_6 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_6,"
                  f" SUM(CASE WHEN answer_7 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_7,"
                  f" SUM(CASE WHEN answer_8 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_8,"
                  f" SUM(CASE WHEN answer_9 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_9,"
                  f" SUM(CASE WHEN answer_10 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_10,"
                  f" SUM(CASE WHEN answer_11 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_11,"
                  f" SUM(CASE WHEN answer_12 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_12,"
                  f" SUM(CASE WHEN answer_13 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_13,"
                  f" SUM(CASE WHEN answer_14 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_14,"
                  f" SUM(CASE WHEN answer_15 NOT IN ('Null', 'Pass') THEN 1 ELSE 0 END) AS count_attempt_15"
                  f" FROM check_answer_ginie_bet where match_name = '{match_name_result}'")
    questions_attempt_count = mycur.fetchall()
    conn.commit()
    formatted_results_attempt = [str(item) for sublist in questions_attempt_count for item in sublist]

    mycur.execute(f"SELECT SUM(CASE WHEN answer_1 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_1,"
                  f" SUM(CASE WHEN answer_2 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_2,"
                  f" SUM(CASE WHEN answer_3 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_3,"
                  f" SUM(CASE WHEN answer_4 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_4,"
                  f" SUM(CASE WHEN answer_5 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_5,"
                  f" SUM(CASE WHEN answer_6 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_6,"
                  f" SUM(CASE WHEN answer_7 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_7,"
                  f" SUM(CASE WHEN answer_8 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_8,"
                  f" SUM(CASE WHEN answer_9 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_9,"
                  f" SUM(CASE WHEN answer_10 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_10,"
                  f" SUM(CASE WHEN answer_11 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_11,"
                  f" SUM(CASE WHEN answer_12 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_12,"
                  f" SUM(CASE WHEN answer_13 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_13,"
                  f" SUM(CASE WHEN answer_14 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_14,"
                  f" SUM(CASE WHEN answer_15 = 'void' THEN 1 ELSE 0 END) AS count_yes_answer_15"
                  f" FROM check_answer_ginie_bet where match_name = '{match_name_result}'")
    questions_yes_count = mycur.fetchall()
    conn.commit()
    formatted_results_void = [str(item) for sublist in questions_yes_count for item in sublist]

    combined_data = [
        (
            *questions_match[i],
            int(formatted_results_attempt[i]),
            int(formatted_results_yes[i]),
            int(formatted_results_void[i])
        )
        for i in range(len(questions_match))
    ]

    # Now 'combined_data' contains a list of tuples with combined values
    print(combined_data)

    # mycur.execute("SELECT * FROM finances_records WHERE  DATE(date_match) = CURDATE()")
    # todays_matches = mycur.fetchall()
    # conn.commit()

    mycur.execute(f"SELECT * FROM finances_records WHERE  match_name = '{match_name_result}'")
    current_matches = mycur.fetchall()
    conn.commit()

    return (render_template
            ("results_match.html", match_selected=match_selected_current,
             user_number=user_number_current, users_won_len=users_won_len, users_lost_len=users_lost_len,
             total_loss_match=total_loss_match, profit_loss_match=profit_loss_match, users_refunded_len=
            users_refunded_len,
             total_profit_match=total_profit_match, top_best_players=
             top_best_players, questions_attempt_count_10=combined_data, current_matches=current_matches))


@app.route('/match_user_details/<user_name>', methods=['GET', 'POST'])
def match_user_details(user_name):
    match_name_result = session.get('match_name_result')
    mycur.execute(f"SELECT * FROM ginie_bet.matches_creation where match_name = '{match_name_result}'")
    match_selected_current = mycur.fetchall()
    conn.commit()

    mycur.execute(f"select question from questions_ginie_bet where match_name = '{match_name_result}'")
    questions_match = mycur.fetchall()
    conn.commit()

    mycur.execute(f"select correct_answer from questions_ginie_bet where match_name = '{match_name_result}'")
    correct_answers_match = mycur.fetchall()
    conn.commit()

    mycur.execute(
        f"SELECT answers FROM check_answer_ginie_bet WHERE match_name = '{match_name_result}' AND user_name = '{user_name}'")
    user_answers = mycur.fetchall()
    conn.commit()

    processed_answers = []
    if user_answers:
        raw_answers = user_answers[0][0]  # Extract the first element from the fetched results
        processed_answers = [tuple(answer.split(', ')) for answer in raw_answers.split(',')]

    mycur.execute(
        f"SELECT answer_1, answer_2, answer_3, answer_4, answer_5, answer_6, answer_7, answer_8, answer_9, answer_10, "
        f"answer_11, answer_12, answer_13, answer_14, answer_15 FROM check_answer_ginie_bet WHERE "
        f"match_name = '{match_name_result}' AND user_name = '{user_name}'")
    user_status = mycur.fetchall()
    conn.commit()

    processed_user_status = []
    if user_status:
        raw_status = user_status[0]  # Extract the first element from the fetched results
        processed_user_status = [tuple(status.split(', ')) if status else ('',) for status in raw_status]

    combined_data = [
        (
            *questions_match[i],
            *processed_answers[i],
            *correct_answers_match[i],
            *processed_user_status[i]
        )
        for i in range(len(questions_match))
    ]

    # Now 'combined_data' contains a list of tuples with combined values

    mycur.execute(f"select * from user_data where user_name = '{user_name}'")
    user_details_match = mycur.fetchall()
    conn.commit()
    user = user_details_match[0]

    mycur.execute(f"select * from check_answer_ginie_bet where user_name = '{user_name}'")
    user_details_match_specific = mycur.fetchall()
    conn.commit()
    user_match = user_details_match_specific[0]
    return render_template("match_user_details.html", user=user, combined_data=combined_data,
                           match_selected=match_selected_current, user_match=user_match)


@app.route('/total_results/<match_name_result>', methods=['POST', 'GET'])
def total_results(match_name_result):
    mycur.execute(f"SELECT * FROM ginie_bet.matches_creation where match_name = '{match_name_result}'")
    match_selected_current = mycur.fetchall()
    conn.commit()

    mycur.execute(f"SELECT * FROM ginie_bet.finances_records where match_name = '{match_name_result}'")
    users_data = mycur.fetchall()
    conn.commit()

    user_number_current = len(users_data)

    users_won = [user_data for user_data in users_data if user_data[3] == "yes"]
    users_won_len = len(users_won)

    total_profit_match = int(sum(user_data[7] for user_data in users_data))
    total_loss_match = int(sum(user_data[8] for user_data in users_data))

    profit_loss_match = total_profit_match - total_loss_match

    return (render_template
            ("total_results.html", match_selected=match_selected_current,
             user_number=user_number_current, users_won_len=users_won_len, total_loss_match=total_loss_match,
             profit_loss_match=profit_loss_match, total_profit_match=total_profit_match))


#
#
#
# end ginie bet
#
#
#

#
#
#
# users
#
#
#

@app.route('/total_users', methods=['GET', 'POST'])
def total_users():
    # Fetch all user data from the database
    mycur.execute("select * from user_data")
    users_data = mycur.fetchall()
    conn.commit()
    for user in users:
        print(user[15])
    user_num = len(users_data)
    random_number = random.randint(1, 30)
    # Pass the user data to the template for rendering
    return render_template('view_users.html', users=users_data, user_num=user_num, random_number=random_number)

@app.route('/user_details/<userid>', methods=['GET', 'POST'])
def user_details(userid):
    # Find the user with the provided username
    user = None
    mycur.execute("select * from user_data")
    users_data = mycur.fetchall()
    conn.commit()
    session['userid'] = userid
    # mycur.execute(f"select * from records_user where user_name = '{user_name}'")
    # conn.commit()
    for u in users_data:
        if u[0] == int(userid):
            user = u
            break

    if user:
        user_name = user[2]
        mycur.execute(f"select * from records_user where user_name = '{user_name}'")
        records = mycur.fetchall()
        conn.commit()
        mycur.execute(f"SELECT * FROM ginie_bet.finances_records where user_name = '{user_name}'")
        matches_user = mycur.fetchall()
        conn.commit()
        return render_template("user_details.html", user=user, records=records, matches_user=matches_user)
    else:
        return "user not found"


@app.route('/update_details', methods=['POST'])
def update_full_name():
    # user = None
    # user_data = users
    userid = session.get('userid')
    # for u in user_data:
    #     if u[0] == int(userid):
    #         user = u
    #         break
    new_user_name = request.json.get('user_name')
    # new_balance = request.json.get('balance')
    # new_added_funds = request.json.get('added_funds')
    # new_withdrawn_funds = request.json.get('withdrawn_funds')
    # new_profits = request.json.get('profits')
    # new_loss = request.json.get('loss')
    new_matches_played = request.json.get('matches_played')
    new_matches_lost = request.json.get('matches_lost')
    new_matches_won = request.json.get('matches_won')
    new_bonus_points_match = request.json.get('bonus_points')
    # You can perform a database update here if needed

    mycur.execute(
        f"UPDATE user_data SET user_name = '{new_user_name}', "
        # f"balance = '{new_balance}', "
        # f"fund_added = '{new_added_funds}', fund_withdrawn = '{new_withdrawn_funds}', "
        # f"total_profit = '{new_profits}', total_loss = '{new_loss}', "
        f"num_matches_played = '{new_matches_played}', matches_lost = '{new_matches_lost}', "
        f"matches_won = '{new_matches_won}', bonus_points = '{new_bonus_points_match}' WHERE user_id = {userid}"
    )
    conn.commit()
    return jsonify({"updated_full_name": new_user_name})


@app.route('/reason_user_change', methods=['GET', 'POST'])
def reason_user_html():
    user = None
    users_data = users
    userid = session.get('userid')
    for u in users_data:
        if u[0] == int(userid):
            user = u
            break

    if user:
        return render_template("reasons_user_input.html", user=user)


@app.route('/overview_user', methods=['GET', 'POST'])
def overview_user():
    return render_template('overview.html')


@app.route('/block_user/<int:user_id>', methods=['POST'])
def block_user(user_id):
    global blocked_users
    print(user_id)
    mycur.execute(f"UPDATE user_data SET status='BLOCK' WHERE user_id = '{user_id}'")
    conn.commit()
    return jsonify({'message': 'User blocked', 'status': 'blocked'})


@app.route('/unblock_user/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    global blocked_users
    print(user_id)
    mycur.execute(f"UPDATE user_data SET status='UNBLOCK' WHERE user_id = '{user_id}'")
    conn.commit()
    return jsonify({'message': 'User blocked', 'status': 'blocked'})


@app.route('/get_users')
def get_users():
    # Replace this with your code to fetch the list of usernames
    mycur.execute('select * from ginie_bet.user_data')
    users_get_info = mycur.fetchall()
    all_users = []
    for user in users_get_info:
        all_users.append(user[2])
    # unique_users = list(set(users_list for users_list in all_users))
    # print(unique_users)
    return jsonify(all_users)


@app.route('/get_leagues')
def get_leagues():
    mycur.execute('select * from ginie_bet.matches_creation')
    leagues = mycur.fetchall()
    all_leagues = []
    for league in leagues:
        all_leagues.append(league[8])
    unique_leagues = list(set(match_league for match_league in all_leagues))
    return jsonify(unique_leagues)


@app.route('/block_unblock', methods=['GET', 'POST'])
def block_unblock_page():
    users_data = users
    user_num = len(users_data)
    random_number = random.randint(1, 30)
    # Pass the user data to the template for rendering
    return render_template('block_unblock.html', users=users_data, user_num=user_num, random_number=random_number,
                           blocked_users=blocked_users)


#
#
#
# end users
#
#
#

#
#
#
# login and register
#
#
#

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        if len(phone_number) == 10:
            if not check_existing_user(int(phone_number)):
                # Generate and send OTP
                otp = generate_otp()
                print(otp)
                # send_otp(phone_number, otp)
                global no_user_exists
                no_user_exists = True

                # Store phone number and OTP in session for validation
                session['phone_number'] = phone_number
                session['otp'] = otp

                return redirect('/otp_verification')

            else:
                return "User already exists, please log in"
        else:
            return "The phone number is invalid.Try again"
    return render_template('registration.html')


@app.route('/otp_verification', methods=['GET', 'POST'])
def otp_verification():
    global name, df, selected_sports
    if request.method == 'POST':
        entered_otp = request.form['otp']
        expected_otp = session.get('otp')

        if int(entered_otp) == int(expected_otp):
            # OTP validation successful
            if no_user_exists:
                return render_template('user_name.html')
                # Store user's data in a DataFrame
            else:
                phone_number = session.get('phone_number')
                mycur.execute(f"select user_name from user_data where user_number = {phone_number}")
                conn.commit()
                user_name = mycur.fetchall()
                if user_name:
                    user = user_name[0][0]  # Extract the balance value from the fetched data
                    session['user'] = user
                    selected_sports = []
                    mycur.execute("SELECT * FROM ginie_bet.sports_creation where soft_delete != 'yes'")
                    sports_login = mycur.fetchall()
                    for sport_info in sports_login:
                        selected_sports.append(sport_info)
                return render_template('home_page.html', sport_options=selected_sports)
        else:
            return "Invalid OTP. Login failed."

    return render_template('otp_verification.html')


@app.route('/user_name', methods=['GET', 'POST'])
def store_data():
    global user_number
    name_user = request.form['name']
    phone_number = session.get('phone_number')
    user_ip = request.remote_addr  # Get the user's IP address
    user_location = get_location(
        user_ip)  # Get location name based on IP address using Google Maps Geolocation and Geocoding APIs
    if phone_number.isdigit():  # Validate if it is a numeric string
        user_number = int(phone_number)
        # Rest of the code for inserting the data
    if users:
        number = len(users) + 1
    else:
        number = 1
    mycur.execute(
        f"INSERT INTO user_data (user_id, actual_name, user_name, user_number, register_time, last_login, balance, "
        f"fund_added, fund_withdrawn, total_profit, total_loss, num_matches_played, matches_lost, matches_won,"
        f" bonus_points, status, location_user, user_ip) "
        f"VALUES ({number},'{name_user}','{name_user}({user_number})', {user_number}, '{formatted_datetime}', '{formatted_datetime}'"
        f",'0','0','0','0','0','0','0','0','0','none', '{user_location}', '{user_ip}');")

    conn.commit()
    return render_template('home_page.html', sport_options=sport_options)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']

        if check_existing_user(int(phone_number)):
            if phone_number == "7777":
                global admin
                admin = True
                mycur.execute(
                    f"UPDATE user_data SET last_login = '{formatted_datetime}' WHERE user_number = {phone_number};")
                conn.commit()
                mycur.execute(f"select user_name from user_data where user_number = {phone_number}")
                conn.commit()
                user_name = mycur.fetchall()
                if user_name:
                    user = user_name[0][0]  # Extract the balance value from the fetched data
                    session['user'] = user
                return render_template('index.html')
            else:
                # Generate and send OTP
                otp = generate_otp()
                print(otp)
                # send_otp(phone_number, otp)
                user_ip = request.remote_addr  # Get the user's IP address
                user_location = get_location(
                    user_ip)  # Get location name based on IP address using Google Maps Geolocation and Geocoding APIs
                print(user_ip, user_location)
                # Update the last_login field in the database
                mycur.execute(
                    f"UPDATE user_data SET last_login = '{formatted_datetime}', location_user = '{user_location}'"
                    f", user_ip = '{user_ip}' WHERE user_number = {phone_number};")
                conn.commit()
                # Store phone number and OTP in session for validation
                session['phone_number'] = phone_number
                session['otp'] = otp

                return redirect('/otp_verification')
        else:
            return "Phone number not found. Registration required."

    return render_template('login.html')


#
#
#
# end login and register
#
#
#


# Function to simulate sending emails
def send_emails():
    # Your email sending logic here
    print("Sending emails...")


# Function to update database entries
def update_database():
    # Your database update logic here
    print("Updating database...")


# Function to generate reports
def generate_reports():
    # Your report generation logic here
    print("Generating reports...")


@app.route('/automate_tasks')
def automate_tasks():
    while True:
        send_emails()
        update_database()
        generate_reports()
        time.sleep(1)  # Add a 1-second delay
    return 'Tasks automated successfully!'


if __name__ == '__main__':
    app.run(debug=True)

#
#
#
# end app
#
#
#
