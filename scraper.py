from sqlalchemy import create_engine
import traceback
import requests
import dbinfo 
import traceback
import time
import datetime
import glob
import os


URI="dbbikes2.cytgvbje9wgu.us-east-1.rds.amazonaws.com"
PORT="3306"
DB="dbbikes2"
USER="admin"
PASSWORD="DublinBikes1"

engine = create_engine("mysql+mysqldb://{}:{}:@{}:{}/{}".format(USER, PASSWORD, URI, PORT, DB), echo=True).connect()
sql = """
CREATE DATABASE IF NOT EXISTS dbbikes2;
"""

engine.execute(sql)

for res in engine.execute("SHOW VARIABLES;"):
    print(res)

def write_to_file(text):
    with open("data/bikes_{}".format(now).replace(" ", "_"), "w") as f:
        f.write(r.text)

def main():
    while True:
        try:
            now = datetime.datetime.now()
            r = requests.get(dbinfo.STATIONS_URI, params={"apiKey": dbinfo.JCKEY, "contract": dbinfo.NAME})
            print(r, now)
            write_to_file(r.text)
            time.sleep(5*60)
        except:
            print(traceback.format_exc())
            if engine is None:
                return
