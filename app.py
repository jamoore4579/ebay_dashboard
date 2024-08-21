from flask import Flask, render_template, jsonify
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')

app = Flask(__name__)

def parse_datetime(date_str):
    # Parse the datetime string and make it timezone-aware
    dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    return dt.replace(tzinfo=timezone.utc)

@app.route('/')
def index():
    try:
        # Initialize the eBay Finding API connection
        api = Finding(appid=API_KEY, config_file=None)

        # Define the request payload
        response = api.execute('findItemsAdvanced', {
            'keywords': 'football rookie card',
            'categoryId': '213',
            'itemFilter': [
                {'name': 'MaxPrice', 'value': '5.00', 'paramName': 'Currency', 'paramValue': 'USD'},
                {'name': 'ListingType', 'value': 'Auction'},
                {'name': 'EndTimeTo', 'value': (datetime.now(timezone.utc) + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')}
            ],
            'paginationInput': {
                'entriesPerPage': '50',
                'pageNumber': '1'
            },
            'sortOrder': 'EndTimeSoonest',
            'outputSelector': ['PictureURLLarge']
        })

        items = []
        if response.reply.ack == 'Success':
            for item in response.reply.searchResult.item:
                title = item.title
                price = item.sellingStatus.currentPrice.value
                end_time = item.listingInfo.endTime
                item_url = item.viewItemURL
                item_id = item.itemId  # Auction ID

                # Convert end_time to timezone-aware datetime if it's a string
                if isinstance(end_time, str):
                    end_time = parse_datetime(end_time)
                else:
                    # Ensure end_time is timezone-aware if it's a datetime object
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=timezone.utc)

                # Calculate time remaining
                time_remaining = end_time - datetime.now(timezone.utc)
                if time_remaining.total_seconds() <= 86400:  # 24 hours in seconds
                    items.append({
                        'title': title,
                        'price': price,
                        'end_time': end_time,
                        'url': item_url,
                        'auction_id': item_id
                    })
        return render_template('index.html', items=items)

    except ConnectionError as e:
        return f"Error: {e} <br> Response: {e.response.dict()}"

if __name__ == '__main__':
    app.run(debug=True)
