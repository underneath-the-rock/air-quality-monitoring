import requests
import psycopg2
import os
from dotenv import load_dotenv, dotenv_values
from config import STATIONS

load_dotenv()

proxies = {
    "http": os.getenv("PROXY"),
    "https": os.getenv("PROXY"),
}

conn = psycopg2.connect(
    dbname=os.getenv("CONN_DBNAME"),
    user=os.getenv("CONN_USER"),
    password=os.getenv("CONN_PASSWORD"),
    host=os.getenv("CONN_HOST"),
)


def fetch_data(token, stations):
    results = []
    for station in stations:
        link = "https://api.waqi.info/feed/" + station + "/?token=" + token
        response = requests.get(link, proxies=proxies)
        response_dict = response.json()
        status = response_dict["status"]
        if response.status_code != 200:
            continue
        elif status != "ok":
            continue
        else:
            results.append(parse_response(response_dict))
    return results


def parse_response(raw):
    return {
        "id": raw["data"]["idx"],
        "station_name": raw["data"]["city"]["name"],
        "timestamp": raw["data"]["time"]["iso"],
        "aqi": raw["data"]["aqi"] if raw["data"]["aqi"] != "-" else None,
        "pm25": (
            raw["data"]["iaqi"]["pm25"]["v"] if "pm25" in raw["data"]["iaqi"] else None
        ),
        "pm10": (
            raw["data"]["iaqi"]["pm10"]["v"] if "pm10" in raw["data"]["iaqi"] else None
        ),
    }


def save_to_db(conn, data):
    cursor = conn.cursor()
    for station in data:
        insert_query = """
        INSERT INTO air_quality (id, station_name, timestamp, aqi, pm25, pm10)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id, timestamp) DO NOTHING;
        """
        to_insert = (
            station["id"],
            station["station_name"],
            station["timestamp"],
            station["aqi"],
            station["pm25"],
            station["pm10"],
        )
        cursor.execute(insert_query, to_insert)
        conn.commit()
        print("Data inserted successfully!")
        print(f"Inserted data: {station}")
    cursor.close()
    conn.close()


save_to_db(conn, fetch_data(os.getenv("TOKEN"), STATIONS))
