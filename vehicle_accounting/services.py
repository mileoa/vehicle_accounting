import requests
from vehicle_accounting.settings import GEOPIFY_API_KEY


def get_address_from_coordinates(lat, lng):
    try:
        url = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={lng}&format=json&apiKey={GEOPIFY_API_KEY}"

        response = requests.get(url)
        data = response.json()

        # Проверяем статус ответа
        if (
            response.status_code == 200
            and data.get("results")
            and len(data["results"]) > 0
        ):
            return {
                "status": "success",
                "address": data["results"][0]["formatted"],
            }
        return {"status": "error", "address": None}

    except Exception:
        return {"status": "error", "address": None}
