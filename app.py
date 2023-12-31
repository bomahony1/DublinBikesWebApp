from flask import Flask, g, render_template, jsonify
from sqlalchemy import create_engine, text
import traceback
import functools
import requests
import time
import simplejson as json
from datetime import datetime
import pickle
import pandas as pd

# Database configuration
URI = ""
PORT = ""
DB = ""
USER = ""
PASSWORD = ""   
engine = create_engine("mysql+mysqldb://{}:{}@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB), echo=True)

# opening pickle file with pretrained model
with open('MLModel/model.pkl', 'rb') as handle:
    model = pickle.load(handle)

# Initialize Flask app
app = Flask("__name__")

@app.route('/')
def home():
    return render_template('index.html')

##JCDeaux API Key
JCDEAUXAPI =  "#Replace with API"

# Define the function to get availability data
@app.route("/stations")
@functools.lru_cache(maxsize=128)
def get_stations():
    try: 
        # Retrieve the data passed into the function and load it as a JSON object
        text = requests.get(JCDEAUXAPI).text
        stations = json.loads(text)    
        return stations
    
    except Exception as e:
        print(traceback.format_exc())
        return "Error in get_stations: " + str(e), 404


##Weather API Key
WEATHERAPI = "http://api.openweathermap.org/data/2.5/weather?appid=APIKEY&q=Dublin, IE"

# Define the function to get weather data
@app.route("/weather")
def get_weather():
    try: 
        # Retrieve the data passed into the function and load it as a JSON object
        text = requests.get(WEATHERAPI).text
        weather = json.loads(text)
        # Extract the necessary values from the JSON object
        vals = (weather["weather"][0]["main"], weather["weather"][0]["description"], weather["main"]["temp"], weather["visibility"], weather["wind"]["speed"], weather["wind"]["deg"], weather["clouds"]["all"], datetime.timestamp(datetime.now()))
        #print('#found {} Availability {}'.format(len(vals), vals))
        return weather
    except Exception as e:
        print(traceback.format_exc())
        return "Error in get_weather: " + str(e), 404
    
# Define the main function that will call the get_stations function every 30 seconds
def update_data():
    while True:
        try:
            # Call the get_stations function and update the stations variable
            stations = get_stations()
            weather = get_weather()
            # print("Data updated at {}".format(datetime.now()))
            # Sleep for 30 seconds before calling the function again
            time.sleep(60)
        except Exception as e:
            print(traceback.format_exc())
            print("Error updating data: {}".format(e))
            # Sleep for 30 seconds before calling the function again
            time.sleep(60)
        return stations, weather

    
@app.route("/predictions/<int:number>")
def get_predict(number):
    try:
        WEATHERAPI = "http://api.openweathermap.org/data/2.5/forecast?lat=53.3498&lon=6.2603&appid=d5de0b0a9c3cc6473da7d0005b3798ac"
        # Need to get Temperature, Wind Speed, Wind direction, Clouds 
        text = requests.get(WEATHERAPI).text
        forecast = json.loads(text)['list']
        predictions = {}

        text = requests.get(JCDEAUXAPI).text
        stations = json.loads(text)
        for station in stations:
            if station['number'] == number:
                stand_number = station['bike_stands'] 
                

        # initialize predictions dictionary for all seven days of the week
        for i in range(7):
            predictions[i] = {}
        
        for i in forecast:
            datetime_obj = datetime.fromtimestamp(i['dt'])
            hour = int(datetime_obj.strftime("%H"))
            day = int(datetime_obj.weekday())

            # Weather API only forecasts every 5 hours, so need to fill in any gap
            for j in range(5):
                df = pd.DataFrame(columns=["number","temp", "wind_speed","wind_direction","clouds","hour",'weekday_or_weekend_weekday','weekday_or_weekend_weekend'])
                df.loc[0, "number"] = number
                df.loc[0, "temp"] = i["main"]["temp"]
                df.loc[0, "wind_speed"] = i["wind"]["speed"]
                df.loc[0, "wind_direction"] = i["wind"]["deg"]
                df.loc[0, "clouds"] = i["clouds"]["all"]
                # Need variables to show with bike stand predictions
                temp = i["main"]["temp"]
                description = i["weather"][0]["description"]
                icon = i["weather"][0]["icon"]

                # Check in case it has gone into the next day
                if (hour + j) >= 24:
                    day += 1
                    if day == 7:
                        day = 0
                    hour -= 24
                df.loc[0, "hour"] = hour + j
                # Model takes weekday or weekend instead  of which day of the week it is
                if day < 5:
                    df.loc[0, "weekday_or_weekend_weekend"] = 0
                    df.loc[0, "weekday_or_weekend_weekday"] = 1
                else:
                    df.loc[0, "weekday_or_weekend_weekend"] = 1
                    df.loc[0, "weekday_or_weekend_weekday"] = 0
                # Make prediction and add it and forecast to dictionary
                prediction = int(model.predict(df).tolist()[0])
                predictions[day][hour+j] = [prediction, temp, description, icon]
        
            # Forecast only predicts for 5 days at a time, if a position in dictionary is empty, will fill with most recent weather data.
            for j in range(24):
                for i in range(7):
                    try:
                        a = predictions[i][j]
                    except:
                        df.loc[0, "hour"] = j
                        day = i
                        if day < 5:
                            df.loc[0, "weekday_or_weekend_weekend"] = 0
                            df.loc[0, "weekday_or_weekend_weekday"] = 1
                        else:
                            df.loc[0, "weekday_or_weekend_weekend"] = 1
                            df.loc[0, "weekday_or_weekend_weekday"] = 0
                        predictions[i][j] = [int(model.predict(df).tolist()[0]), temp, description, icon]
        # Will add stand number at end of dictionary so can get available stands as well
        predictions[8] = stand_number
        return predictions
    
    except Exception as e:
        print(traceback.format_exc())
        return "Error in get_predict: " + str(e), 404
    

@app.route("/averages/<int:number>")
def get_averages(number):
    try:
        sql = text("""SELECT s.address, AVG(a.available_bike_stands) AS Avg_bike_stands,
                AVG(a.available_bikes) AS Avg_bikes_free, 
                DATE_FORMAT(FROM_UNIXTIME(a.datetime), '%a') AS day_of_week FROM dbbikes2.station s
                JOIN dbbikes2.availability2 a ON s.number = a.number AND DATE_FORMAT(FROM_UNIXTIME(a.datetime), '%a') IS NOT NULL
                WHERE s.number = :number
                GROUP BY s.address, day_of_week
                ORDER BY s.address, day_of_week;""")
        
        df = pd.read_sql(sql, engine, params={'number': number})   
        df = df.to_dict(orient="records")   
        return jsonify(df)
    
    except Exception as e:
        print(traceback.format_exc())
        return "Error in get_averages: " + str(e), 404
    
if __name__ == "__main__":
    # Start a new thread to continuously update the data
    import threading
    t = threading.Thread(target=update_data)
    t.start()
    app.run(debug=True)