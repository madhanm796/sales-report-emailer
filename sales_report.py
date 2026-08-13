from decimal import Decimal


# ============================================================
# COD GATEWAYS
# ============================================================

COD_GATEWAYS = {
    "manual",
    "cash",
    "cash on delivery",
    "cash_on_delivery",
    "cod",
    "cash on delivery (cod)",
}


# ============================================================
# HELPERS
# ============================================================

def money(value) -> Decimal:
    """
    Safely convert a value into Decimal.
    """

    try:

        return Decimal(
            str(value or "0")
        )

    except Exception:

        return Decimal("0")


def get_payment_gateways(
    order: dict
) -> list:

    gateways = (
        order.get(
            "payment_gateway_names"
        )
        or []
    )

    return [
        str(gateway)
        .strip()
        .lower()

        for gateway in gateways
    ]


def is_cod_order(
    order: dict
) -> bool:
    """
    Determine whether an order is COD.
    """

    gateways = get_payment_gateways(
        order
    )

    legacy_gateway = str(
        order.get(
            "gateway"
        )
        or ""
    ).strip().lower()

    # Explicit COD gateway names
    if any(
        gateway in COD_GATEWAYS
        for gateway in gateways
    ):
        return True

    # Shopify manual payment gateway
    if legacy_gateway == "manual":
        return True

    return False


# ============================================================
# MAIN CALCULATION
# ============================================================

def calculate_sales_metrics(
    orders: list
) -> dict:

    total_orders = len(
        orders
    )

    total_items = 0

    total_sales = Decimal("0")

    total_discounts = Decimal("0")

    total_shipping = Decimal("0")

    total_tax = Decimal("0")

    refunded_amount = Decimal("0")

    net_sales = Decimal("0")

    # --------------------------------------------------------
    # COD
    # --------------------------------------------------------

    cod_orders_count = 0

    cod_sales = Decimal("0")

    # --------------------------------------------------------
    # Paid
    # --------------------------------------------------------

    paid_orders_count = 0

    paid_sales = Decimal("0")

    # --------------------------------------------------------
    # Cancelled
    # --------------------------------------------------------

    cancelled_orders_count = 0

    cancelled_sales = Decimal("0")

    # ========================================================
    # PROCESS ORDERS
    # ========================================================

    for order in orders:

        total_price = money(
            order.get(
                "total_price"
            )
        )

        # ----------------------------------------------------
        # Items
        # ----------------------------------------------------

        for line_item in (
            order.get(
                "line_items",
                []
            )
        ):

            try:

                total_items += int(
                    line_item.get(
                        "quantity",
                        0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                pass

        # ----------------------------------------------------
        # Discounts
        # ----------------------------------------------------

        total_discounts += money(
            order.get(
                "total_discounts"
            )
        )

        # ----------------------------------------------------
        # Shipping
        # ----------------------------------------------------

        shipping_data = (
            order.get(
                "total_shipping_price_set",
                {}
            )
        )

        shop_money = (
            shipping_data.get(
                "shop_money",
                {}
            )
        )

        total_shipping += money(
            shop_money.get(
                "amount"
            )
        )

        # ----------------------------------------------------
        # Tax
        # ----------------------------------------------------

        total_tax += money(
            order.get(
                "total_tax"
            )
        )

        # ----------------------------------------------------
        # Gross sales
        # ----------------------------------------------------

        total_sales += total_price

        # ----------------------------------------------------
        # Cancelled
        # ----------------------------------------------------

        if order.get(
            "cancelled_at"
        ):

            cancelled_orders_count += 1

            cancelled_sales += (
                total_price
            )

        # ----------------------------------------------------
        # COD
        # ----------------------------------------------------

        if is_cod_order(
            order
        ):

            cod_orders_count += 1

            cod_sales += total_price

        # ----------------------------------------------------
        # Paid
        # ----------------------------------------------------

        financial_status = str(
            order.get(
                "financial_status"
            )
            or ""
        ).lower()

        if financial_status in {
            "paid",
            "partially_paid"
        }:

            paid_orders_count += 1

            paid_sales += total_price

        # ----------------------------------------------------
        # Refunds
        # ----------------------------------------------------

        for refund in (
            order.get(
                "refunds",
                []
            )
        ):

            for transaction in (
                refund.get(
                    "transactions",
                    []
                )
            ):

                if (
                    transaction.get(
                        "kind"
                    )
                    != "refund"
                ):
                    continue

                refunded_amount += money(
                    transaction.get(
                        "amount"
                    )
                )

    # ========================================================
    # NET SALES
    # ========================================================

    net_sales = (
        total_sales
        - refunded_amount
    )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "total_orders":
            total_orders,

        "total_items":
            total_items,

        "total_sales":
            total_sales,

        "total_discounts":
            total_discounts,

        "total_shipping":
            total_shipping,

        "total_tax":
            total_tax,

        "refunded_amount":
            refunded_amount,

        "net_sales":
            net_sales,

        "cod_orders_count":
            cod_orders_count,

        "cod_sales":
            cod_sales,

        "paid_orders_count":
            paid_orders_count,

        "paid_sales":
            paid_sales,

        "cancelled_orders_count":
            cancelled_orders_count,

        "cancelled_sales":
            cancelled_sales,
    }