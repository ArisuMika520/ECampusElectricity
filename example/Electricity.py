from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
from time import sleep
import requests

class ECampusElectricity:
    def __init__(self, config=None):
        self.config = {
            'shiroJID': 'df8bde3a-06e5-435d-b7a8-1026e4d8c331',
            'ymId': '2502567889956864141',
            # 邮件服务器配置
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 465,  # 使用SSL端口
            'smtp_user': '@qq.com',
            'smtp_pass': '',  #授权码
            'from_email': '@qq.com',
            'alert_threshold': 20.0  
        }
        if config:
            self.config.update(config)

    def set_config(self, config):
        self.config.update(config)

    def school_info(self):
        data = self._request('getCoutomConfig', {'customType': 1})
        if data.get('success'):
            return {
                'error': 0,
                'data': {
                    'schoolCode': data['data']['schoolCode'],
                    'schoolName': data['data']['schoolName']
                }
            }
        return self._error_response(data)

    def query_area(self):
        data = self._request('queryArea', {'type': 1})
        if data.get('success'):
            for item in data['rows']:
                item.pop('paymentChannel', None)
                item.pop('isBindAfterRecharge', None)
                item.pop('bindRoomNum', None)
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_building(self, area_id):
        data = self._request('queryBuilding', {'areaId': area_id})
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_floor(self, area_id, building_code):
        data = self._request('queryFloor', {
            'areaId': area_id,
            'buildingCode': building_code
        })
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_room(self, area_id, building_code, floor_code):
        data = self._request('queryRoom', {
            'areaId': area_id,
            'buildingCode': building_code,
            'floorCode': floor_code
        })
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_room_surplus(self, area_id, building_code, floor_code, room_code):
        data = self._request('queryRoomSurplus', {
            'areaId': area_id,
            'buildingCode': building_code,
            'floorCode': floor_code,
            'roomCode': room_code
        })
        if data.get('success'):
            return {
                'error': 0,
                'data': {
                    'surplus': data['data']['amount'],
                    'roomName': data['data']['displayRoomName']
                }
            }
        return self._error_response(data)

    def _error_response(self, data):
        return {
            'error': 1,
            'error_description': self._errcode(data.get('statusCode', 0))
        }

    def _errcode(self, code):
        return {
            233: 'shiroJID无效',
        }.get(code, '未知错误')

    def _request(self, uri, params):
        url = f'https://application.xiaofubao.com/app/electric/{uri}'
        params.update({
            'ymId': self.config['ymId'],
            'platform': 'YUNMA_APP'
        })
        headers = {
            'Cookie': f'shiroJID={self.config["shiroJID"]}'
        }
        
        try:
            response = requests.post(
                url,
                params=params,
                headers=headers,
                #verify=False
            )
            return response.json()
        except Exception as e:
            print(f"Request Error: {e}")
            return {'success': False}
        
    def check_and_alert(self, room_info, recipients,  threshold=None): #邮箱发送检查
        """
        检查电费余额并发送告警邮件
        :param room_info: query_room_surplus返回的房间信息
        :param recipients: 收件人列表
        :param threshold: 自定义阈值（可选）
        """
        if room_info['error'] != 0:
            print("错误：无法获取有效的房间信息")
            return False

        surplus = float(room_info['data']['surplus'])
        #threshold = threshold or self.config.get('alert_threshold', 30.0)

        #if surplus < threshold:
        subject = f"欧尼酱！电费告警！余额不足喵！"
        content = f"""
        moooooooooo！！！~~~欧尼酱是笨蛋！！！电费都忘记充了！
        诶~！欧尼酱要是没有我该怎么办呀！！！~~~
        欧尼酱の房间名称：{room_info['data']['roomName']}
        当前余额：{surplus} 元
        告警阈值：{threshold} 元
        
        及时给钱喵！
        欧尼酱要是因为没有我而停电了，那真是太可悲了喵！
        请你照顾好自己喵！呜呜呜呜呜~~~~~~~~~~~
                                    ————爱你的妹妹！
        """
        return self.send_alert(subject, content, recipients)
        #return False

    def send_alert(self, subject, content, recipients): #发送邮箱
        """
        发送告警邮件
        :param subject: 邮件主题
        :param content: 邮件内容
        :param recipients: 收件人列表
        """
        try:
            # 根据配置选择连接方式
            if self.config.get('use_tls', False):
                server = smtplib.SMTP(
                    host=self.config['smtp_server'],
                    port=self.config['smtp_port'],
                    timeout=15
                )
                server.starttls()  # 启用TLS加密
            else:
                server = smtplib.SMTP_SSL(
                    host=self.config['smtp_server'],
                    port=self.config['smtp_port'],
                    timeout=15
                )

            server.login(self.config['smtp_user'], self.config['smtp_pass'])
            # 构造符合RFC标准的邮件
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8').encode()
            msg['From'] = formataddr((Header('电费监控系统', 'utf-8').encode(), self.config['from_email']))
            msg['To'] = ', '.join(recipients)
            
            server.sendmail(self.config['from_email'], recipients, msg.as_string())
            print("发送成功")
            return True
        except smtplib.SMTPServerDisconnected as e:
            print(f"服务器意外断开: {str(e)}")
            print("可能原因:1.认证失败 2.超时 3.协议不匹配")
            return False
        except Exception as e:
            print(f"其他错误: {str(e)}")
            return False

# 使用示例
if __name__ == "__main__":
    config = {
        'shiroJID': 'df8bde3a-06e5-435d-b7a8-1026e4d8c331',
        'ymId': '2502567889956864141',
        # 邮件服务器配置
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465,  # 使用SSL端口
        'smtp_user': '@qq.com',
        'smtp_pass': 'kankexbbwiakjhdj',  # 授权码
        'from_email': '@qq.com',
        'alert_threshold': 20.0  # 自定义全局阈值
    }
    threshold = 200.0
    while(1):
        ece = ECampusElectricity(config)
        
        # 收件人列表
        recipients = ['@outlook.com', '@qq.com']
    
        # 获取校区
        area_info = ece.query_area()
        area_id = area_info['data'][0]['id'] #西校区
        
        area_info = ece.query_area()
        area_id = area_info['data'][1]['id'] #东校区
        
        # 获取宿舍楼
        building_list = ece.query_building(area_id)
        building_code = building_list['data'][14]['buildingCode'] #D9东
        
        #building_list = ece.query_building(area_id)
        #building_code = building_list['data'][34]['buildingCode'] #f10南
        
        # 获取楼层
        floor_list = ece.query_floor(area_id, building_code)
        floor_code = floor_list['data'][3]['floorCode'] #F4
        
        
        # 获取房间
        room_list = ece.query_room(area_id, building_code, floor_code)
        room_code = room_list['data'][24]['roomCode'] #x25
        
        # 获取电费信息
        room_info = ece.query_room_surplus(area_id, building_code, floor_code, room_code)
        surplus = room_info['data']['surplus']
        name = room_info['data']['roomName']
        
        print(f'房间：{name} 当前余额：{surplus}')
        if(surplus < threshold):
            # 检查余额并发送告警（使用全局阈值）
            ece.check_and_alert(room_info, recipients)
        sleep(3600)