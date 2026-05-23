import pandas as pd
import psycopg2
import streamlit as st
import os
import plotly.express as px
import datetime
from dotenv import load_dotenv, dotenv_values

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("CONN_DBNAME"),
    user=os.getenv("CONN_USER"),
    password=os.getenv("CONN_PASSWORD"),
    host=os.getenv("CONN_HOST"),
)

st.set_page_config(page_title="Air Quality Monitor", layout="wide")
st.title("Мониторинг качества воздуха")


@st.cache_data(ttl=300)
def get_data():
    return pd.read_sql(
        "SELECT * FROM air_quality ORDER BY station_name, timestamp", conn
    )


df = get_data()
df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/Moscow")

with st.sidebar:
    st.header("Фильтры")

    stations = sorted(df["station_name"].unique())
    selected_stations = st.multiselect(
        "Станции",
        options=stations,
        default=stations,
    )

    metric = st.selectbox(
        "Показатель",
        options=["aqi", "pm25", "pm10"],
        format_func=lambda x: {"aqi": "AQI", "pm25": "PM2.5", "pm10": "PM10"}[x],
    )

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Начальная дата", value=df["timestamp"].min().date())
        start_time = st.time_input("Начальное время", value=datetime.time(0, 0))

    with col2:
        end_date = st.date_input("Конечная дата", value=df["timestamp"].max().date())
        end_time = st.time_input("Конечное время", value=datetime.time(23, 59))

    start_dt = datetime.datetime.combine(start_date, start_time)
    end_dt = datetime.datetime.combine(end_date, end_time)

    health = {
        "AQI": ["0–50", "51–100", "101–150", "151–200", "201–300", "300+"],
        "Уровень загрязнения": [
            "Низкий",
            "Умеренный",
            "Выше нормы",
            "Высокий",
            "Очень высокий",
            "Опасный",
        ],
    }
    st.table(health)

filtered = df[
    df["station_name"].isin(selected_stations)
    & (df["timestamp"].dt.tz_localize(None) >= start_dt)
    & (df["timestamp"].dt.tz_localize(None) <= end_dt)
]

fig = px.line(
    filtered,
    x="timestamp",
    y=metric,
    color="station_name",
    labels={
        "timestamp": "Время",
        metric: metric.upper(),
        "station_name": "Станция",
    },
    title=f"Динамика {metric.upper()} по станциям",
)

fig.update_layout(
    hovermode="x unified",
    legend_title="Станция",
    height=600,
)

st.plotly_chart(fig)

st.caption("Данные: World Air Quality Index Project (waqi.info)")

st.subheader("Статистика за период")
summary = (
    filtered.groupby("station_name")[["aqi", "pm25", "pm10"]]
    .agg(["mean", "max", "min"])
    .round(1)
)
summary.columns = [f"{col[0].upper()} ({col[1]})" for col in summary.columns]
summary.index.name = "Название станции"
st.dataframe(summary)
