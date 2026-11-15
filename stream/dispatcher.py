import argparse
import json
import os
import random
import time
from datetime import datetime, timezone

import pika

EXCHANGE = "rapido-dispatch"
CITIES = ["bangalore", "chennai"]
ZONES = ["koramangala", "indiranagar", "whitefield", "tnagar"]
TYPES = ["ride", "food"]


def connect():
    url = os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/%2F")
    return pika.BlockingConnection(pika.URLParameters(url))


def publish(ch, message_id, force_key=None, bad=False):
    city = random.choice(CITIES)
    zone = random.choice(ZONES)
    kind = random.choice(TYPES)
    key = force_key or f"{city}.{zone}.{kind}"
    payload = {"id": message_id, "city": city, "type": kind,
               "ts": datetime.now(timezone.utc).isoformat()}
    if not bad:
        payload["zone"] = zone
    ch.basic_publish(
        exchange=EXCHANGE,
        routing_key=key,
        body=json.dumps(payload),
        properties=pika.BasicProperties(content_type="application/json",
                                        delivery_mode=1),
        mandatory=True,
    )
    print(f"PUBLISHED id={message_id} key={key} bad={bad}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--test-key", help="Publish one exact routing key and exit")
    args = parser.parse_args()

    conn = connect()
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    try:
        if args.test_key:
            publish(ch, 1, force_key=args.test_key)
            return
        for i in range(1, args.count + 1):
            publish(ch, i, bad=(i % 10 == 0))
            time.sleep(args.interval)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
