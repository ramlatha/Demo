import re
from re import compile
import json
from json import loads
from urllib.parse import urlencode

import scrapy
from scrapy.http import Request

class Target(scrapy.Spider):
    name = 'target'
    tcin_regex = compile(r'\-(\d+)')
    tcin = ''
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    params = {
        'key': '9f36aeafbe60771e321a7cc95a78140772ab3e96',
        'is_bot': 'false',
        'store_id': '1792',
        'pricing_store_id': '1792',
        'has_pricing_store_id': 'true',
        'has_financing_options': 'true',
        'visitor_id': '0189D5B6C85402019E574782DF170CD2',
        'has_size_context': 'true',
        'latitude': '15.910',
        'longitude': '80.470',
        'zip': '52210',
        'state': 'AP',
        'skip_personalized': 'true',
        'channel': 'WEB',
        'page': '/p/undefined',
    }

    api_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?%s'

    def __init__(self, *args, **kwargs):
        super(Target, self).__init__(*args, **kwargs)
        tcin = self.tcin_regex.search(kwargs['url'])
        if tcin:
            self.tcin = tcin.group(1)
            self.params['tcin'] = self.tcin 

    def start_requests(self):
        yield Request(
            url= self.api_url % urlencode(self.params),
            headers=self.headers
        )

    def parse(self, response):
        data = json.loads(response.body.decode('utf-8', 'ignore'))
        product_info = data.get('data',{}).get('product',{})
        url = product_info.get('item',{}).get('enrichment',{}).get('buy_url','')
        tcin = product_info.get('tcin')
        price_amount = product_info.get('price',{}).get('current_retail')
        upc = product_info.get('item',{}).get('primary_barcode')
        bullets = product_info.get('item',{}).get('product_description',{}).get('soft_bullet_description')
        features =  product_info.get('item',{}).get('product_description',{}).get('bullet_descriptions')
        product_data_dict = {}
        pattern = r"<B>(.*?):</B>\s*(.*?)$"
        for item in features:
            match = re.match(pattern, item)
            if match:
                label = match.group(1).strip()
                value = match.group(2).strip()
                product_data_dict[label] = value
        data = {
            "url": url,
            "tcin": tcin,
            "upc": upc,
            "price_amount": price_amount,
            "bullets": bullets,
            "features": product_data_dict
        }

        json_file_path = f"product_info_{self.tcin}.json"

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
