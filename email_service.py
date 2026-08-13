import logging
import smtplib

from email.mime.multipart import (
    MIMEMultipart
)

from email.mime.text import (
    MIMEText
)


from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_SENDER_EMAIL,
    SMTP_APP_PASSWORD,
)


logger = logging.getLogger(
    __name__
)


# ============================================================
# CURRENCY
# ============================================================

def format_currency(
    value
) -> str:

    return (
        f"₹{float(value):,.2f}"
    )


# ============================================================
# HTML REPORT
# ============================================================

def generate_html_report(
    brand_label: str,
    metrics: dict,
    start_display: str,
    end_display: str,
) -> str:

    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<style>

body {{
    margin: 0;
    padding: 0;

    background: #f3f4f6;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #111827;
}}

.wrapper {{
    width: 100%;
    padding: 30px 0;
}}

.container {{
    width: 700px;
    max-width: 92%;

    margin: 0 auto;

    background: #ffffff;

    border: 1px solid #e5e7eb;

    border-radius: 12px;

    overflow: hidden;
}}

.header {{
    background: #111827;

    padding: 28px 30px;

    color: #ffffff;
}}

.header h1 {{
    margin: 0;

    font-size: 24px;

    font-weight: 700;
}}

.header p {{
    margin: 8px 0 0;

    font-size: 13px;

    color: #d1d5db;
}}

.content {{
    padding: 30px;
}}

.section {{
    margin-bottom: 30px;
}}

.section-title {{
    margin: 0 0 12px;

    font-size: 15px;

    font-weight: 700;

    color: #111827;
}}

.metrics {{
    width: 100%;

    border-collapse: collapse;
}}

.metrics td {{
    padding: 12px 10px;

    border-bottom:
        1px solid #eeeeee;

    font-size: 14px;
}}

.metric-name {{
    color: #6b7280;
}}

.metric-value {{
    text-align: right;

    font-weight: 700;

    color: #111827;
}}

.highlight td {{
    background: #f9fafb;
}}

.highlight .metric-value {{
    font-size: 16px;
}}

.footer {{
    padding: 18px 30px;

    background: #f9fafb;

    text-align: center;

    font-size: 12px;

    color: #9ca3af;
}}

@media only screen and (max-width: 600px) {{

    .content {{
        padding: 20px;
    }}

    .header {{
        padding: 22px;
    }}

}}

</style>

</head>

<body>

<div class="wrapper">

<div class="container">

    <div class="header">

        <h1>
            {brand_label} — Hourly Sales Report
        </h1>

        <p>
            {start_display}
            →
            {end_display}
        </p>

    </div>


    <div class="content">


        <!-- ORDER SUMMARY -->

        <div class="section">

            <div class="section-title">
                Order Summary
            </div>

            <table class="metrics">

                <tr>

                    <td class="metric-name">
                        Total Orders
                    </td>

                    <td class="metric-value">
                        {metrics["total_orders"]}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        Items Sold
                    </td>

                    <td class="metric-value">
                        {metrics["total_items"]}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        Paid Orders
                    </td>

                    <td class="metric-value">
                        {metrics["paid_orders_count"]}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        Cancelled Orders
                    </td>

                    <td class="metric-value">
                        {metrics["cancelled_orders_count"]}
                    </td>

                </tr>

            </table>

        </div>


        <!-- SALES -->

        <div class="section">

            <div class="section-title">
                Sales
            </div>

            <table class="metrics">

                <tr class="highlight">

                    <td class="metric-name">
                        Gross Sales
                    </td>

                    <td class="metric-value">
                        {format_currency(
                            metrics["total_sales"]
                        )}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        Discounts
                    </td>

                    <td class="metric-value">
                        {format_currency(
                            metrics["total_discounts"]
                        )}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        Refunds
                    </td>

                    <td class="metric-value">
                        {format_currency(
                            metrics["refunded_amount"]
                        )}
                    </td>

                </tr>


                <tr class="highlight">

                    <td class="metric-name">
                        Net Sales
                    </td>

                    <td class="metric-value">
                        {format_currency(
                            metrics["net_sales"]
                        )}
                    </td>

                </tr>

            </table>

        </div>


        <!-- PAYMENT -->

        <div class="section">

            <div class="section-title">
                Payment Summary
            </div>

            <table class="metrics">

                <tr>

                    <td class="metric-name">
                        COD Orders
                    </td>

                    <td class="metric-value">
                        {metrics["cod_orders_count"]}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        COD Sales
                    </td>

                    <td class="metric-value">
                        {format_currency(
                            metrics["cod_sales"]
                        )}
                    </td>

                </tr>


                <tr>

                    <td class="metric-name">
                        Paid Sales
                    </td>

                    <td class="metric-value">
                        {format_currency(
                            metrics["paid_sales"]
                        )}
                    </td>

                </tr>

            </table>

        </div>


    </div>


    <div class="footer">

        Automated Shopify Sales Report

    </div>

</div>

</div>

</body>

</html>
"""


# ============================================================
# SEND EMAIL
# ============================================================

def send_report_email(
    recipient_email: str,
    cc_emails: list[str],
    brand_label: str,
    metrics: dict,
    start_display: str,
    end_display: str,
):

    subject = (
        f"[{brand_label}] "
        f"Hourly Sales Report | "
        f"{start_display} - {end_display}"
    )


    html_body = (
        generate_html_report(

            brand_label=brand_label,

            metrics=metrics,

            start_display=start_display,

            end_display=end_display,
        )
    )


    message = MIMEMultipart(
        "alternative"
    )


    message["Subject"] = (
        subject
    )


    message["From"] = (
        SMTP_SENDER_EMAIL
    )


    message["To"] = (
        recipient_email
    )


    if cc_emails:

        message["Cc"] = (
            ", ".join(
                cc_emails
            )
        )


    message.attach(

        MIMEText(

            html_body,

            "html",

            "utf-8"
        )
    )


    if not SMTP_SENDER_EMAIL:

        raise RuntimeError(
            "SMTP_SENDER_EMAIL "
            "is not configured."
        )


    if not SMTP_APP_PASSWORD:

        raise RuntimeError(
            "SMTP_APP_PASSWORD "
            "is not configured."
        )


    # ========================================================
    # RECIPIENT LIST
    # ========================================================

    all_recipients = [

        recipient_email,

        *cc_emails,
    ]


    logger.info(
        "Sending email to %s recipient(s).",
        len(all_recipients)
    )


    # ========================================================
    # SMTP
    # ========================================================

    with smtplib.SMTP_SSL(

        SMTP_HOST,

        SMTP_PORT,

        timeout=30

    ) as server:

        server.login(

            SMTP_SENDER_EMAIL,

            SMTP_APP_PASSWORD
        )


        server.sendmail(

            SMTP_SENDER_EMAIL,

            all_recipients,

            message.as_string()
        )


    logger.info(
        "Email sent successfully."
    )