from sqlmodel import Session
from models.User import User
from models.Balance import Balance
from models.crud.balance import create as bl_create, update_balance, get_all as get_all_bl, get_by_user_id as get_by_user_id_bl
import pytest
from models.Prediction_result import PredictionResult
from models.crud.prediction_result import create as pr_create, get_all as get_all_pr, get_by_task_id
from models.Prediction_task import PredictionTask
from models.crud.prediction_task import create as pt_create, get_all as get_all_pt, get_by_user_id as get_by_user_id_pt


"""
СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
"""


def test_create_user(session: Session):
    try:
        user = User(id=8, email="test_2@mail.ru", password="")
        user.set_password('set_password')
        session.add(user)
        session.commit()
        assert True
    except:
        assert False


"""
БАЛАНС ТЕСТЫ
"""


def test_create_balance_and_get_by_user_id(session: Session):
    # создаём новый баланс
    bal = bl_create(session, user_id=42, initial_amount=123.45)
    assert isinstance(bal, Balance)
    assert bal.user_id == 42
    assert bal.amount == pytest.approx(123.45)

    # забираем по user_id
    fetched = get_by_user_id_bl(session, 42)
    assert fetched is not None
    assert fetched.id == bal.id
    assert fetched.amount == pytest.approx(123.45)


def test_update_balance(session: Session):
    # создаём и тут же меняем amount
    bal = bl_create(session, user_id=7, initial_amount=10.0)
    bal.amount += 15.0
    # сохраняем через CRUD‑метод
    updated = update_balance(session, bal)
    assert isinstance(updated, Balance)
    assert updated.amount == pytest.approx(25.0)

    # убеждаемся, что в базе лежит новая сумма
    fetched = get_by_user_id_bl(session, 7)
    assert fetched.amount == pytest.approx(25.0)


def test_get_all_balance(session: Session):
    # заводим две записи
    b1 = bl_create(session, user_id=1, initial_amount=1.0)
    b2 = bl_create(session, user_id=2, initial_amount=2.0)
    all_bals = get_all_bl(session)
    # по крайней мере две записи, и среди них наши
    assert len(all_bals) >= 2
    ids = {b.id for b in all_bals}
    assert b1.id in ids
    assert b2.id in ids


def test_get_by_user_id_nonexistent(session: Session):
    # для несуществующего user_id должно вернуться None
    assert get_by_user_id_bl(session, user_id=9999) is None


"""
ПРЕДСКАЗАНИЯ ТЕСТЫ
"""


def test_create_prediction_and_get_by_task_id(session: Session):
    # создаём новую запись
    res = pr_create(session, task_id=123, recommended_distribution="{'a':10,'b':20}")
    assert isinstance(res, PredictionResult)
    assert res.task_id == 123
    assert res.recommended_distribution == "{'a':10,'b':20}"

    # проверяем, что get_by_task_id возвращает именно её
    fetched = get_by_task_id(session, 123)
    assert fetched is not None
    assert fetched.id == res.id
    assert fetched.recommended_distribution == res.recommended_distribution


def test_get_all_tasks(session: Session):
    # заводим две разных записи
    r1 = pr_create(session, task_id=1, recommended_distribution="{'x':1}")
    r2 = pr_create(session, task_id=2, recommended_distribution="{'y':2}")

    all_results = get_all_pr(session)
    # как минимум две — наши
    assert len(all_results) >= 2
    ids = {r.id for r in all_results}
    assert r1.id in ids
    assert r2.id in ids


def test_get_by_task_id_nonexistent(session: Session):
    # для несуществующего task_id должно вернуться None
    assert get_by_task_id(session, task_id=9999) is None

"""
ЗАДАНИЕ ТЕСТЫ
"""


def test_create_task_and_get_by_user_id(session: Session):
    # создаём задачу без fake‑возврата
    task = pt_create(session, user_id=7, budget_amount=100.0, preferences="{'a':1}")
    assert isinstance(task, PredictionTask)
    assert task.user_id == 7
    assert task.budget_amount == pytest.approx(100.0)
    assert task.preferences == "{'a':1}"

    # get_by_user_id должен вернуть список с нашей задачей
    lst = get_by_user_id_pt(session, 7)
    assert isinstance(lst, list)
    assert len(lst) == 1
    fetched = lst[0]
    assert fetched.id == task.id
    assert fetched.budget_amount == pytest.approx(100.0)


def test_create_with_fake(session: Session):
    # если передаём fake‑аргумент, слышимый create возвращает кортеж
    pair = pt_create(session, user_id=5, budget_amount=50.0, preferences="{}", fake="dummy")
    assert isinstance(pair, tuple) and len(pair) == 2
    task, fake = pair
    assert isinstance(task, PredictionTask)
    assert fake == "dummy"


def test_get_all_predict(session: Session):
    # заводим две задачи для разных user_id
    t1 = pt_create(session, user_id=1, budget_amount=10.0, preferences="{}")
    t2 = pt_create(session, user_id=2, budget_amount=20.0, preferences="{}")
    all_tasks = get_all_pt(session)
    # как минимум две
    assert len(all_tasks) >= 2
    ids = {t.id for t in all_tasks}
    assert t1.id in ids
    assert t2.id in ids


def test_get_by_user_id_no_tasks(session: Session):
    # для несуществующего пользователя список пуст
    assert get_by_user_id_pt(session, user_id=9999) == []

