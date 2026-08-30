import requests
import time
import json
import datetime 
from datetime import timedelta


url = URL = f"https://gamma-api.polymarket.com/markets"


past_markets = []
future_markets = []
offset = 0
limit = 100
today = datetime.date.today()
one_week = datetime.timedelta(days=7)
end_date_max = today + one_week
end_date_min = today - one_week
#i think we need one set for historical data and one for active markets because the api endpoints for prices are different

#get historical data
while True:
    try:
        response = requests.get(url, params={'limit': limit, 'offset': offset, 'end_date_max': datetime.date.today(), 'end_date_min': end_date_min}, timeout=10)

        data = response.json()

        if not data:
            break

        past_markets.extend(data)

        offset += limit

        if len(past_markets) % 5000 == 0:
            # with open('polymarket_markets_historical_partial.json', 'w') as f:
            #     json.dump(past_markets, f)
            
            print(f"saved {len(past_markets)} markets so far...")
            time.sleep(1)
    except Exception as e:
        print(f"Error fetching markets: {e}: trying again in 5 seconds...")
        time.sleep(5)
        continue


with open('polymarket_markets_historical.json', 'w') as f:
    json.dump(past_markets, f)


print(f" Done. Total historical markets fetched: {len(past_markets)}")




offset = 0



#get future markets starting today and looking forward one week
while True:
    try:
        response = requests.get(url, params={'limit': limit, 'offset': offset, 'end_date_min': datetime.date.today(), 'end_date_max': end_date_max}, timeout=10)
        data = response.json()

        if not data:
            break
        future_markets.extend(data)
        offset += limit

        if len(future_markets) % 5000 == 0:
            # with open('polymarket_markets_future_partial', 'w') as f:
            #     json.dump(future_markets, f)
            print(f"saved {len(future_markets)} markets so far...")
            time.sleep(1)
    except Exception as e:
        print(f"Error fetching markets: {e}: trying again in 5 seconds...")
        time.sleep(5)
        continue

past_markets.extend(future_markets)

with open('polymarket_markets_all.json', 'w') as f:
    json.dump(past_markets, f)


print(f"Done. Total future markets fetched: {len(future_markets)}")
print(f"Total markets fetched: {len(past_markets)}")

