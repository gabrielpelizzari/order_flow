from worker_app.consumers.runner import run_consumer
from worker_app.services.stock_service import CONSUMER_NAME, process_stock_event


def main() -> None:
    run_consumer(
        queue_name="q.stock.payment_approved",
        consumer_name=CONSUMER_NAME,
        expected_event_types={"payment.approved"},
        required_data_fields={"order_id", "total_cents"},
        processor=process_stock_event,
    )


if __name__ == "__main__":
    main()
