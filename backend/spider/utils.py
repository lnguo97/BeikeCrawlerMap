import asyncio
import base64
import pathlib

from pydoll.browser.tab import Tab 


async def crawl_login_qr_code(tab: Tab) -> str:
    await tab.go_to('https://sh.ke.com/')
    login_btn = await tab.find(class_name="btn-login", timeout=5)
    await login_btn.click()
    qr_login_btn = await tab.query(
        '//*[@id="loginModel"]/div[2]/div[2]/div[4]/div[1]/ul/li[1]',
        timeout=5
    )
    await qr_login_btn.click()
    await asyncio.sleep(2)
    qr_img = await tab.find(class_name='qrcode_pic_container', timeout=5)
    img_path = pathlib.Path('temp/qr_code.png')
    img_path.parent.mkdir(parents=True, exist_ok=True)
    await qr_img.take_screenshot(img_path, quality=200)
    with open(img_path, 'rb') as image_file:
        base64_str = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_str


async def crawl_login_status(tab: Tab) -> bool:
    login_info = await tab.find(class_name="typeShowUser", timeout=5)
    login_info_text = await login_info.text
    return login_info_text.endswith('退出')
