from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
from time import sleep
import requests

class ECampusElectricity:
    def __init__(self, config=None):
        self.config = {
            'shiroJID': 'b8282b30-38d7-453f-883a-2df9f830cd4a',
            'ymId': '2407708335166238732',
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
    
    def get_myRoom(area,building,floor,room,ece):
        # 获取校区
        area_info = ece.query_area()
        area_id = area_info['data'][area]['id']
        # 获取宿舍楼
        building_list = ece.query_building(area_id)
        building_code = building_list['data'][building]['buildingCode']
        # 获取楼层
        floor_list = ece.query_floor(area_id, building_code)
        floor_code = floor_list['data'][floor]['floorCode']
        # 获取房间
        room_list = ece.query_room(area_id, building_code, floor_code)
        room_code = room_list['data'][room]['roomCode']
        # 获取电费信息
        room_info = ece.query_room_surplus(area_id, building_code, floor_code, room_code)
        surplus = room_info['data']['surplus']
        name = room_info['data']['roomName']
        return (surplus,name)
    

# 使用示例
if __name__ == "__main__":
    config = {
        'shiroJID': 'b8282b30-38d7-453f-883a-2df9f830cd4a',
        'ymId': '2407708335166238732',
        'alert_threshold': 20.0  # 自定义全局阈值
    }
    threshold = 20.0
    