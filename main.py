import logging
import os

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from zoneinfo import ZoneInfo


from config import (
    BRANDS_CONFIG,
    REPORT_TIMEZONE,
    DRY_RUN,
)


from shopify_client import (
    ShopifyClient,
    ShopifyAPIError,
)


from sales_report import (
    calculate_sales_metrics,
)


from email_service import (
    send_report_email,
)


from report_state import (
    ReportState,
)


# ============================================================
# LOGGING
# ============================================================

LOG_DIRECTORY = "logs"


os.makedirs(
    LOG_DIRECTORY,
    exist_ok=True
)


logging.basicConfig(

    level=logging.INFO,

    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),

    handlers=[

        logging.FileHandler(
            os.path.join(
                LOG_DIRECTORY,
                "sales_report.log"
            ),
            encoding="utf-8"
        ),

        logging.StreamHandler(),
    ],
)


logger = logging.getLogger(
    __name__
)


# ============================================================
# TIMEZONE
# ============================================================

try:

    REPORT_TZ = ZoneInfo(
        REPORT_TIMEZONE
    )

except Exception as exc:

    raise RuntimeError(
        f"Invalid REPORT_TIMEZONE "
        f"'{REPORT_TIMEZONE}': {exc}"
    )


# ============================================================
# TIME HELPERS
# ============================================================

def utc_now() -> datetime:
    """
    Return the current UTC datetime.
    """

    return datetime.now(
        timezone.utc
    )


# ============================================================

def parse_timestamp(
    timestamp: str
) -> datetime:
    """
    Convert an ISO timestamp into an aware datetime.
    """

    parsed = datetime.fromisoformat(
        timestamp
    )


    if parsed.tzinfo is None:

        parsed = parsed.replace(
            tzinfo=timezone.utc
        )


    return parsed


# ============================================================

def get_initial_start_time() -> datetime:
    """
    Determines the reporting period for the very first run.

    If no previous successful checkpoint exists,
    use the previous one hour.
    """

    return (
        utc_now()
        - timedelta(
            hours=1
        )
    )


# ============================================================

def format_display_time(
    dt: datetime
) -> str:
    """
    Convert UTC datetime into the configured
    reporting timezone.
    """

    local_dt = (
        dt.astimezone(
            REPORT_TZ
        )
    )


    return local_dt.strftime(
        "%d %b %Y, %I:%M %p"
    )


# ============================================================
# TERMINAL REPORT
# ============================================================

def print_dry_run_report(
    brand_label: str,
    metrics: dict,
    start_display: str,
    end_display: str,
    recipient_email: str,
    cc_emails: list[str] | None = None,
):
    """
    Print the generated report to the terminal
    during dry-run mode.
    """

    separator = "=" * 60


    print()
    print(separator)

    print(
        f"{brand_label.upper()} SALES REPORT - DRY RUN"
    )

    print(separator)


    print(
        f"Reporting Period : "
        f"{start_display} -> {end_display}"
    )


    print(
        f"Recipient        : "
        f"{recipient_email}"
    )


    if cc_emails:

        print(
            f"CC               : "
            f"{', '.join(cc_emails)}"
        )


    print()


    print("ORDER SUMMARY")

    print("-" * 60)


    print(
        f"Total Orders     : "
        f"{metrics['total_orders']}"
    )


    print(
        f"Items Sold       : "
        f"{metrics['total_items']}"
    )


    print(
        f"Paid Orders      : "
        f"{metrics['paid_orders_count']}"
    )


    print(
        f"Cancelled Orders : "
        f"{metrics['cancelled_orders_count']}"
    )


    print()


    print("SALES")

    print("-" * 60)


    print(
        f"Gross Sales      : "
        f"₹{float(metrics['total_sales']):,.2f}"
    )


    print(
        f"Discounts        : "
        f"₹{float(metrics['total_discounts']):,.2f}"
    )


    print(
        f"Refunds          : "
        f"₹{float(metrics['refunded_amount']):,.2f}"
    )


    print(
        f"Net Sales        : "
        f"₹{float(metrics['net_sales']):,.2f}"
    )


    print()


    print("PAYMENT SUMMARY")

    print("-" * 60)


    print(
        f"COD Orders       : "
        f"{metrics['cod_orders_count']}"
    )


    print(
        f"COD Sales        : "
        f"₹{float(metrics['cod_sales']):,.2f}"
    )


    print(
        f"Paid Sales       : "
        f"₹{float(metrics['paid_sales']):,.2f}"
    )


    print()

    print(separator)

    print(
        "DRY RUN: EMAIL WAS NOT SENT"
    )

    print(separator)

    print()


# ============================================================
# BRAND REPORT
# ============================================================

