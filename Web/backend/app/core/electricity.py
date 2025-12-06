"""核心电费查询功能（从 Electricity.py 迁移）"""
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import requests
from typing import Optional, Dict, List, Any


class ECampusElectricity:
    """校园电费信息查询核心类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        使用配置初始化 ECampusElectricity
        
        Args:
            config: 配置字典，包含以下键：
                - shiroJID: 认证令牌
                - smtp_server: SMTP 服务器地址
                - smtp_port: SMTP 服务器端口
                - smtp_user: SMTP 用户名
                - smtp_pass: SMTP 密码
                - from_email: 发件人邮箱地址
                - use_tls: 是否使用 TLS（默认：False）
                - alert_threshold: 默认告警阈值（默认：20.0）
        """
        self.config = {
            'shiroJID': '',
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 465,
            'smtp_user': '',
            'smtp_pass': '',
            'from_email': '',
            'use_tls': False,
            'alert_threshold': 20.0
        }
        if config:
            self.config.update(config)

    def set_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)

    def school_info(self) -> Dict[str, Any]:
        """获取学校信息"""
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

    def query_area(self) -> Dict[str, Any]:
        """查询校区信息"""
        data = self._request('queryArea', {'type': 1})
        if data.get('success'):
            for item in data['rows']:
                item.pop('paymentChannel', None)
                item.pop('isBindAfterRecharge', None)
                item.pop('bindRoomNum', None)
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_building(self, area_id: str) -> Dict[str, Any]:
        """查询指定校区的楼栋信息"""
        data = self._request('queryBuilding', {'areaId': area_id})
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_floor(self, area_id: str, building_code: str) -> Dict[str, Any]:
        """查询指定楼栋的楼层信息"""
        data = self._request('queryFloor', {
            'areaId': area_id,
            'buildingCode': building_code
        })
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_room(self, area_id: str, building_code: str, floor_code: str) -> Dict[str, Any]:
        """查询指定楼层的房间信息"""
        data = self._request('queryRoom', {
            'areaId': area_id,
            'buildingCode': building_code,
            'floorCode': floor_code
        })
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_room_surplus(self, area_id: str, building_code: str, 
                          floor_code: str, room_code: str) -> Dict[str, Any]:
        """查询指定房间的电费余额"""
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

    def check_and_alert(self, room_info: Dict[str, Any], recipients: List[str], 
                       threshold: Optional[float] = None) -> bool:
        """
        检查电费余额并在需要时发送告警邮件
        
        Args:
            room_info: query_room_surplus 返回的房间信息
            recipients: 邮件收件人列表
            threshold: 自定义阈值（可选）
            
        Returns:
            发送告警返回 True，否则返回 False
        """
        if room_info.get('error') != 0:
            return False

        surplus = float(room_info['data']['surplus'])
        threshold = threshold or self.config.get('alert_threshold', 20.0)

        if surplus < threshold:
            subject = f"电费告警：{room_info['data']['roomName']} 余额不足"
            content = f"""
房间名称：{room_info['data']['roomName']}
当前余额：{surplus} 元
告警阈值：{threshold} 元

请及时充值！
"""
            return self.send_alert(subject, content, recipients)
        return False

    def send_alert(self, subject: str, content: str, recipients: List[str]) -> bool:
        """
        发送告警邮件
        
        Args:
            subject: 邮件主题
            content: 邮件内容
            recipients: 邮件收件人列表
            
        Returns:
            成功发送返回 True，否则返回 False
        """
        try:
            if self.config.get('use_tls', False):
                server = smtplib.SMTP(
                    host=self.config['smtp_server'],
                    port=self.config['smtp_port'],
                    timeout=15
                )
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(
                    host=self.config['smtp_server'],
                    port=self.config['smtp_port'],
                    timeout=15
                )

            server.login(self.config['smtp_user'], self.config['smtp_pass'])
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8').encode()
            msg['From'] = formataddr((
                Header('电费监控系统', 'utf-8').encode(),
                self.config['from_email']
            ))
            msg['To'] = ', '.join(recipients)
            
            server.sendmail(self.config['from_email'], recipients, msg.as_string())
            return True
        except smtplib.SMTPServerDisconnected as e:
            print(f"服务器意外断开: {str(e)}")
            print("可能原因:1.认证失败 2.超时 3.协议不匹配")
            return False
        except Exception as e:
            print(f"其他错误: {str(e)}")
            return False

    def _error_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成错误响应"""
        return {
            'error': 1,
            'error_description': self._errcode(data.get('statusCode', 0))
        }

    def _errcode(self, code: int) -> str:
        """根据错误代码获取错误描述"""
        error_codes = {
            233: 'shiroJID无效',
        }
        return error_codes.get(code, '未知错误')

    def _request(self, uri: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        向电费 API 发送 HTTP 请求
        
        Args:
            uri: API 端点 URI
            params: 请求参数
            
        Returns:
            响应数据字典
        """
        url = f'https://application.xiaofubao.com/app/electric/{uri}'
        params.update({
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
                timeout=30
            )
            return response.json()
        except Exception as e:
            print(f"Request Error: {e}")
            return {'success': False}



