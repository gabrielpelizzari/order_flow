from worker_app.consumers.runner import run_consumer
from worker_app.services.shipping_service import CONSUMER_NAME, process_shipping_event


def main() -> None:
    run_consumer(
        queue_name="q.shipping.stock_reserved",
        consumer_name=CONSUMER_NAME,
        expected_event_types={"stock.reserved"},
        required_data_fields={"order_id", "total_cents"},
        processor=process_shipping_event,
    )


if __name__ == "__main__":
    main()
