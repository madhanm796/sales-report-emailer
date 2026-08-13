import json
import os
import threading


class ReportState:

    def __init__(
        self,
        file_path: str = "report_state.json"
    ):

        self.file_path = file_path

        self.lock = (
            threading.Lock()
        )

        self.data = (
            self._load()
        )

    # ========================================================
    # LOAD
    # ========================================================

    def _load(self) -> dict:

        if not os.path.exists(
            self.file_path
        ):

            return {}

        try:

            with open(
                self.file_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            if isinstance(
                data,
                dict
            ):

                return data

            return {}

        except (
            json.JSONDecodeError,
            OSError
        ):

            return {}

    # ========================================================
    # GET
    # ========================================================

    def get_last_successful_run(
        self,
        brand_key: str
    ):

        return self.data.get(
            brand_key
        )

    # ========================================================
    # SAVE
    # ========================================================

    def set_last_successful_run(
        self,
        brand_key: str,
        timestamp: str
    ):

        with self.lock:

            self.data[
                brand_key
            ] = timestamp

            temporary_file = (
                f"{self.file_path}.tmp"
            )

            with open(
                temporary_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.data,
                    file,
                    indent=4
                )

            os.replace(
                temporary_file,
                self.file_path
            )