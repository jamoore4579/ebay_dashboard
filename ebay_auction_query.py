import os
import csv
from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')

class Ebay_21(object):
    def __init__(self, API_KEY):
        self.api_key = API_KEY

    def fetch(self):
        try:
            api = Connection(appid=self.api_key, config_file=None)
            # Set up the filter parameters
            request = {
                'keywords': 'michael jordan -love -packers -nfl',
                'categoryId': '213',  # Category ID for trading cards
                'itemFilter': [
                    {'name': 'EndTimeTo', 'value': '2024-08-16T23:59:59Z'},  # End date/time
                    {'name': 'ListingType', 'value': 'Auction'}  # Only auctions
                ],
                'outputSelector': ['SellerInfo', 'PictureURLLarge'],
                'sortOrder': 'EndTimeSoonest'
            }
        
            response = api.execute('findItemsAdvanced', request)

            # Check if search results and items exist
            if hasattr(response.reply, 'searchResult') and hasattr(response.reply.searchResult, 'item'):
                items = response.reply.searchResult.item
                if not isinstance(items, list):
                    items = [items]  # Ensure 'items' is a list even if there's only one item
                
                # Prepare to write data to CSV
                file_path = 'C:/Users/jmoore/Documents/projects/Auction Items.csv'
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Auction ID', 'Title', 'Price', 'End Time'])

                    for item in items:
                        auction_id = item.itemId
                        title = item.title
                        price = item.sellingStatus.currentPrice.value
                        end_time = item.listingInfo.endTime

                        # Print auction details
                        print(f"Auction ID: {auction_id}, Title: {title}, Price: {price}, End Time: {end_time}")

                        # Write auction details to CSV
                        writer.writerow([auction_id, title, price, end_time])
            else:
                print("No items found for the specified search criteria.")

        except ConnectionError as e:
            print(e)
            print(e.response.dict())

    def parse(self):
        pass

# Main driver
if __name__ == '__main__':
    e = Ebay_21(API_KEY)
    e.fetch()
    e.parse()