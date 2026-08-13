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
# MONEY
# ============================================================

def money(value) -> Decimal:

    try:

        return Decimal(
            str(
                value or "0"
            )
        )

    except Exception:

        return Decimal("0")


# ============================================================
# PAYMENT GATEWAYS
# ============================================================

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


# ============================================================
# COD DETECTION
# ============================================================

def is_cod_order(
    order: dict
) -> bool:

    gateways = (
        get_payment_gateways(
            order
        )
    )


    legacy_gateway = (
        str(
            order.get(
                "gateway"
            )
            or ""
        )
        .strip()
        .lower()
    )


    # Top-level gateway names

    for gateway in gateways:

        if gateway in COD_GATEWAYS:

            return True


        if (
            "cash on delivery"
            in gateway
        ):

            return True


    # Legacy gateway

    if (
        legacy_gateway
        in COD_GATEWAYS
    ):

        return True


    if (
        "cash on delivery"
        in legacy_gateway
    ):

        return True


    # Transaction gateway

    transactions = (
        order.get(
            "transactions"
        )
        or []
    )


    for transaction in transactions:

        gateway = (
            str(
                transaction.get(
                    "gateway"
                )
                or ""
            )
            .strip()
            .lower()
        )


        if gateway in COD_GATEWAYS:

            return True


        if (
            "cash on delivery"
            in gateway
        ):

            return True


    return False


# ============================================================
# SALES METRICS
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

    cod_orders_count = 0

    cod_sales = Decimal("0")

    paid_orders_count = 0

    paid_sales = Decimal("0")

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
        # ITEMS
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
        # DISCOUNTS
        # ----------------------------------------------------

        total_discounts += money(
            order.get(
                "total_discounts"
            )
        )


        # ----------------------------------------------------
        # SHIPPING
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
        # TAX
        # ----------------------------------------------------

        total_tax += money(
            order.get(
                "total_tax"
            )
        )


        # ----------------------------------------------------
        # SALES
        # ----------------------------------------------------

        total_sales += (
            total_price
        )


        # ----------------------------------------------------
        # CANCELLED
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

            cod_sales += (
                total_price
            )


        # ----------------------------------------------------
        # PAID
        # ----------------------------------------------------

        financial_status = str(
            order.get(
                "financial_status"
            )
            or ""
        ).lower()


        if financial_status in {

            "paid",

            "partially_paid",
        }:

            paid_orders_count += 1

            paid_sales += (
                total_price
            )


        # ----------------------------------------------------
        # REFUNDS
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
    # RETURN
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