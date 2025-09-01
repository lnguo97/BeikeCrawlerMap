
import csv
import json
import os
import time

import dotenv
import requests

from bs4 import BeautifulSoup


def verify_city_code(city_code: str) -> bool:
    print(f'checking city code: {city_code}', end=' ')
    res = requests.get(f'https://map.ke.com/map/{city_code}/ESF/')
    res.raise_for_status()
    soup = BeautifulSoup(res.content, 'html.parser')
    msg = soup.find(class_='big')
    if msg is not None and msg.get_text(strip=True).startswith('呣'):
        print('Invalid')
        return False
    print('Valid')
    return True


def crawl_city_coordinate(city_code: str):
    dotenv.load_dotenv()
    api_key = os.getenv('AMAP_API_KEY')
    res = requests.get(
        url='https://restapi.amap.com/v3/config/district',
        params={
            'key': api_key, 
            'keywords': city_code, 
            'subdistrict': 0,
            'extensions': 'all'
        }
    )
    res.raise_for_status()
    geo_info = res.json()
    lat_list, lon_list = [], []
    for point in geo_info['districts'][0]['polyline'].split(';'):
        for sub_point in point.split('|'):
            lat, lon = sub_point.split(',')
            lat_list.append(lat)
            lon_list.append(lon)
    min_lat, max_lat = min(lat_list), max(lat_list)
    min_lon, max_lon = min(lon_list), max(lon_list)
    return {
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lon': min_lon,
        'max_lon': max_lon,
    }


def update_city_list():
    headers = {
        'user-agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/138.0.0.0 '
            'Safari/537.36'
        )
    }
    city_code_resource = 'data/AMap_adcode_citycode.csv'
    with open(city_code_resource, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        city_code_mapping = {}
        for row in list(csv_reader)[1:]:
            city_name_prefix = row[0][:2]
            city_code = row[1]
            city_code_mapping[city_name_prefix] = city_code
    res = requests.get('https://www.ke.com/city/', headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, 'html.parser')
    city_data = []
    city_root_ul = soup.find("ul", class_="city_list_ul")
    for province_group in city_root_ul.find_all("div", class_="city_province"):
        for city_li in province_group.find_all("li", class_="CLICKDATA"):
            city_a_tag = city_li.find("a")
            city_name = city_a_tag.get_text(strip=True)
            city_url = 'https:' + city_a_tag.get("href")

            res = requests.get(city_url, headers=headers)


            city_code = city_code_mapping[city_name[:2]]
            city_coordinate = crawl_city_coordinate(city_code)
            city_data.append({
                'name': city_name,
                'url': 'https:' + city_url,
                'code': city_code,
                **city_coordinate
            })
            print(city_name, city_code, city_url)
            time.sleep(0.5)
    with open('data/city_list.json', mode='w') as f:
        json.dump(city_data, f, indent=2, ensure_ascii=False)
        
        
update_city_list()
