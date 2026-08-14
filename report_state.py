import json
import logging
import os

from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class ReportState:
    """
    Persistent report state.

    The state is stored in report_state.json.

    Example:

    {
        "baybee": "2026-08-14T08:00:00+00:00",
        "drogo": "2026-08-14T08:00:00+00:00",
        "domestica": "2026-08-14T08:00:00+00:00"
    }

    Each brand has its own checkpoint.

    This is important because one brand may succeed while
    another brand fails.
    """

    STATE_FILE = "report_state.json"

    def __init__(self):

        self._state = {}

        self._load()


    # ============================================================
    # LOAD STATE
    # ============================================================

    def _load(self):
        """
        Load the state from report_state.json.

        If the file doesn't exist, start with an empty state.
        """

        if not os.path.exists(
            self.STATE_FILE
        ):

            logger.info(
                "No report state file found. "
                "Starting with empty state."
            )

            self._state = {}

            return


        try:

            with open(
                self.STATE_FILE,
                "r",
                encoding="utf-8"
            ) as state_file:

                data = json.load(
                    state_file
                )


            if not isinstance(
                data,
                dict
            ):

                logger.warning(
                    "Report state file does not contain "
                    "a valid JSON object."
                )

                self._state = {}

                return


            self._state = data


            logger.info(
                "Report state loaded successfully."
            )


        except json.JSONDecodeError as exc:

            logger.error(
                "Invalid JSON in %s: %s",
                self.STATE_FILE,
                exc
            )

            self._state = {}


        except Exception as exc:

            logger.exception(
                "Failed loading report state: %s",
                exc
            )

            self._state = {}


    # ============================================================
    # GET LAST SUCCESSFUL RUN
    # ============================================================

    def get_last_successful_run(
        self,
        brand_key: str
    ) -> str | None:
        """
        Return the last successfully completed timestamp
        for a specific brand.
        """

        value = self._state.get(
            brand_key
        )


        if not value:

            return None


        return str(
            value
        )


    # ============================================================
    # SET LAST SUCCESSFUL RUN
    # ============================================================

    def set_last_successful_run(
        self,
        brand_key: str,
        timestamp: str
    ) -> None:
        """
        Update the in-memory checkpoint for a brand.

        The file is not written immediately.

        The complete state is persisted by save().
        """

        self._state[
            brand_key
        ] = timestamp


    # ============================================================
    # SAVE STATE
    # ============================================================

    def save(self) -> None:
        """
        Write the current state to report_state.json.
        """

        temporary_file = (
            f"{self.STATE_FILE}.tmp"
        )


        try:

            with open(
                temporary_file,
                "w",
                encoding="utf-8"
            ) as state_file:

                json.dump(
                    self._state,
                    state_file,
                    indent=4,
                    sort_keys=True
                )

                state_file.write(
                    "\n"
                )


            # Atomic replacement.

            os.replace(
                temporary_file,
                self.STATE_FILE
            )


            logger.info(
                "Report state saved successfully."
            )


        except Exception as exc:

            logger.exception(
                "Failed saving report state: %s",
                exc
            )


            # Remove temporary file if necessary.

            try:

                if os.path.exists(
                    temporary_file
                ):

                    os.remove(
                        temporary_file
                    )

            except Exception:

                pass


            raise


    # ============================================================
    # VALIDATE TIMESTAMP
    # ============================================================

    @staticmethod
    def parse_timestamp(
        timestamp: str
    ) -> datetime:
        """
        Parse a stored ISO timestamp.

        Always returns a timezone-aware datetime.
        """

        parsed = datetime.fromisoformat(
            timestamp
        )


        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )


        return parsed