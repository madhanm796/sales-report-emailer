import os
import sys

from dotenv import load_dotenv


# ============================================================
# APPLICATION DIRECTORY
# ============================================================

def get_application_directory() -> str:
    """
    Return the directory containing the application.
    """

    if getattr(sys, "frozen", False):

        return os.path.dirname(
            os.path.abspath(
                sys.executable
            )
        )

    return os.path.dirname(
        os.path.abspath(
            __file__
        )
    )


# ============================================================
# LOAD LOCAL .ENV
# ============================================================

def load_environment():
    """
    Load .env for local development.

    GitHub Actions does not require .env.
    GitHub Secrets are exposed as environment variables.
    """

    application_directory = (
        get_application_directory()
    )

    env_path = os.path.join(
        application_directory,
        ".env"
    )

    if os.path.exists(env_path):

        load_dotenv(
            dotenv_path=env_path
        )


load_environment()


# ============================================================
# SHOPIFY
# ============================================================

SHOPIFY_API_VERSION = os.getenv(
    "SHOPIFY_API_VERSION",
    "2026-07"
)


# ============================================================
# REPORT CONFIGURATION
# ============================================================

REPORT_TIMEZONE = os.getenv(
    "REPORT_TIMEZONE",
    "Asia/Kolkata"
)


REPORT_INTERVAL_HOURS = float(
    os.getenv(
        "REPORT_INTERVAL_HOURS",
        "1"
    )
)


# ============================================================
# DRY RUN
# ============================================================

DRY_RUN = (
    os.getenv(
        "DRY_RUN",
        "true"
    )
    .strip()
    .lower()
    in {
        "true",
        "1",
        "yes",
        "y",
    }
)


# ============================================================
# SMTP
# ============================================================

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com"
)


SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "465"
    )
)


SMTP_SENDER_EMAIL = os.getenv(
    "SMTP_SENDER_EMAIL"
)


SMTP_APP_PASSWORD = os.getenv(
    "SMTP_APP_PASSWORD"
)


# ============================================================
# EMAIL LIST PARSER
# ============================================================

def parse_email_list(
    value: str | None
) -> list[str]:
    """
    Convert comma-separated email addresses into a list.

    Example:

        a@example.com,b@example.com

    becomes:

        [
            "a@example.com",
            "b@example.com"
        ]
    """

    if not value:

        return []

    return [
        email.strip()

        for email in value.split(",")

        if email.strip()
    ]


# ============================================================
# BRAND CONFIGURATION
# ============================================================

BRANDS_CONFIG = {

    # ========================================================
    # BAYBEE
    # ========================================================

    "baybee": {

        "label": os.getenv(
            "BAYBEE_LABEL",
            "Baybee"
        ),

        "shop_name": os.getenv(
            "BAYBEE_SHOP_NAME"
        ),

        "client_id": os.getenv(
            "BAYBEE_CLIENT_ID"
        ),

        "client_secret": os.getenv(
            "BAYBEE_CLIENT_SECRET"
        ),

        "recipient_email": os.getenv(
            "BAYBEE_RECIPIENT_EMAIL"
        ),

        "cc_emails": parse_email_list(
            os.getenv(
                "BAYBEE_CC_EMAILS"
            )
        ),

        "api_version": SHOPIFY_API_VERSION,
    },


    # ========================================================
    # DROGO
    # ========================================================

    "drogo": {

        "label": os.getenv(
            "DROGO_LABEL",
            "Drogo"
        ),

        "shop_name": os.getenv(
            "DROGO_SHOP_NAME"
        ),

        "client_id": os.getenv(
            "DROGO_CLIENT_ID"
        ),

        "client_secret": os.getenv(
            "DROGO_CLIENT_SECRET"
        ),

        "recipient_email": os.getenv(
            "DROGO_RECIPIENT_EMAIL"
        ),

        "cc_emails": parse_email_list(
            os.getenv(
                "DROGO_CC_EMAILS"
            )
        ),

        "api_version": SHOPIFY_API_VERSION,
    },


    # ========================================================
    # DOMESTICA
    # ========================================================

    "domestica": {

        "label": os.getenv(
            "DOMESTICA_LABEL",
            "Domestica"
        ),

        "shop_name": os.getenv(
            "DOMESTICA_SHOP_NAME"
        ),

        "client_id": os.getenv(
            "DOMESTICA_CLIENT_ID"
        ),

        "client_secret": os.getenv(
            "DOMESTICA_CLIENT_SECRET"
        ),

        "recipient_email": os.getenv(
            "DOMESTICA_RECIPIENT_EMAIL"
        ),

        "cc_emails": parse_email_list(
            os.getenv(
                "DOMESTICA_CC_EMAILS"
            )
        ),

        "api_version": SHOPIFY_API_VERSION,
    },
}