import pandas as pd
import json
import scrapy
from scrapy.crawler import CrawlerProcess

def read_urls(filename):

    # Load the all_urls list from the JSON file
    with open(filename, 'r') as file:
        all_urls = json.load(file)

    print(f"All URLs loaded from {filename}")

    return all_urls

class CustomSpider(scrapy.Spider):
    name = 'custom_spider'

    # Initialize a counter
    request_count = 0

    def __init__(self, urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls[100:] if urls else []

    def parse(self, response):
        self.request_count += 1  # Increment the counter with each request
        description = ""

        # Scraping the review title (h1 tag inside div.product_title)
        review_title = response.css('h1.product-title::text').get()

        if review_title:
            h1_tag = review_title.strip()
        else:
            h1_tag = ""

        # Now, h1_tag contains the content of the h1 tag
        print(h1_tag)

        price = response.css('span.woocommerce-Price-amount ::text')

        if price:
            price = price.get().strip()
        else:
            price = ""

        # Scraping the ck-content
        ck_contents = response.css('div.woocommerce-Tabs-panel--description')

        for ck_content in ck_contents:
            for element in ck_content.xpath('./*'):
                # Extract the text from h2 and h3 tags
                if element.root.tag == 'h2':
                    description += ' '.join(element.css('::text').getall()).strip() + "\n"
                elif element.root.tag == 'h3':
                    description += ' '.join(element.css('::text').getall()).strip() + "\n"

                # Extract the text from p tags
                elif element.root.tag == 'p':
                    description += ' '.join(element.css('::text').getall()).strip() + "\n"

                # Extract the list items from ul tags
                elif element.root.tag == 'ul':
                    li_tags = element.css('li')
                    for li_tag in li_tags:
                        description += f"- {' '.join(li_tag.css('::text').getall()).strip()}" + "\n"

        # Initialize an empty array to hold image URLs
        image_urls = []

        # Select all the div elements with the specific class
        image_elements = response.css('div.woocommerce-product-gallery__image')

        # Loop through each image element to extract the URLs
        for element in image_elements:
            # Extract the main image URL from the 'data-large_image' attribute
            image_url = element.css('img::attr(data-large_image)').get()

            # Add the extracted image URL to the array
            if image_url:
                image_urls.append(image_url)

        data = {}

        if h1_tag and description:
            data = {
                "url": response.url,  # Add the URL of the request
                "content": description,
                "price": price,
                "title": h1_tag  # h1_tag is now guaranteed to be a string
            }

            yield data
        # Print out the current request count
        print('====> h1_tag', h1_tag)
        print('====>description', description)
        print('====>image_urls', image_urls)
        print('====>price', price)

        self.logger.info(f"Number of requests done: {self.request_count}")
        self.logger.info(f"Crawled: {response.url}")

def main():
    # Fetch the url list
    all_urls = read_urls('data/all_urls.json')

    # Initialize the Scrapy crawler process
    process = CrawlerProcess({
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            'data/output.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': None,
                'indent': 4,
            },
        },
        'CLOSESPIDER_TIMEOUT': 60000000000,  # Close the spider after 60 seconds (adjust as needed)
        'DOWNLOAD_DELAY': 3,  # Delay of 2 seconds between each request
    })

    # Start the spider
    process.crawl(CustomSpider, urls=all_urls)
    process.start()

if __name__ == "__main__":
    main()