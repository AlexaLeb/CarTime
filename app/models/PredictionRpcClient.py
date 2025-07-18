import json
import uuid
import pika


class PredictionRpcClient:
    """
    RPC‑клиент для отправки запроса на предсказание в очередь RabbitMQ.
    Основан на примере с Fibonacci RPC.
    """
    def __init__(self):
        # В docker-compose имя сервиса RabbitMQ обычно: "rabbitmq"
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq", heartbeat=600)
        )
        self.channel = self.connection.channel()
        # Объявляем уникальную временную очередь для получения ответов
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self, ch, method, properties, body):
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self, payload: dict) -> dict:
        self.response = None
        self.corr_id = str(uuid.uuid4())
        # Публикуем сообщение в очередь "prediction_rpc_queue"
        self.channel.basic_publish(
            exchange='',
            routing_key='prediction_tasks',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(payload)
        )
        # Ожидаем ответа (блокирующее ожидание)
        while self.response is None:
            self.connection.process_data_events()
        return json.loads(self.response.decode())