def run_brand_report(
    brand_key: str,
    brand_config: dict,
    state: ReportState,
) -> bool:

    label = brand_config.get(
        "label",
        brand_key
    )


    shop_name = brand_config.get(
        "shop_name"
    )


    client_id = brand_config.get(
        "client_id"
    )


    client_secret = brand_config.get(
        "client_secret"
    )


    recipient_email = brand_config.get(
        "recipient_email"
    )


    cc_emails = brand_config.get(
        "cc_emails",
        []
    )


    api_version = brand_config.get(
        "api_version"
    )


    # ========================================================
    # CONFIGURATION VALIDATION
    # ========================================================

    missing = []


    if not shop_name:

        missing.append(
            "shop_name"
        )


    if not client_id:

        missing.append(
            "client_id"
        )


    if not client_secret:

        missing.append(
            "client_secret"
        )


    if not recipient_email:

        missing.append(
            "recipient_email"
        )


    if missing:

        logger.error(
            "%s: Missing configuration: %s",
            label,
            ", ".join(missing)
        )

        return False


    # ========================================================
    # REPORT PERIOD
    # ========================================================

    last_successful_run = (
        state.get_last_successful_run(
            brand_key
        )
    )


    if last_successful_run:

        try:

            start_time = parse_timestamp(
                last_successful_run
            )


            logger.info(
                "%s: Last successful report: %s",
                label,
                format_display_time(
                    start_time
                )
            )


        except Exception as exc:

            logger.error(
                "%s: Invalid stored timestamp '%s': %s",
                label,
                last_successful_run,
                exc
            )


            start_time = (
                get_initial_start_time()
            )


    else:

        start_time = (
            get_initial_start_time()
        )


        logger.info(
            "%s: No previous successful report found. "
            "Using previous 1 hour.",
            label
        )


    # ========================================================
    # CURRENT END TIME
    # ========================================================

    end_time = utc_now()


    # ========================================================
    # PERIOD VALIDATION
    # ========================================================

    if start_time >= end_time:

        logger.warning(
            "%s: Invalid reporting period. "
            "Start=%s End=%s",
            label,
            start_time,
            end_time,
        )

        return False


    # ========================================================
    # API TIMESTAMPS
    # ========================================================

    start_iso = (
        start_time.isoformat()
    )


    end_iso = (
        end_time.isoformat()
    )


    # ========================================================
    # DISPLAY TIMESTAMPS
    # ========================================================

    start_display = (
        format_display_time(
            start_time
        )
    )


    end_display = (
        format_display_time(
            end_time
        )
    )


    logger.info(
        "%s: Reporting period: "
        "%s -> %s",
        label,
        start_display,
        end_display,
    )


    # ========================================================
    # CREATE SHOPIFY CLIENT
    # ========================================================

    client = ShopifyClient(

        shop_name=shop_name,

        client_id=client_id,

        client_secret=client_secret,

        api_version=api_version,
    )


    # ========================================================
    # FETCH ORDERS
    # ========================================================

    try:

        logger.info(
            "%s: Fetching Shopify orders...",
            label
        )


        orders = client.get_orders(

            start_iso=start_iso,

            end_iso=end_iso,
        )


        logger.info(
            "%s: Shopify returned %s orders.",
            label,
            len(orders)
        )


    except ShopifyAPIError as exc:

        logger.error(
            "%s: Shopify API error: %s",
            label,
            exc
        )


        return False


    except Exception as exc:

        logger.exception(
            "%s: Unexpected Shopify error: %s",
            label,
            exc
        )


        return False


    # ========================================================
    # CALCULATE METRICS
    # ========================================================

    try:

        metrics = (
            calculate_sales_metrics(
                orders
            )
        )


    except Exception as exc:

        logger.exception(
            "%s: Failed calculating sales metrics: %s",
            label,
            exc
        )


        return False


    # ========================================================
    # LOG SUMMARY
    # ========================================================

    logger.info(
        "%s: Orders=%s | "
        "Items=%s | "
        "Gross Sales=₹%.2f | "
        "Net Sales=₹%.2f | "
        "COD Orders=%s | "
        "COD Sales=₹%.2f",

        label,

        metrics[
            "total_orders"
        ],

        metrics[
            "total_items"
        ],

        float(
            metrics[
                "total_sales"
            ]
        ),

        float(
            metrics[
                "net_sales"
            ]
        ),

        metrics[
            "cod_orders_count"
        ],

        float(
            metrics[
                "cod_sales"
            ]
        ),
    )


    # ========================================================
    # DRY RUN
    # ========================================================

    if DRY_RUN:

        logger.info(
            "%s: DRY_RUN=true",
            label
        )


        logger.info(
            "%s: Email sending is disabled.",
            label
        )


        print_dry_run_report(

            brand_label=label,

            metrics=metrics,

            start_display=start_display,

            end_display=end_display,

            recipient_email=recipient_email,

            cc_emails=cc_emails,
        )


        # IMPORTANT:
        #
        # We intentionally do NOT update the state
        # during dry-run mode.
        #
        # This allows us to repeatedly test the same
        # reporting period.


        logger.info(
            "%s: Dry run completed. "
            "Report state was NOT updated.",
            label
        )


        return True


    # ========================================================
    # REAL EMAIL
    # ========================================================

    try:

        logger.info(
            "%s: Sending report email to %s...",
            label,
            recipient_email
        )


        send_report_email(

            recipient_email=(
                recipient_email
            ),

            brand_label=(
                label
            ),

            metrics=(
                metrics
            ),

            start_display=(
                start_display
            ),

            end_display=(
                end_display
            ),
        )


    except Exception as exc:

        logger.exception(
            "%s: Email sending failed: %s",
            label,
            exc
        )


        # IMPORTANT:
        #
        # Do not update the checkpoint.
        #
        # The next run will retry the same reporting period.


        return False


    # ========================================================
    # SAVE SUCCESSFUL BRAND CHECKPOINT
    # ========================================================

    try:

        state.set_last_successful_run(

            brand_key,

            end_time.isoformat()
        )


        logger.info(
            "%s: Successful checkpoint updated to %s.",
            label,
            end_time.isoformat()
        )


    except Exception as exc:

        logger.exception(
            "%s: Failed to update report state: %s",
            label,
            exc
        )


        return False


    # ========================================================
    # SUCCESS
    # ========================================================

    logger.info(
        "%s: Report completed successfully.",
        label
    )


    return True


