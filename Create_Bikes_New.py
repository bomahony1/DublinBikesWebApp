from sqlalchemy import create_engine
import simplejson as json
import requests


##Parameters for creating sql engine
URI = ""
PORT = ""
DB = ""
USER = ""
PASSWORD = ""
engine = create_engine("mysql+mysqldb://{}:{}@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB), echo=True)


##create station table, static data
sql = """
CREATE TABLE IF NOT EXISTS station (
   address VARCHAR(256),
   banking INTEGER,
   total_bike_stands INTEGER,
   number INTEGER,
   position_lat REAL,
   position_lng REAL
)
"""
try:
    res = engine.execute(sql)
    print(res.fetchall())
except Exception as e:
    print(e)


##create availability table, dynamic data to be filled by scraper script
sql = """
CREATE TABLE IF NOT EXISTS availability2 (
number INTEGER,
available_bikes INTEGER,
available_bike_stands INTEGER,
status VARCHAR(256),
datetime INTEGER
)
"""
try:
    res = engine.execute(sql)
    print(res.fetchall())
except Exception as e:
    print(e)


##function to fill static data table with json data
def stations_to_db(text):
    stations = json.loads(text)
    for station in stations:
        vals = (station.get('address'), int(station.get('banking')), station.get('bike_stands'), station.get('number'), station.get('position').get('lat'), station.get('position').get('lng'))
        engine.execute("insert into station values(%s,%s,%s,%s,%s,%s)", vals)
    return

##API request to get stations data from JCDeceaux
URI =  "https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey=API_KEY"
r = requests.get(URI)
json.loads(r.text)
stations_to_db(r.text) ##calling filler function


# Creating weather table, to be filled by scraper script
sql = """
CREATE TABLE IF NOT EXISTS weather2 (
main VARCHAR(256),
description VARCHAR(256),
temp REAL,
visibility REAL,
wind_speed FLOAT,
wind_direction FLOAT,
clouds FLOAT,
datetime INTEGER
)
"""
try:
    res = engine.execute(sql)
    print(res.fetchall())
except Exception as e:
    print(e)
