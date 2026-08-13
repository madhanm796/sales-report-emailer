import os
import sys
from dotenv import load_dotenv


# ============================================================
# APPLICATION PATH
# ============================================================

def get_application_directory() -> str:
    """
    Returns the directory containing the Python script
    or the compiled executable.
    """

    if getattr(sys, "frozen", False):
        return os.path.dirname(
            os.path.abspath(sys.executable)
        )

    return os.path.dirname(
        os.path.abspath(__file__)
    )


# ============================================================
# ENVIRONMENT LOADING
# ============================================================

def load_environment():
    """
    Load the .env file from the application directory.
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

    else:

        print(
            f"WARNING: .env file not found at: {env_path}"
        )

        # Fallback to default dotenv behavior
        load_dotenv()


# Load .env when this module is imported
load_environment()


# ============================================================
# GLOBAL SHOPIFY CONFIGURATION
# ============================================================

SHOPIFY_API_VERSION = os.getenv(
    "SHOPIFY_API_VERSION",
    "2026-07"
)

REPORT_TIMEZONE = os.getenv(
    "REPORT_TIMEZONE",
    "Asia/Kolkata"
)

REPORT_INTERVAL_HOURS = float(
    os.getenv(
        "REPORT_INTERVAL_HOURS",
        "4"
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
# GMAIL SMTP CONFIGURATION
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
# SHOPIFY BRAND CONFIGURATION
# ============================================================

BRANDS_CONFIG = {

    # --------------------------------------------------------
    # BAYBEE
    # --------------------------------------------------------

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

        "api_version": SHOPIFY_API_VERSION,
    },


    # --------------------------------------------------------
    # DROGO
    # --------------------------------------------------------

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

        "api_version": SHOPIFY_API_VERSION,
    },


    # --------------------------------------------------------
    # DOMESTICA
    # --------------------------------------------------------

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

        "api_version": SHOPIFY_API_VERSION,
    },
}