import json
import requests



url = 'https://map.ke.com/proxyApi/i.c-pc-webapi.ke.com/map/houselist'
params = {
    'cityId': 310000,
    'dataSource': 'ESF',
    'curPage': 1,
    'condition': None,
    'type': 30002,
    'resblockId': 5011000013309,
    'maxLatitude': 31.067811327412045,
    'minLatitude': 31.05794353810513,
    'maxLongitude': 121.26133769519328,
    'minLongitude': 121.20851733120658,
}
cookies = {
    'lianjia_uuid': r'51f245bc-cf1f-49e9-a048-5a1a41843183',
    'crosSdkDT2019DeviceId': r'affubm--9il3s-vtusotxi8fn0ku2-6nar8g43n',
    'lfrc_': r'0f3e6ec7-1c40-4e60-b39d-4157c6835b58',
    '_ga': r'GA1.2.1051830722.1754268915',
    'Hm_lvt_b160d5571570fd63c347b9d4ab5ca610': r'1754540474,1754638633,1754901360,1754979176',
    'HMACCOUNT': r'C519DC537B49CB16',
    'ftkrc_': r'3edc3f66-c74e-4451-90cf-bc65a44aa741',
    'select_city': r'310000',
    'lianjia_ssid': r'1aa8f194-c9a3-4be0-81ac-5636d337676d',
    'sensorsdata2015jssdkcross': r'%7B%22distinct_id%22%3A%221979fc22d1f108b-08a1f6542dd1ed8-18525636-1405320-1979fc22d2030da%22%2C%22%24device_id%22%3A%221979fc22d1f108b-08a1f6542dd1ed8-18525636-1405320-1979fc22d2030da%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.bing.com%2F%22%2C%22%24latest_referrer_host%22%3A%22www.bing.com%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_utm_source%22%3A%22biying%22%2C%22%24latest_utm_medium%22%3A%22pinzhuan%22%2C%22%24latest_utm_campaign%22%3A%22wymoren%22%2C%22%24latest_utm_content%22%3A%22biaotimiaoshu%22%2C%22%24latest_utm_term%22%3A%22biaoti%22%7D%7D',
    'login_ucid': r'2000000352323126',
    'lianjia_token': r'2.001176bd467cedd69c00db94777911589d',
    'lianjia_token_secure': r'2.001176bd467cedd69c00db94777911589d',
    'security_ticket': r'NXX2bPStMZVA/kqPKSEx0USfoTRXGShhbplAhwrLIEOJPPUKB+Dpmf9nyIIghE93aZPewRw+TRg60I8UiiLOk8gWB5e8pQriV6bH0TWjM7WjdyRtvGEGrqIYvj63USP7/Qn+7bg9UQMR001hOqu2lRaNWFGJt7sz/JvELqTNVDw=',
    'Hm_lpvt_b160d5571570fd63c347b9d4ab5ca610': r'1755502320',
}
cookie = '; '.join([f'{k}={v}' for k, v in cookies.items()])
print(cookie == 'lianjia_uuid=51f245bc-cf1f-49e9-a048-5a1a41843183; crosSdkDT2019DeviceId=affubm--9il3s-vtusotxi8fn0ku2-6nar8g43n; lfrc_=0f3e6ec7-1c40-4e60-b39d-4157c6835b58; _ga=GA1.2.1051830722.1754268915; Hm_lvt_b160d5571570fd63c347b9d4ab5ca610=1754540474,1754638633,1754901360,1754979176; HMACCOUNT=C519DC537B49CB16; digv_extends=%7B%22utmTrackId%22%3A%22%22%7D; ke_uuid=ee3316cb8ba83f9099701b28430d5d7c; beikeBaseData=%7B%22parentSceneId%22%3A%22%22%7D; LiveWSPKT21787522=d7f7d27785be4385a22e57dbcfa5076b; NPKT21787522fistvisitetime=1754979653942; NPKT21787522lastvisitetime=1754979653942; NPKT21787522visitecounts=1; NPKT21787522visitepages=1; NPKT21787522IP=%7C61.169.135.2%7C; ftkrc_=3edc3f66-c74e-4451-90cf-bc65a44aa741; select_city=310000; lianjia_ssid=1aa8f194-c9a3-4be0-81ac-5636d337676d; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221979fc22d1f108b-08a1f6542dd1ed8-18525636-1405320-1979fc22d2030da%22%2C%22%24device_id%22%3A%221979fc22d1f108b-08a1f6542dd1ed8-18525636-1405320-1979fc22d2030da%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.bing.com%2F%22%2C%22%24latest_referrer_host%22%3A%22www.bing.com%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_utm_source%22%3A%22biying%22%2C%22%24latest_utm_medium%22%3A%22pinzhuan%22%2C%22%24latest_utm_campaign%22%3A%22wymoren%22%2C%22%24latest_utm_content%22%3A%22biaotimiaoshu%22%2C%22%24latest_utm_term%22%3A%22biaoti%22%7D%7D; login_ucid=2000000352323126; lianjia_token=2.001176bd467cedd69c00db94777911589d; lianjia_token_secure=2.001176bd467cedd69c00db94777911589d; security_ticket=NXX2bPStMZVA/kqPKSEx0USfoTRXGShhbplAhwrLIEOJPPUKB+Dpmf9nyIIghE93aZPewRw+TRg60I8UiiLOk8gWB5e8pQriV6bH0TWjM7WjdyRtvGEGrqIYvj63USP7/Qn+7bg9UQMR001hOqu2lRaNWFGJt7sz/JvELqTNVDw=; Hm_lpvt_b160d5571570fd63c347b9d4ab5ca610=1755502320')
print(list(cookies.keys()))

headers = {
    'cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()]),
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
}
res = requests.get(url, params=params, headers=headers)
print(json.dumps(res.json(), indent=2, ensure_ascii=False))