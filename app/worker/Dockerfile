#Dockerfile.worker

FROM python:3.10-slim

# Не буферизуем вывод, чтобы логи шли сразу
ENV PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# 1) Скопировать файл зависимостей воркера и установить
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Скопировать весь проект
COPY . .

# 3) Установить PYTHONPATH так, чтобы корень проекта был в путях поиска
ENV PYTHONPATH=/app

# 4) По умолчанию просто запускаем скрипт напрямую
#    Это обходит проблемы с module-spec, когда python -m не находит пакет
CMD ["python", "worker.py"]






#FROM python:3.10
#
#WORKDIR /app
#
#COPY requirements.txt .
#RUN pip install --upgrade pip && pip install -r requirements.txt
#
#COPY . .
#
## Устанавливаем PYTHONPATH, чтобы Python видел `app/` как пакет
#ENV PYTHONPATH=/app
#
## Теперь запускаем модуль через -m
#CMD ["python", "-m", "app.worker.worker"]