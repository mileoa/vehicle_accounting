import requests
from django.core.cache import cache

from core.settings.local import GEOPIFY_API_KEY


def get_address_from_coordinates(lat, lng):
    try:
        cache_key = f"lat_lang_to_address_{lat}_{lng}"
        cached_address = cache.get(cache_key)
        if cached_address is not None:
            return {"status": "success", "address": cached_address}

        url = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={lng}&format=json&apiKey={GEOPIFY_API_KEY}"

        response = requests.get(url)
        data = response.json()

        # Проверяем статус ответа
        if (
            response.status_code == 200
            and data.get("results")
            and len(data["results"]) > 0
        ):
            received_address = data["results"][0]["formatted"]
            cache.set(cache_key, received_address, 60 * 60 * 24)
            return {
                "status": "success",
                "address": received_address,
            }
        return {"status": "error", "address": None}

    except Exception:
        return {"status": "error", "address": None}
