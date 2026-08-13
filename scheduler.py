import logging
import time

from config import (
    REPORT_INTERVAL_HOURS
)

from main import (
    run_sales_reporter
)


logger = logging.getLogger(
    __name__
)


def run_scheduler():

    interval_seconds = (
        REPORT_INTERVAL_HOURS
        * 60
        * 60
    )


    logger.info(
        "=========================================="
    )

    logger.info(
        "Automated Sales Report Scheduler"
    )

    logger.info(
        "Interval: %.2f hours",
        REPORT_INTERVAL_HOURS
    )

    logger.info(
        "=========================================="
    )


    while True:

        try:

            run_sales_reporter()

        except Exception:

            logger.exception(
                "Unexpected scheduler error."
            )


        logger.info(
            "Next report will run in %.2f hours.",
            REPORT_INTERVAL_HOURS
        )


        try:

            time.sleep(
                interval_seconds
            )

        except KeyboardInterrupt:

            logger.info(
                "Scheduler stopped by user."
            )

            break


if __name__ == "__main__":

    run_scheduler()