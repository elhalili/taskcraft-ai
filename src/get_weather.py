import requests

WEATHER_API_KEY="b37e3983fbf14744a0b185648251104"
def get_weather(city, api_key):
    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": api_key, "q": city}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 

        data = response.json()
        weather = data['current']['condition']['text']
        temp = data['current']['temp_c']

        print(f"Weather in {city}: {weather}, Temperature: {temp}°C")
        return weather, temp

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch weather data: {e}")
        return None

get_weather("Rabat", WEATHER_API_KEY)

