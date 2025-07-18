FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Устанавливаем PYTHONPATH, чтобы Python видел `app/` как пакет
ENV PYTHONPATH=/app

# Теперь запускаем модуль через -m
CMD ["python", "-m", "app.worker.worker"]