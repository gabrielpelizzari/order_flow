from worker_app.consumers.runner import run_consumer
from worker_app.services.payment_service import CONSUMER_NAME, process_payment_event


def main() -> None:
    run_consumer(
        queue_name="q.payment.order_created",
        consumer_name=CONSUMER_NAME,
        expected_event_types={"order.created"},
        required_data_fields={"order_id", "total_cents"},
        processor=process_payment_event,
    )


if __name__ == "__main__":
    main()
