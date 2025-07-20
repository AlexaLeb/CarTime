import os
from joblib import load
import pandas as pd
from typing import List, Union

# Загрузка SARIMAX-модели при импорте модуля
THIS_DIR = os.path.dirname(__file__)
DEFAULT_MODEL_PATH = os.path.abspath(
    os.path.join(THIS_DIR, '..', 'best_sarimax_model.joblib')
)
_model = load(DEFAULT_MODEL_PATH)


def get_required_exog_columns() -> List[str]:
    """
    Возвращает список названий колонок, которые ожидает SARIMAX-модель в качестве экзогенных переменных.

    Returns
    -------
    List[str]
        ['pickup_location_id', 'AWND', 'PRCP', 'SNOW', 'SNWD', 'TMAX', 'TMIN', 'WT01']
    """
    return _model.model.exog_names


def predict_from_dataframe(
    data: Union[pd.DataFrame, List[dict]]
) -> pd.Series:
    """
    Делает прогноз количества поездок на основе входного набора данных.

    Принимаемые форматы:
    ---------------------
    - pandas.DataFrame
      * Колонки: должны содержать все имена из get_required_exog_columns().
      * Индекс: DateTimeIndex или PeriodIndex с частотой, которая соответствует обучению модели (например, 'H' для почасового ряда).
      * Если вместо индекс-таймстемпов передана колонка 'timestamp', функция автоматически преобразует её в DateTimeIndex и удалит.

    - Список словарей (List[dict])
      * Каждый словарь должен содержать ключ 'timestamp' (в формате ISO8601) и все экзогенные поля.
      * Функция автоматически преобразует список в DataFrame и настраивает индекс.

    Возвращаемые данные:
    --------------------
    pandas.Series
      * Название: 'predicted_mean'
      * Индекс: совпадает с временным индексом входных данных (DateTimeIndex).
      * Значения: прогноз количества поездок (ride_count) на каждый период.

    Пример:

    # >>> import pandas as pd
    # >>> from ml_utils import predict_from_dataframe
    # >>> df = pd.DataFrame(
    # ...     [
    # ...         {'timestamp': '2025-07-21T00:00:00', 'pickup_location_id':1, 'AWND':5, 'PRCP':0, 'SNOW':0, 'SNWD':0, 'TMAX':22, 'TMIN':15, 'WT01':0},
    # ...         # ... ещё словари или строки DataFrame
    # ...     ]
    # ... )
    # >>> forecast = predict_from_dataframe(df)
    # >>> print(forecast)

    """
    # Преобразуем список словарей в DataFrame
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError("Аргумент data должен быть pandas.DataFrame или List[dict]")

    # Если есть колонка 'timestamp', преобразуем её в индекс
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

    # Проверяем тип индекса
    if not isinstance(df.index, (pd.DatetimeIndex, pd.PeriodIndex)):
        raise ValueError("Индекс должен быть DateTimeIndex или PeriodIndex, либо вход должен содержать колонку 'timestamp'.")

    # Проверяем экзогенные колонки
    required = set(get_required_exog_columns())
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Входной DataFrame не содержит колонки: {missing}")

    # Определяем количество шагов
    steps = len(df)
    if steps < 1:
        raise ValueError("Входной набор данных должен содержать хотя бы одну запись.")

    # Выполняем прогноз
    forecast = _model.forecast(steps=steps, exog=df)

    # Назначаем индекс
    try:
        forecast.index = df.index
    except Exception:
        forecast = pd.Series(forecast, index=df.index, name='predicted_mean')

    return forecast
