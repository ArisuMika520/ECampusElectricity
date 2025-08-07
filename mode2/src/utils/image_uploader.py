'''
图片上传图床的脚本

Build by ArisuMika
'''
import requests
import os
import json
import logging

_log = logging.getLogger(__name__)

class ImageUploader:
    """
    与图床 API 交互的工具类。
    - 按寝室管理图片，实现旧图删除、新图上传。
    - 自动记录每个寝室最后一次上传的图片信息。
    * **注意：** 本类请详细跟据具体图床的API文档进行修改！！！可能需要大重构
    """
    def __init__(self, token: str, album_id: int, record_file_path: str):
        """
        初始化上传器。
        """
        self.base_url = ""
        if not token:
            raise ValueError("图床授权 Token 未在配置文件中正确配置。")
        # 以下自己跟据API修改
        # if not album_id:
        #     raise ValueError("图床相册 ID 未在配置文件中正确配置。")

        # self.album_id = album_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"{token}", # 跟据token请求格式自行修改
            "Accept": "" # 跟据token请求格式自行修改
        })
        self.record_file = record_file_path
        self._ensure_record_file()

    def _ensure_record_file(self):
        """确保记录文件及其所在目录存在。"""
        os.makedirs(os.path.dirname(self.record_file), exist_ok=True)
        if not os.path.exists(self.record_file):
            with open(self.record_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _read_records(self) -> dict:
        """
        安全地从记录文件中读取所有寝室的图片密钥。
        增加了对文件内容格式的健壮性检查。
        """
        try:
            with open(self.record_file, 'r', encoding='utf-8') as f:
                # 处理文件为空的情况
                content = f.read()
                if not content:
                    return {}
                data = json.loads(content)
            
            # 确保加载的数据是字典类型
            if not isinstance(data, dict):
                _log.warning(f"记录文件 '{self.record_file}' 格式不正确 (应为字典，实际为 {type(data).__name__})，已重置。")
                # 重置文件为一个空的字典
                self._write_records({})
                return {}
            
            return data
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果文件不存在或JSON损坏，返回一个空字典
            _log.warning(f"记录文件 '{self.record_file}' 不存在或损坏，将创建新文件。")
            return {}

    def _write_records(self, records: dict):
        """将更新后的记录写回文件。"""
        try:
            with open(self.record_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=4)
        except IOError as e:
            _log.error(f"写入图床记录文件 '{self.record_file}' 失败: {e}")

    def _get_key_for_room(self, room_name: str) -> str or None:
        """获取指定寝室上一次上传的图片密钥。"""
        return self._read_records().get(room_name)

    def _save_key_for_room(self, room_name: str, key: str):
        """为指定寝室保存新的图片密钥。"""
        records = self._read_records()
        records[room_name] = key
        self._write_records(records)
        _log.info(f"已为寝室「{room_name}」保存新的图片密钥: {key}")

    def _delete_image_by_key(self, key: str) -> bool:
        """根据密钥删除图片。"""
        if not key:
            _log.info("没有提供图片密钥，跳过删除。")
            return True
        
        _log.info(f"正在尝试删除旧图片，密钥: {key}...")
        delete_url = f"{self.base_url}/images/{key}"
        try:
            response = self.session.delete(delete_url)
            response.raise_for_status()
            res_json = response.json()
            if res_json.get('status'):
                _log.info(f"成功删除旧图片: {res_json.get('message')}")
                return True
            else:
                _log.warning(f"删除旧图片失败 (API): {res_json.get('message')}")
                return False
        except requests.exceptions.RequestException as e:
            _log.error(f"删除图片请求失败: {e}")
            return False

    def _upload_image_file(self, file_path: str) -> dict or None:
        """上传单个图片文件。"""
        if not os.path.exists(file_path):
            _log.error(f"待上传的图片文件不存在: {file_path}")
            return None

        upload_url = f"{self.base_url}/upload"
        files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
        data = {'album_id': self.album_id}

        _log.info(f"正在上传新图片 '{os.path.basename(file_path)}'...")
        try:
            response = self.session.post(upload_url, files=files, data=data)
            response.raise_for_status()
            res_json = response.json()

            if res_json.get('status'):
                _log.info("图片上传成功!")
                image_data = res_json.get('data', {})
                image_key = image_data.get('key')
                image_url = image_data.get('links', {}).get('url')
                if image_key and image_url:
                    return {'key': image_key, 'url': image_url}
                else:
                    _log.error("上传成功，但 API 响应中缺少 key 或 url。")
                    return None
            else:
                _log.error(f"图片上传失败 (API): {res_json.get('message')}")
                return None
        except requests.exceptions.RequestException as e:
            _log.error(f"上传图片请求失败: {e}")
            return None
        finally:
            if 'file' in files:
                files['file'][1].close()
            
    def manage_upload(self, room_name: str, image_path: str) -> dict:
        """
        - 查找并删除与该寝室关联的旧图。
        - 上传新生成的图片。
        - 记录新图的密钥以备下次删除。
        - 删除本地的临时图片文件。
        """
        # 查找并删除旧图
        old_key = self._get_key_for_room(room_name)
        if old_key:
            self._delete_image_by_key(old_key)
        else:
            _log.info(f"寝室「{room_name}」没有旧图片记录，将直接上传新图。")

        # 上传新图
        upload_result = self._upload_image_file(image_path)
        if not upload_result:
            return {"code": 201, "info": "上传图片到图床失败，请检查网络或联系管理员。"}

        # 保存新图的密钥
        new_key = upload_result['key']
        new_url = upload_result['url']
        self._save_key_for_room(room_name, new_key)
        
        # 删除本地临时图片
        try:
            os.remove(image_path)
            _log.info(f"已删除本地临时图片: {image_path}")
        except OSError as e:
            _log.error(f"删除本地临时图片 '{image_path}' 失败: {e}")

        return {"code": 200, "info": "操作成功", "url": new_url}
