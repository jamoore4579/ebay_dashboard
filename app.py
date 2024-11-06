from flask import Flask, request, render_template
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')

app = Flask(__name__)

def search_auction_trading_cards(keywords):
    try:
        api = Finding(appid=API_KEY, config_file=None)
        category_id = "213"  # Category ID for trading cards
        response = api.execute('findItemsAdvanced', {
            'keywords': keywords,
            'categoryId': category_id,
            'itemFilter': [
                {'name': 'ListingType', 'value': 'Auction'}
            ]
        })
        
        est = pytz.timezone('America/New_York')
        items = response.reply.searchResult.item
        results = []
        
        for item in items:
            end_date_utc = item.listingInfo.endTime
            if isinstance(end_date_utc, str):
                end_date_utc = datetime.fromisoformat(end_date_utc).replace(tzinfo=pytz.utc)
            elif end_date_utc.tzinfo is None:
                end_date_utc = end_date_utc.replace(tzinfo=pytz.utc)

            end_date_est = end_date_utc.astimezone(est)
            
            listing = {
                'title': getattr(item, 'title', ''),
                'category_name': getattr(item.primaryCategory, 'categoryName', '') if hasattr(item, 'primaryCategory') else '',
                'location': getattr(item, 'location', ''),
                'condition': getattr(item.condition, 'conditionDisplayName', '') if hasattr(item, 'condition') else '',
                'end_date': end_date_est.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                'current_price': getattr(item.sellingStatus.currentPrice, 'value', ''),
                'currency': getattr(item.sellingStatus.currentPrice, '_currencyId', ''),
                'bid_count': getattr(item.sellingStatus, 'bidCount', ''),
                'view_item_url': getattr(item, 'viewItemURL', '')
            }
            results.append(listing)

        print("Results:", results)

        return results or [{"message": "No results found"}]

    except ConnectionError as e:
        print(e)
        return [{"error": "Connection error"}]

@app.route("/", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    print(f"Request method: {request.method}")
    if request.method == "POST":
        keywords = request.form.get("keywords")
        results = search_auction_trading_cards(keywords)
        print("Search Results:", results)
        return render_template("openSearchResults.html", results=results)
    return render_template("openSearch.html")

if __name__ == "__main__":
    app.run(debug=True)
