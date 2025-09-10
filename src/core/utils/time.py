from datetime import datetime

import pytz


def str_iso_datetime_to_timezone(
    iso_datetime, iso_datetime_timezone, to_timezone
):
    try:
        naive_datetime = datetime.fromisoformat(
            iso_datetime.replace("Z", "+00:00").replace("z", "+00:00")
        )

        datetime_local = naive_datetime
        if naive_datetime.tzinfo is None:
            datetime_local = iso_datetime_timezone.localize(naive_datetime)

        start_datetime_utc = datetime_local.astimezone(to_timezone)
        return start_datetime_utc
    except ValueError:
        return None
