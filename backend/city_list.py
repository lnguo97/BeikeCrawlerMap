
import csv
import json
import asyncio
import os
import re
import time

import dotenv
import requests
from bs4 import BeautifulSoup


def crawl_city_list() -> list[dict]:
    dotenv.load_dotenv()
    city_code_map = {}
    city_code_map_abbr = {}
    with open('data/AMap_adcode_citycode.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)
        for row in csv_reader:
            city_code_map[row[0]] = row[1]
            city_code_map_abbr[row[0][:2]] = row[1]
    res = requests.get(
        'https://www.ke.com/city/', 
        headers={
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/138.0.0.0 '
                'Safari/537.36'
            )
        }
    )
    res.raise_for_status()
    soup = BeautifulSoup(res.content, 'html.parser')
    city_list = []
    city_root_ul = soup.find("ul", class_="city_list_ul")
    for province_group in city_root_ul.find_all("div", class_="city_province"):
        for city_li in province_group.find_all("li", class_="CLICKDATA"):
            city_a_tag = city_li.find("a")
            city_name = city_a_tag.get_text(strip=True)
            city_url = 'https:' + city_a_tag.get("href")
            print(city_name)
            if city_name + '市' in city_code_map:
                city_code = city_code_map[city_name + '市']
            else:
                city_code = city_code_map_abbr[city_name[:2]]
            res = requests.get(
                url='https://restapi.amap.com/v3/config/district', 
                headers={
                    'user-agent': (
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/138.0.0.0 '
                        'Safari/537.36'
                    )
                }, 
                params={
                    'key': os.getenv('AMAP_API_KEY'), 
                    'keywords': city_code, 
                    'subdistrict': 0,
                    'extensions': 'all'
                }
            )
            res.raise_for_status()
            result = res.json()
            polyline = result['districts'][0]['polyline']
            lat_list, lon_list = [], []
            for point in re.split(r'[;|]', polyline):
                lat, lon = point.split(',')
                lat_list.append(float(lat))
                lon_list.append(float(lon))
            min_lat, max_lat = min(lat_list), max(lat_list)
            min_lon, max_lon = min(lon_list), max(lon_list)
            time.sleep(0.5)
            city_list.append({
                'name': city_name, 
                'url': city_url,
                'code': city_code,
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon,
            })
    with open('data/city_list.json', mode='w') as f:
        json.dump(city_list, f, indent=2, ensure_ascii=False)
