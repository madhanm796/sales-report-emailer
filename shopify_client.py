import logging
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

import requests


logger = logging.getLogger(__name__)


class ShopifyAPIError(Exception):
    """
    Custom Shopify API exception.
    """
    pass


class ShopifyClient:

    TOKEN_REFRESH_BUFFER_SECONDS = 300

    def __init__(
        self,
        shop_name: str,
        client_id: str,
        client_secret: str,
        api_version: str = "2026-07"
    ):

        self.shop_name = shop_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_version = api_version

        self.store_base_url = (
            f"https://{self.shop_name}.myshopify.com"
        )

        self.api_base_url = (
            f"{self.store_base_url}"
            f"/admin/api/{self.api_version}"
        )

        self.token_url = (
            f"{self.store_base_url}"
            f"/admin/oauth/access_token"
        )

        self.session = requests.Session()

        self.access_token = None
        self.token_expires_at = None

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def get_access_token(self) -> str:
        """
        Returns a valid Admin API access token.

        If the current token is missing or expired,
        a new token is requested using the Client ID
        and Client Secret.
        """

        if self._token_is_valid():

            return self.access_token

        logger.info(
            "%s: Requesting new Shopify Admin API token...",
            self.shop_name
        )

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:

            response = requests.post(
                self.token_url,
                data=payload,
                headers={
                    "Content-Type":
                        "application/x-www-form-urlencoded",
                    "Accept":
                        "application/json",
                },
                timeout=30,
            )

        except requests.RequestException as exc:

            raise ShopifyAPIError(
                f"{self.shop_name}: "
                f"Unable to connect to Shopify token endpoint: "
                f"{exc}"
            ) from exc

        if response.status_code != 200:

            try:
                error_data = response.json()
            except ValueError:
                error_data = response.text

            raise ShopifyAPIError(
                f"{self.shop_name}: "
                f"Token request failed "
                f"(HTTP {response.status_code}): "
                f"{error_data}"
            )

        try:

            data = response.json()

        except ValueError as exc:

            raise ShopifyAPIError(
                f"{self.shop_name}: "
                f"Shopify returned invalid token JSON."
            ) from exc

        access_token = data.get(
            "access_token"
        )

        expires_in = int(
            data.get(
                "expires_in",
                86399
            )
        )

        if not access_token:

            raise ShopifyAPIError(
                f"{self.shop_name}: "
                f"Shopify did not return an access token."
            )

        self.access_token = access_token

        self.token_expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                seconds=expires_in
            )
        )

        logger.info(
            "%s: Shopify Admin API token obtained.",
            self.shop_name
        )

        logger.info(
            "%s: Token expires at %s",
            self.shop_name,
            self.token_expires_at.isoformat()
        )

        return self.access_token

    def _token_is_valid(self) -> bool:
        """
        Checks whether the current token is still valid.

        A 5-minute buffer is used so we don't start a request
        right before the token expires.
        """

        if not self.access_token:
            return False

        if not self.token_expires_at:
            return False

        refresh_time = (
            self.token_expires_at
            - timedelta(
                seconds=self.TOKEN_REFRESH_BUFFER_SECONDS
            )
        )

        return (
            datetime.now(timezone.utc)
            < refresh_time
        )

    # ========================================================
    # REQUEST
    # ========================================================

    def _get_headers(self) -> dict:

        access_token = (
            self.get_access_token()
        )

        return {
            "X-Shopify-Access-Token":
                access_token,

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",
        }

    def _get(
        self,
        url: str,
        params: dict | None = None
    ):

        max_retries = 3

        for attempt in range(
            1,
            max_retries + 1
        ):

            try:

                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30,
                )

            except requests.RequestException as exc:

                if attempt == max_retries:

                    raise ShopifyAPIError(
                        f"{self.shop_name}: "
                        f"Network error: {exc}"
                    ) from exc

                wait_seconds = attempt * 2

                logger.warning(
                    "%s: Network error. "
                    "Retrying in %s seconds...",
                    self.shop_name,
                    wait_seconds
                )

                time.sleep(
                    wait_seconds
                )

                continue

            # ------------------------------------------------
            # Rate limit
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After",
                    "2"
                )

                try:
                    retry_after = float(
                        retry_after
                    )
                except ValueError:
                    retry_after = 2

                logger.warning(
                    "%s: Shopify rate limit reached. "
                    "Waiting %.2f seconds...",
                    self.shop_name,
                    retry_after
                )

                time.sleep(
                    retry_after
                )

                continue

            # ------------------------------------------------
            # Unauthorized
            # ------------------------------------------------

            if response.status_code == 401:

                logger.warning(
                    "%s: Access token rejected. "
                    "Refreshing token...",
                    self.shop_name
                )

                self.access_token = None
                self.token_expires_at = None

                if attempt < max_retries:
                    continue

            # ------------------------------------------------
            # Other errors
            # ------------------------------------------------

            if not response.ok:

                try:
                    error_data = response.json()
                except ValueError:
                    error_data = response.text

                raise ShopifyAPIError(
                    f"{self.shop_name}: "
                    f"Shopify API request failed "
                    f"(HTTP {response.status_code}): "
                    f"{error_data}"
                )

            return response

        raise ShopifyAPIError(
            f"{self.shop_name}: "
            f"Shopify request failed after "
            f"{max_retries} attempts."
        )

    # ========================================================
    # ORDERS
    # ========================================================

    def get_orders(
        self,
        start_iso: str,
        end_iso: str
    ) -> list:
        """
        Fetch every Shopify order in the specified
        reporting period.

        Cursor pagination is automatically handled.
        """

        url = (
            f"{self.api_base_url}"
            f"/orders.json"
        )

        params = {

            "status": "any",

            "created_at_min":
                start_iso,

            "created_at_max":
                end_iso,

            "limit":
                250,

            "order":
                "created_at asc",
        }

        all_orders = []

        page_number = 1

        while url:

            logger.info(
                "%s: Fetching Shopify orders page %s...",
                self.shop_name,
                page_number
            )

            response = self._get(
                url=url,
                params=params
            )

            data = response.json()

            orders = data.get(
                "orders",
                []
            )

            all_orders.extend(
                orders
            )

            logger.info(
                "%s: Page %s returned %s orders.",
                self.shop_name,
                page_number,
                len(orders)
            )

            # ------------------------------------------------
            # Get next cursor URL
            # ------------------------------------------------

            next_url = (
                self._get_next_page_url(
                    response.headers.get(
                        "Link"
                    )
                )
            )

            if next_url:

                url = next_url

                # IMPORTANT:
                #
                # The page_info URL already contains the
                # pagination information. Shopify does not
                # allow us to append the original filtering
                # parameters to it.
                params = None

                page_number += 1

            else:

                url = None

        logger.info(
            "%s: Finished retrieving orders. "
            "Total = %s",
            self.shop_name,
            len(all_orders)
        )

        return all_orders

    # ========================================================
    # PAGINATION
    # ========================================================

    @staticmethod
    def _get_next_page_url(
        link_header: str | None
    ) -> str | None:
        """
        Extract rel="next" from Shopify Link header.
        """

        if not link_header:
            return None

        links = link_header.split(",")

        for link in links:

            parts = link.split(";")

            if len(parts) < 2:
                continue

            url_part = parts[0].strip()

            relation = (
                parts[1]
                .strip()
                .lower()
            )

            if relation == 'rel="next"':

                if (
                    url_part.startswith("<")
                    and
                    url_part.endswith(">")
                ):

                    return url_part[1:-1]

        return None

    # ========================================================
    # CONNECTION TEST
    # ========================================================

    def test_connection(self) -> bool:
        """
        Tests whether Client ID + Secret can obtain
        an Admin API token.
        """

        try:

            self.get_access_token()

            logger.info(
                "%s: Shopify authentication successful.",
                self.shop_name
            )

            return True

        except ShopifyAPIError as exc:

            logger.error(
                "%s: Shopify authentication failed: %s",
                self.shop_name,
                exc
            )

            return False