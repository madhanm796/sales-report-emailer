import json
import logging
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class ReportState:
    """
    Persistent reporting state.

    The actual persistence is handled by GitHub Actions
    through the REPORT_STATE environment variable.

    This class keeps the application independent of the
    storage mechanism.
    """

    def __init__(self, raw_state: str | None = None):

        self._state = {}

        if raw_state:

            try:

                parsed = json.loads(
                    raw_state
                )

                if isinstance(
                    parsed,
                    dict
                ):

                    self._state = parsed

            except json.JSONDecodeError:

                logger.warning(
                    "REPORT_STATE contains invalid JSON. "
                    "Starting with empty state."
                )


    # ========================================================
    # GET
    # ========================================================

    def get_last_successful_run(
        self,
        brand_key: str
    ) -> str | None:

        value = self._state.get(
            brand_key
        )

        if not value:

            return None

        return str(value)


    # ========================================================
    # SET
    # ========================================================

    def set_last_successful_run(
        self,
        brand_key: str,
        timestamp: str
    ) -> None:

        self._state[
            brand_key
        ] = timestamp


    # ========================================================
    # EXPORT
    # ========================================================

    def to_json(self) -> str:

        return json.dumps(
            self._state,
            separators=(
                ",",
                ":"
            ),
            sort_keys=True
        )


    # ========================================================
    # VALIDATE TIMESTAMP
    # ========================================================

    def validate_timestamp(
        self,
        timestamp: str
    ) -> datetime:

        parsed = datetime.fromisoformat(
            timestamp
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed