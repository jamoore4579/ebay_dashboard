from flask import Flask, render_template, request
from ebaysdk.finding import Connection as Finding
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')

# Home route to show the search form
@app.route('/', methods=['GET', 'POST'])
def index():
    items = []
    total_pages = 1
    current_page = int(request.args.get('page', 1))
    
    # Initialize variables
    keywords = request.form.get('keywords', request.args.get('keywords', '"football" "rookie"'))
    category_id = request.form.get('category_id', request.args.get('category_id', '213'))
    max_price = request.form.get('max_price', request.args.get('max_price', '5.00'))
    listing_type = request.form.get('listing_type', request.args.get('listing_type', 'Auction'))
    start_time_from = request.form.get('start_time_from', request.args.get('start_time_from'))
    start_time_to = request.form.get('start_time_to', request.args.get('start_time_to'))

    # Convert start_time_from and start_time_to to the correct format if they are provided
    if start_time_from:
        try:
            start_time_from = datetime.strptime(start_time_from, '%Y-%m-%dT%H:%M')
            start_time_from = start_time_from.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        except ValueError:
            start_time_from = None
        
    if start_time_to:
        try:
            start_time_to = datetime.strptime(start_time_to, '%Y-%m-%dT%H:%M')
            start_time_to = start_time_to.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        except ValueError:
            start_time_to = None

    # Create a connection to the eBay Finding API
    api = Finding(appid=API_KEY, config_file=None, siteid="EBAY-US")

    # Construct the API request
    request_params = {
        'keywords': keywords,
        'categoryId': category_id,
        'itemFilter': [
            {'name': 'MaxPrice', 'value': max_price, 'paramName': 'Currency', 'paramValue': 'USD'},
            {'name': 'ListingType', 'value': listing_type}
        ],
        'sortOrder': 'EndTimeSoonest',
        'outputSelector': 'SellerInfo',
        'paginationInput': {
            'entriesPerPage': 10,
            'pageNumber': current_page
        }
    }
    
    # Add time filters only if both are provided
    if start_time_from and start_time_to:
        request_params['itemFilter'].extend([
            {'name': 'EndTimeFrom', 'value': start_time_from},
            {'name': 'EndTimeTo', 'value': start_time_to}
        ])

    # Execute the API request
    response = api.execute('findItemsAdvanced', request_params)

    # Debugging: Print the number of items found
    print(f"Number of items found: {len(response.reply.searchResult.item)}")

    # Get total pages
    total_pages = int(response.reply.paginationOutput.totalPages)

    # Parse the response and collect the desired information
    for item in response.reply.searchResult.item:
        try:
            item_id = item.itemId
            title = item.title
            price = float(item.sellingStatus.currentPrice.value)
            end_time = item.listingInfo.endTime

            # Adjust end time to Pacific Time
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            end_time_adjusted = end_time - timedelta(hours=4)

            # Store the item information
            items.append({
                'item_id': item_id,
                'title': title,
                'price': price,
                'end_time': end_time_adjusted.strftime("%Y-%m-%d %I:%M %p")
            })
        except Exception as e:
            print(f"Error processing item: {e}")

    return render_template(
        'index.html', 
        items=items, 
        current_page=current_page, 
        total_pages=total_pages, 
        keywords=keywords, 
        category_id=category_id, 
        max_price=max_price, 
        listing_type=listing_type, 
        start_time_from=start_time_from, 
        start_time_to=start_time_to
    )

if __name__ == '__main__':
    app.run(debug=True)
