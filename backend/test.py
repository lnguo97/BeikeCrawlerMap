import asyncio

import requests

# from spider import BeikeMapSpider
from spider.utils import user_agent


# url = BeikeMapSpider.get_community_list_url(30.66, 30.66+0.05, 120.86, 120.86+0.05)
res = requests.get(
    'https://map.ke.com/proxyApi/i.c-pc-webapi.ke.com/map/bubblelist?cityId=310000&dataSource=ESF&condition=&id=&groupType=district&maxLatitude=31.420653367976175&minLatitude=31.077355244681904&maxLongitude=121.73511267634586&minLongitude=121.07395982100208', 
    headers={'user-agent': user_agent})
print(res.json())
