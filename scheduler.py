import logging
import time

from config import (
    REPORT_INTERVAL_HOURS,
)

from main import (
    run_sales_reporter,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(

    level=logging.INFO,

    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)


logger = logging.getLogger(
    __name__
)


# ============================================================
# SCHEDULER
# ============================================================

def run_scheduler():

    interval_seconds = (
        REPORT_INTERVAL_HOURS
        * 60
        * 60
    )


    logger.info(
        "=================================================="
    )

    logger.info(
        "AUTOMATED SALES REPORT SCHEDULER"
    )

    logger.info(
        "=================================================="
    )

    logger.info(
        "Interval: %.2f hour(s)",
        REPORT_INTERVAL_HOURS
    )

    logger.info(
        "=================================================="
    )


    while True:

        # ----------------------------------------------------
        # RUN REPORT
        # ----------------------------------------------------

        try:

            run_sales_reporter()

        except Exception:

            logger.exception(
                "Unexpected error during report cycle."
            )


        # ----------------------------------------------------
        # WAIT
        # ----------------------------------------------------

        logger.info(
            "Next report will run in %.2f hour(s).",
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


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_scheduler()