# ============================================================
# RUN COMPLETE REPORT CYCLE
# ============================================================

def run_sales_reporter():

    logger.info(
        "=================================================="
    )


    logger.info(
        "SHOPIFY AUTOMATED SALES REPORT"
    )


    logger.info(
        "=================================================="
    )


    logger.info(
        "Dry Run: %s",
        "ENABLED" if DRY_RUN else "DISABLED"
    )


    logger.info(
        "Reporting Timezone: %s",
        REPORT_TIMEZONE
    )


    logger.info(
        "=================================================="
    )


    # ========================================================
    # REPORT STATE
    # ========================================================

    state = ReportState()


    # ========================================================
    # PROCESS BRANDS
    # ========================================================

    total_brands = len(
        BRANDS_CONFIG
    )


    successful_brands = 0

    failed_brands = 0


    for (
        brand_key,
        brand_config
    ) in BRANDS_CONFIG.items():

        label = brand_config.get(
            "label",
            brand_key
        )


        logger.info(
            ""
        )


        logger.info(
            "--------------------------------------------------"
        )


        logger.info(
            "Processing: %s",
            label
        )


        logger.info(
            "--------------------------------------------------"
        )


        try:

            success = run_brand_report(

                brand_key=brand_key,

                brand_config=brand_config,

                state=state,
            )


            if success:

                successful_brands += 1


                logger.info(
                    "%s: SUCCESS",
                    label
                )


            else:

                failed_brands += 1


                logger.warning(
                    "%s: FAILED",
                    label
                )


        except Exception:

            failed_brands += 1


            logger.exception(
                "%s: Unexpected error.",
                label
            )


    # ========================================================
    # PERSIST STATE
    # ========================================================
    #
    # Only save state when NOT in dry-run mode.
    #
    # In real mode:
    #
    #     successful brand -> checkpoint updated
    #
    #     failed brand     -> checkpoint unchanged
    #
    # ========================================================

    if not DRY_RUN:

        try:

            state.save()


            logger.info(
                "Report state persisted successfully."
            )


        except Exception as exc:

            logger.exception(
                "Failed to persist report state: %s",
                exc
            )


            # If state cannot be persisted, the next run
            # may repeat successful reports.
            #
            # We intentionally report this as an error.


            failed_brands += 1


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    logger.info(
        ""
    )


    logger.info(
        "=================================================="
    )


    logger.info(
        "REPORT CYCLE COMPLETED"
    )


    logger.info(
        "=================================================="
    )


    logger.info(
        "Total Brands : %s",
        total_brands
    )


    logger.info(
        "Successful   : %s",
        successful_brands
    )


    logger.info(
        "Failed       : %s",
        failed_brands
    )


    logger.info(
        "Dry Run      : %s",
        "YES" if DRY_RUN else "NO"
    )


    logger.info(
        "=================================================="
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_sales_reporter()