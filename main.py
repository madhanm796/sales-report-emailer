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


# ============================================================
# LOGGING
# ============================================================

BASE_DIRECTORY = os.path.dirname(
    os.path.abspath(__file__)
)


LOG_DIRECTORY = os.path.join(
    BASE_DIRECTORY,
    "logs"
)


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
        f"'{REPORT_TIMEZONE}'. "
        f"Install tzdata with: "
        f"pip install tzdata. "
        f"Original error: {exc}"
    )


# ============================================================
# TIME HELPERS
# ============================================================

def utc_now() -> datetime:
    """
    Return current UTC time.
    """

    return datetime.now(
        timezone.utc
    )


def get_previous_hour_period():
    """
    Return the previous one-hour reporting period.

    Example:

        Current time:
            13:25

        Reporting period:
            12:25 -> 13:25
    """

    end_time = utc_now()

    start_time = (
        end_time
        - timedelta(
            hours=1
        )
    )

    return (
        start_time,
        end_time
    )


def format_display_time(
    dt: datetime
) -> str:
    """
    Convert UTC datetime into the configured
    local reporting timezone.
    """

    local_dt = (
        dt.astimezone(
            REPORT_TZ
        )
    )

    return local_dt.strftime(
        "%d %b %Y, %I:%M:%S %p"
    )


# ============================================================
# DRY RUN REPORT
# ============================================================

def print_dry_run_report(
    brand_label: str,
    metrics: dict,
    start_display: str,
    end_display: str,
    recipient_email: str,
    cc_emails: list[str],
):

    separator = "=" * 65

    print()
    print(separator)

    print(
        f"{brand_label.upper()} "
        f"HOURLY SALES REPORT - DRY RUN"
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

    print(
        f"CC               : "
        f"{', '.join(cc_emails) if cc_emails else 'None'}"
    )

    print()

    # ========================================================
    # ORDER SUMMARY
    # ========================================================

    print("ORDER SUMMARY")
    print("-" * 65)

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

    # ========================================================
    # SALES
    # ========================================================

    print("SALES")
    print("-" * 65)

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

    # ========================================================
    # PAYMENT SUMMARY
    # ========================================================

    print("PAYMENT SUMMARY")
    print("-" * 65)

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
# VALIDATE BRAND CONFIGURATION
# ============================================================

def validate_brand_config(
    brand_key: str,
    brand_config: dict
) -> list[str]:
    """
    Return a list of missing configuration values.
    """

    missing = []

    if not brand_config.get(
        "shop_name"
    ):

        missing.append(
            "shop_name"
        )

    if not brand_config.get(
        "client_id"
    ):

        missing.append(
            "client_id"
        )

    if not brand_config.get(
        "client_secret"
    ):

        missing.append(
            "client_secret"
        )

    if not brand_config.get(
        "recipient_email"
    ):

        missing.append(
            "recipient_email"
        )

    return missing


# ============================================================
# PROCESS ONE BRAND
# ============================================================

def run_brand_report(
    brand_key: str,
    brand_config: dict,
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

    missing = validate_brand_config(
        brand_key,
        brand_config
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

    start_time, end_time = (
        get_previous_hour_period()
    )


    start_iso = (
        start_time.isoformat()
    )

    end_iso = (
        end_time.isoformat()
    )


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
        end_display
    )


    # ========================================================
    # SHOPIFY CLIENT
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
            "%s: Retrieved %d orders.",
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

        "%s: "
        "Orders=%s | "
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


        return True


    # ========================================================
    # SEND EMAIL
    # ========================================================

    try:

        logger.info(
            "%s: Sending hourly report.",
            label
        )

        logger.info(
            "%s: TO=%s",
            label,
            recipient_email
        )

        if cc_emails:

            logger.info(
                "%s: CC=%s",
                label,
                ", ".join(
                    cc_emails
                )
            )


        send_report_email(

            recipient_email=(
                recipient_email
            ),

            cc_emails=(
                cc_emails
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

        return False


    logger.info(
        "%s: Hourly report sent successfully.",
        label
    )


    return True


# ============================================================
# RUN COMPLETE REPORT CYCLE
# ============================================================

def run_sales_reporter():

    logger.info(
        ""
    )

    logger.info(
        "=================================================="
    )

    logger.info(
        "SHOPIFY HOURLY SALES REPORT"
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


    total_brands = len(
        BRANDS_CONFIG
    )

    successful_brands = 0

    failed_brands = 0


    # ========================================================
    # PROCESS ALL BRANDS
    # ========================================================

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
    # FINAL SUMMARY
    # ========================================================

    logger.info(
        ""
    )

    logger.info(
        "=================================================="
    )

    logger.info(
        "HOURLY REPORT CYCLE COMPLETED"
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