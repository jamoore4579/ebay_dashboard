from flask import Flask, render_template, request
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
from datetime import datetime, timezone
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

@app.route('/', methods=['GET', 'POST'])
def index():
    items = []
    if request.method == 'POST':
        # Get the start and end times from the form
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')

        try:
            # Convert to datetime objects
            start_time = datetime.fromisoformat(start_time_str).replace(tzinfo=timezone.utc)
            end_time = datetime.fromisoformat(end_time_str).replace(tzinfo=timezone.utc)

            # Initialize the eBay Finding API connection
            finding_api = Finding(appid=API_KEY, config_file=None)

            # Define the request payload with outputSelector for additional details
            response = finding_api.execute('findItemsAdvanced', {
                'keywords': 'football rookie card',
                'categoryId': '213',
                'itemFilter': [
                    {'name': 'MaxPrice', 'value': '5.00', 'paramName': 'Currency', 'paramValue': 'USD'},
                    {'name': 'ListingType', 'value': 'Auction'},
                    {'name': 'EndTimeTo', 'value': end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')},
                    {'name': 'StartTimeFrom', 'value': start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
                ],
                'paginationInput': {
                    'entriesPerPage': '50',
                    'pageNumber': '1'
                },
                'sortOrder': 'EndTimeSoonest',
                'outputSelector': ['PictureURLLarge']
            })

            if response.reply.ack == 'Success':
                for item in response.reply.searchResult.item:
                    title = item.title
                    price = item.sellingStatus.currentPrice.value
                    item_end_time = item.listingInfo.endTime
                    item_url = item.viewItemURL
                    item_id = item.itemId  # Auction ID

                    # Convert end_time to timezone-aware datetime if it's a string
                    if isinstance(item_end_time, str):
                        item_end_time = parse_datetime(item_end_time)
                    else:
                        # Ensure end_time is timezone-aware if it's a datetime object
                        if item_end_time.tzinfo is None:
                            item_end_time = item_end_time.replace(tzinfo=timezone.utc)

                    # Calculate time remaining
                    time_remaining = item_end_time - datetime.now(timezone.utc)
                    if time_remaining.total_seconds() <= 86400:  # 24 hours in seconds
                        items.append({
                            'title': title,
                            'price': price,
                            'end_time': item_end_time,
                            'url': item_url,
                            'auction_id': item_id
                        })
        except ConnectionError as e:
            return f"Connection Error: {e}"
        except Exception as e:
            return f"Error: {e}"

    return render_template('index.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
