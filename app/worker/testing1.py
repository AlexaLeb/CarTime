import os
from joblib import load
import pandas as pd
import json

# Загружаем модель один раз при импорте
THIS_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.abspath(
    os.path.join(THIS_DIR, '..', 'best_sarimax_model.joblib')
)
_model = load(MODEL_PATH)


def predict_rides(exog: pd.DataFrame) -> pd.Series:
    """
    Делает прогноз количества поездок на периоды, заданные индексом exog.

    exog: DataFrame с колонками ['pickup_location_id', 'AWND', 'PRCP',
        'SNOW', 'SNWD', 'TMAX', 'TMIN', 'WT01'] и datetime/PeriodIndex.
    Возвращает Series прогнозных ride_count с тем же индексом.
    """
    # Проверка входных колонок
    required_cols = _model.model.exog_names
    missing = set(required_cols) - set(exog.columns)
    if missing:
        raise ValueError(f"Не хватает колонок в exog: {missing}")
    # inferring steps
    steps = len(exog)
    if steps <= 0:
        raise ValueError("exog должен содержать хотя бы одну строку")
    # проверка индекса
    if not isinstance(exog.index, (pd.DatetimeIndex, pd.PeriodIndex)):
        raise ValueError("Индекс exog должен быть DatetimeIndex или PeriodIndex")
    # прогноз
    forecast = _model.forecast(steps=steps, exog=exog)
    # назначим индекс
    try:
        forecast.index = exog.index
    except Exception:
        forecast = pd.Series(forecast, index=exog.index, name='predicted_mean')
    return forecast


def predict_from_request(request: dict) -> dict:
    """
    Обрабатывает JSON-запрос к сервису прогнозов:
    {
        'exog': [ {...row1...}, {...row2...}, ... ],
        'steps': optional int
    }

    Каждый элемент exog-row должен содержать ключ 'timestamp' и все exog-колонки.
    Если ключ 'steps' передан, он должен совпадать с длиной списка exog.

    Возвращает словарь:
    {
        'forecast': [
            {'timestamp': '...', 'ride_count': ...},
            ...
        ]
    }
    """
    if 'exog' not in request:
        raise KeyError("В запросе отсутствует ключ 'exog'")
    rows = request['exog']
    # преобразуем список dict в DataFrame
    df = pd.DataFrame(rows)
    # извлекаем или требуем шаги
    steps = request.get('steps', len(df))
    if steps != len(df):
        raise ValueError(f"steps ({steps}) не совпадает с количеством exog-строк ({len(df)})")
    # конвертация timestamp в индекс
    if 'timestamp' not in df.columns:
        raise KeyError("В exog-строках отсутствует 'timestamp'")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    # вызываем predict_rides
    preds = predict_rides(df)
    # формируем результат
    result = {'forecast': []}
    for ts, value in preds.items():
        result['forecast'].append({
            'timestamp': ts.isoformat(),
            'ride_count': float(value)
        })
    return result


if __name__ == '__main__':
    # Тестовые примеры запросов
    test_requests = [
        # прогноз на 1 период
        {
            'exog': [
                {
                    'timestamp': '2025-07-21T00:00:00',
                    'pickup_location_id': 1,
                    'AWND': 4.2,
                    'PRCP': 0,
                    'SNOW': 0,
                    'SNWD': 0,
                    'TMAX': 25,
                    'TMIN': 16,
                    'WT01': 0
                }
            ],
            'steps': 1
        },
        # прогноз на 3 периода
        {
            'exog': [
                {'timestamp': '2025-07-21T01:00:00','pickup_location_id':1,'AWND':5,'PRCP':0,'SNOW':0,'SNWD':0,'TMAX':24,'TMIN':15,'WT01':0},
                {'timestamp': '2025-07-21T02:00:00','pickup_location_id':1,'AWND':5,'PRCP':0,'SNOW':0,'SNWD':0,'TMAX':23,'TMIN':14,'WT01':0},
                {'timestamp': '2025-07-21T03:00:00','pickup_location_id':1,'AWND':5,'PRCP':1,'SNOW':0,'SNWD':0,'TMAX':22,'TMIN':14,'WT01':0}
            ],
            'steps': 3
        },
        # без явного steps (понимается длиной exog)
        {
            'exog': [
                {'timestamp': '2025-07-21T04:00:00','pickup_location_id':2,'AWND':3,'PRCP':0,'SNOW':0,'SNWD':0,'TMAX':20,'TMIN':12,'WT01':1},
                {'timestamp': '2025-07-21T05:00:00','pickup_location_id':2,'AWND':3,'PRCP':0,'SNOW':0,'SNWD':0,'TMAX':19,'TMIN':11,'WT01':1}
            ]
        }
    ]

    # Выполнение тестов и вывод результатов
    for req in test_requests:
        print(json.dumps(predict_from_request(req), ensure_ascii=False, indent=2))