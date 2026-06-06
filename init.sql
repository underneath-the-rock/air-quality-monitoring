CREATE TABLE air_quality
 (id bigint NOT NULL,
  station_name varchar NOT NULL,
  timestamp timestamptz NOT NULL,
  aqi bigint,
  pm25 int,
  pm10 int,
  PRIMARY KEY (id, timestamp));