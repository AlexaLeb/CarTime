import pandas as pd
from model import predict_from_dataframe, get_required_exog_columns


def test_predict_from_dataframe():
    """
    Пример тестовой функции, демонстрирующей вызов predict_from_dataframe
    с pandas DataFrame.
    """
    cols = get_required_exog_columns()
    now = pd.Timestamp('2025-07-21T00:00:00')
    future_index = pd.date_range(start=now, periods=2, freq='H')
    df = pd.DataFrame({col: [i for _ in range(2)] for i, col in enumerate(cols)}, index=future_index)
    forecast = predict_from_dataframe(df)
    print("Forecast from DataFrame:")
    print(forecast)


def test_predict_from_json_list():
    """
    Пример тестовой функции, демонстрирующей вызов predict_from_dataframe
    со списком словарей (JSON-like list).
    """
    cols = get_required_exog_columns()
    # Создаем JSON-список на 3 периода
    now = pd.Timestamp('2025-07-21T00:00:00')
    future_timestamps = [now + pd.Timedelta(hours=i) for i in range(3)]
    json_list = []
    for i, ts in enumerate(future_timestamps):
        entry = {'timestamp': ts.isoformat()}
        # dummy значения: i, i+1, ... для демонстрации
        entry.update({col: i for col in cols})
        json_list.append(entry)

    forecast = predict_from_dataframe(json_list)
    print("Forecast from JSON list:")
    print(forecast)


if __name__ == "__main__":
    test_predict_from_dataframe()
    test_predict_from_json_list()
