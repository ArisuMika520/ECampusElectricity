from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import re

def get_credentials():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--proxy-server=http://localhost:8080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问电费查询页面触发认证
        driver.get("https://application.xiaofubao.com/app/electric/")
        time.sleep(3)
        
        # 执行模拟查询（需根据实际页面元素调整选择器）
        driver.find_element(By.CSS_SELECTOR, ".query-btn").click()
        time.sleep(2)
        
        # 从浏览器日志获取网络请求
        logs = driver.get_log('performance')
        for log in logs:
            message = json.loads(log['message'])['message']
            if message['method'] == 'Network.requestWillBeSent':
                url = message['params']['request']['url']
                if 'queryRoomSurplus' in url:
                    # 提取shiroJID
                    cookies = message['params']['request']['headers'].get('Cookie', '')
                    shiro_jid = re.search(r'shiroJID=([^;]+)', cookies).group(1)
                    
                    # 提取ymId
                    post_data = message['params']['request']['postData']
                    ym_id = re.search(r'ymId=([^&]+)', post_data).group(1)
                    
                    return shiro_jid, ym_id
    finally:
        driver.quit()

def update_config(shiro_jid, ym_id):
    # 更新YAML配置
    with open("d:/Code/CFT&Py/Elect-bot/config.yaml", "r+", encoding="utf-8") as f:
        content = f.read()
        content = re.sub(r'shiroJID: .+', f'shiroJID: {shiro_jid}', content)
        content = re.sub(r'ymId: .+', f'ymId: {ym_id}', content)
        f.seek(0)
        f.write(content)
        f.truncate()
    
    # 更新Python代码
    with open("d:/Code/CFT&Py/Elect-bot/Electricity.py", "r+", encoding="utf-8") as f:
        content = f.read()
        content = re.sub(r"shiroJID': '.+?'", f"shiroJID': '{shiro_jid}'", content)
        content = re.sub(r"ymId': '.+?'", f"ymId': '{ym_id}'", content)
        f.seek(0)
        f.write(content)
        f.truncate()

if __name__ == "__main__":
    # 先启动mitmproxy监听
    from mitmproxy.tools.main import mitmdump
    mitmdump(["-s", __file__])
    
    # 执行自动化抓取
    shiro_jid, ym_id = get_credentials()
    if shiro_jid and ym_id:
        update_config(shiro_jid, ym_id)
        print("参数更新成功！")
    else:
        print("未捕获到有效参数")