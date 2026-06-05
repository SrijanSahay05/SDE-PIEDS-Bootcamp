import requests

def get_weather(city: str) -> str:

    try:
        response = requests.get(
            f"https://wttr.in/{city}",
            params={"format":"3"},
            timeout=10
        )
    except Exception as e:
        return f"Error: {e}"
    

    response.raise_for_status()
    return response.text.strip()

# print(get_weather("Pilani"))
# print(get_weather("Delhi"))

enter_num_city = int(input("Enter the number of cities: "))

for i in range(enter_num_city):
    city = input(f"Enter city[{i+1}]: ")
    weather_res = get_weather(city)
    print(weather_res)