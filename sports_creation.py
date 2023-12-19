import mysql.connector

conn = mysql.connector.connect(
    user="root",
    password="abcd1234",
    host="localhost",
    database="ginie_bet",
    port="3306"
)

mycur = conn.cursor()
# mycur.execute('select * from ginie_bet.sports_creation')


def sport_number():
    mycur.execute('select * from ginie_bet.sports_creation')
    sports = mycur.fetchall()
    number = len(sports) + 1
    return number

def sports_creation_sql(sports_id, sports_name, sports_icon):
    query = "INSERT INTO sports_creation (sports_id, sports_name, sports_icon) VALUES (%s, %s, %s);"
    values = (sports_id, sports_name, sports_icon)
    mycur.execute(query, values)
    conn.commit()
    return True

def sports_delete_creation(sport_id):
    mycur.execute(f"DELETE FROM sports_creation where sports_id = {sport_id}")
    conn.commit()
    return True



# sports_creation_sql(sports_id=sport_number,sports_name=sports_namee, sports_icon=sports_icone)
# sports_delete_creation(3)