import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_URL = os.getenv("API_URL")
MARKET = os.getenv("MARKET")

MAX_BOUND = float(os.getenv("MAX_BOUND"))

PRICE_INCREMENT = 0.001e-07

HEADERS = {
    "Authorization": f'Bearer {API_SECRET}',
    'Content-Type': 'application/json'
}



def get_order_book():
    response = requests.get(f"{API_URL}/orderbook/{MARKET}", headers=HEADERS)
    #print(f"[DEBUG] Status: {response.status_code}")
    #print(f"[DEBUG get_order_book] Response Text: {response.text}")
    return response.json()

def get_my_orders():
    response = requests.get(f"{API_URL}/order/market/{MARKET}", headers=HEADERS)
    #print(f"[DEBUG] Status: {response.status_code}")
    #print(f"[DEBUG get_my_orders] Response Text: {response.text}")
    return response.json()

def cancel_order(order_id):
    response = requests.get(f"{API_URL}/order/{order_id}/cancel", headers=HEADERS)
    #print(f"[DEBUG] Status: {response.status_code}")
    #print(f"[DEBUG cancel_order] Response Text: {response.text}")
    return response.status_code == 204

def place_order(price, amount):
    data = {
        "amount": amount,
        "market": MARKET,
        "price": price,
        "side": "buy",
        "type": "limit"
    }

    #print(f"[DEBUG] Placing order with data: {data}")


    response = requests.post(f"{API_URL}/order", headers=HEADERS, json=data)
    #print(f"[DEBUG] Status: {response.status_code}")
    #print(f"[DEBUG place_order] Response Text: {response.text}")

    return response.json()

def get_balance():
    response = requests.get(f"{API_URL}/balances", headers=HEADERS)
    #print(f"[DEBUG] Status: {response.status_code}")
    #print(f"[DEBUG get_balance] Response Text: {response.text}")

    try:
        data = response.json()
        currencies = data['data']['user']['currencies']
    except Exception as e:
        print(f"[ERROR] Failed to parse balances: {e}")
        return 0.0

    for currency in currencies:
        if currency['id'] == 'USDT':
            return float(currency['balance'])
    return 0.0
def main():

    order_book = get_order_book()

    time.sleep(1)
    highest_bid = float(order_book['bids'][0][0])
    print(f'highest bid: {highest_bid}')
    new_bid_price = highest_bid + PRICE_INCREMENT
    
    my_orders_raw = get_my_orders()
    time.sleep(1)

    my_orders = my_orders_raw['data']['userOrders']['result']
    #print(my_orders)
    if(my_orders != []): 
        count = 0   
        my_bid = next((order for order in my_orders if order['market'] == MARKET and order['side'] == 'buy'), None)
        count +=1
        print(count)

        if new_bid_price > MAX_BOUND:
            print(f"New bid price {new_bid_price} exceeds max limit {MAX_BOUND}")
            return

        if my_bid:
            #print(my_bid)
            current_price = float(my_bid['price'])
            print(f'my bid: {highest_bid}')
            if current_price < highest_bid:
                print(f"Outbid! Canceling and rebidding at {new_bid_price}")
                cancel_order(my_bid['id'])
                time.sleep(1)

                available_usdt = get_balance()
                time.sleep(1)
                if available_usdt > 1:
                    amount = round(available_usdt / new_bid_price, 12)
                    place_order(new_bid_price, amount-100000)
                    time.sleep(1)
                else:
                    print("Insufficient USDT balance.")

            else:
                print("Still highest bidder.")
    else:
        print("No active bid. Placing one now.")
        available_usdt = get_balance()
        time.sleep(1)
        if available_usdt > 1:
            amount = round(available_usdt / new_bid_price, 8)
            place_order(new_bid_price, amount-100000)
            time.sleep(1)
        else:
            print("Insufficient USDT balance.")



if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)  # Check every 3 seconds