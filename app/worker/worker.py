import json
import time
import pika
from database.database import get_session
from models.services.prediction import prediction
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def callback(ch, method, properties, body):
    logger.info(f'Получено сообщение {body}')
    try:
        # Предположим, сообщение приходит как JSON
        message = json.loads(body)
        user_id = message.get("user_id")
        budget_amount = message.get("budget_amount")
        preferences = message.get("preferences")
    except Exception as e:
        logger.error(f'Ошибка {e}')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    # Создаем сессию для работы с БД; используем context manager для автоматического закрытия
    session = next(get_session())
    # Поскольку алгоритм предсказания отсутствует, мы просто формируем фиктивный результат:
    simulated_result = f"Simulated result for budget {budget_amount} and preferences {preferences}"
    logger.info("Симулирован результат работы алгоритма")
    # Вызываем функцию, которая обрабатывает задачу предсказания:
    # create_prediction_task(session, user_id, budget_amount, preferences, simulated_result)
    prediction.create_prediction(session, user_id, 500, 50)

    # def create_prediction(session, user_id: int, region: str, predicted_value: int, cost: Decimal)
    # Формирование ответа: создаем JSON-объект с результатом предсказания
    response = json.dumps({
        "predicted_result": simulated_result
    })
    # Если в свойствах сообщения указан reply_to, отправляем ответ обратно
    if properties.reply_to:
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            ),
            body=response
        )
        logger.info("Ответ отправлен в очередь:", properties.reply_to)

    # Подтверждаем получение сообщения
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("\n\n\n\n\n\n\n\nЗадача обработана, баланс обновлен, транзакция и результат сохранены.\n\n\n\n\n\n")


def create_connection(max_attempts=10):
    for attempt in range(max_attempts):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq", heartbeat=100))
            logger.info("Соединение установлено.")
            return connection
        except pika.exceptions.AMQPConnectionError:
            logger.warning(f"Попытка {attempt+1}: не удалось установить соединение с RabbitMQ, повтор через 5 секунд...")
            time.sleep(5)
    raise Exception("Не удалось установить соединение с RabbitMQ после нескольких попыток.")


def main():
    # Настраиваем подключение к RabbitMQ. Обратите внимание, что хост должен быть именем сервиса RabbitMQ (например, "rabbitmq")
    connection = create_connection()
    channel = connection.channel()

    # Объявляем очередь (durable означает, что сообщения сохраняются при перезапуске сервера)
    channel.queue_declare(queue="prediction_tasks", durable=True)

    # Ограничиваем количество не подтвержденных сообщений
    channel.basic_qos(prefetch_count=1)

    # Подписываемся на очередь
    channel.basic_consume(queue="prediction_tasks", on_message_callback=callback)
    logger.info("Worker (слушатель) запущен. Ожидаем сообщений...")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.warning("Worker остановлен вручную.")
        channel.stop_consuming()
        connection.close()
        logger.info("соединение закрыто")
    except Exception as err:
        logger.error("Неожиданная ошибка слушателя:", err)


if __name__ == "__main__":
    logger.info('\n\n\nWorker is here\n\n\n')
    while True:
        try:
            main()  # запускает потребителя, блокирует на start_consuming()
        except Exception as err:
            logger.error("Worker умер, попытка переподключиться через 5 секунд:", err)
            time.sleep(5)
        else:
            logger.warning('Worker перестал работать')
            break
