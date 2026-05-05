from worker_app.consumers.runner import run_consumer
from worker_app.services.notification_service import CONSUMER_NAME, process_notification_event


def main() -> None:
    run_consumer(
        queue_name="q.notification.events",
        consumer_name=CONSUMER_NAME,
        expected_event_types={
            "payment.approved",
            "payment.rejected",
            "stock.failed",
            "order.ready_to_ship",
        },
        required_data_fields={"order_id"},
        processor=process_notification_event,
    )


if __name__ == "__main__":
    main()
