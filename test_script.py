from unittest.mock import patch, Mock
from script import fetch_data, parse_response, save_to_db


def test_fetch_data_success():
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "status": "ok",
        "data": {
            "idx": 123,
            "city": {"name": "Moscow"},
            "time": {"iso": "2024-01-01T12:00:00+03:00"},
            "aqi": 30,
            "iaqi": {"pm25": {"v": 10}, "pm10": {"v": 20}},
        },
    }

    with patch("script.requests.get", return_value=fake_response):
        result = fetch_data("fake_token", ["moscow"])

    assert len(result) == 1
    assert result[0]["station_name"] == "Moscow"


def test_fetch_data_wrong_status_code():
    fake_response = Mock()
    fake_response.status_code = 404
    fake_response.json.return_value = {
        "status": "ok",
        "data": {
            "idx": 123,
            "city": {"name": "Moscow"},
            "time": {"iso": "2024-01-01T12:00:00+03:00"},
            "aqi": 30,
            "iaqi": {"pm25": {"v": 10}, "pm10": {"v": 20}},
        },
    }

    with patch("script.requests.get", return_value=fake_response):
        result = fetch_data("fake_token", ["moscow"])

    assert len(result) == 0


def test_fetch_data_status_not_ok():
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "status": "not ok",
        "data": {
            "idx": 123,
            "city": {"name": "Moscow"},
            "time": {"iso": "2024-01-01T12:00:00+03:00"},
            "aqi": 30,
            "iaqi": {"pm25": {"v": 10}, "pm10": {"v": 20}},
        },
    }

    with patch("script.requests.get", return_value=fake_response):
        result = fetch_data("fake_token", ["moscow"])

    assert len(result) == 0


def test_parse_response_normal():
    raw = {
        "data": {
            "idx": 123,
            "city": {"name": "Moscow"},
            "time": {"iso": "2024-01-01T12:00:00+03:00"},
            "aqi": 30,
            "iaqi": {"pm25": {"v": 10}, "pm10": {"v": 20}},
        }
    }

    result = parse_response(raw)

    assert result["id"] == 123
    assert result["station_name"] == "Moscow"
    assert result["timestamp"] == "2024-01-01T12:00:00+03:00"
    assert result["aqi"] == 30
    assert result["pm25"] == 10
    assert result["pm10"] == 20


def test_parse_response_edge():
    raw = {
        "data": {
            "idx": 123,
            "city": {"name": "Moscow"},
            "time": {"iso": "2024-01-01T12:00:00+03:00"},
            "aqi": "-",
            "iaqi": {},
        }
    }

    result = parse_response(raw)

    assert result["id"] == 123
    assert result["station_name"] == "Moscow"
    assert result["timestamp"] == "2024-01-01T12:00:00+03:00"
    assert result["aqi"] == None
    assert result["pm25"] == None
    assert result["pm10"] == None


def test_save_to_db_success():
    mock_cursor = Mock()
    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor

    data = [
        {
            "id": 123,
            "station_name": "Moscow",
            "timestamp": "2024-01-01T12:00:00+03:00",
            "aqi": 30,
            "pm25": 10,
            "pm10": 20,
        }
    ]

    save_to_db(mock_conn, data)

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_save_to_db_no_data():
    mock_cursor = Mock()
    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor

    data = []

    save_to_db(mock_conn, data)

    mock_cursor.execute.assert_not_called()
    mock_conn.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()
