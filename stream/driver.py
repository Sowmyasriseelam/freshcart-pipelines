import argparse
import json
import os

import pika

EXCHANGE = "rapido-dispatch"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("pattern")
    args = parser.parse_args()

    url = os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/%2F")
    conn = pika.BlockingConnection(pika.URLParameters(url))
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    result = ch.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    ch.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=args.pattern)
    ch.basic_qos(prefetch_count=1)

    print(f"{args.name} listening: pattern={args.pattern} queue={queue_name}")

    def callback(channel, method, properties, body):
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        if not payload.get("zone"):
            print(f"{args.name} NACK id={payload.get('id')} key={method.routing_key}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            print(f"{args.name} RECEIVED id={payload.get('id')} key={method.routing_key}")
            channel.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
