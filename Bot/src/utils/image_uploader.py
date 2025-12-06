"""
图片上传图床的工具类

Build by ArisuMika
"""
import json
import logging
import os
from typing import Optional
from urllib.parse import urljoin

import requests

_log = logging.getLogger(__name__)


class ImageUploader:
    """
    与 7bu 图床 API 交互的帮助类。
    - 负责按寝室管理图片，自动删除旧图、上传新图；
    - 维护一份上传记录，方便下次删除旧图。
    """

    DEFAULT_BASE_URL = ""

    def __init__(self, token: str, album_id: Optional[int], record_file_path: str, base_url: Optional[str] = None):
        if not token:
            raise ValueError("图床授权 Token 未在配置文件中正确配置。")

        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip('/') + '/'
        if not self.base_url.startswith("http"):
            raise ValueError("图床 base_url 配置错误，应包含协议头。")

        self.album_id = str(album_id) if album_id else None
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self._normalize_token(token),
            "Accept": "application/json"
        })

        self.record_file = record_file_path
        self._ensure_record_file()

    # ------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------
    def _normalize_token(self, token: str) -> str:
        token = token.strip()
        if not token.lower().startswith("bearer "):
            return f"Bearer {token}"
        return token

    def _make_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip('/'))

    def _ensure_record_file(self):
        os.makedirs(os.path.dirname(self.record_file), exist_ok=True)
        if not os.path.exists(self.record_file):
            with open(self.record_file, 'w', encoding='utf-8') as fp:
                json.dump({}, fp)

    def _read_records(self) -> dict:
        try:
            with open(self.record_file, 'r', encoding='utf-8') as fp:
                content = fp.read()
            if not content:
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                _log.warning(f"记录文件 '{self.record_file}' 结构异常，已重置。")
                self._write_records({})
                return {}
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            _log.warning(f"记录文件 '{self.record_file}' 丢失或损坏，已重新创建。")
            self._write_records({})
            return {}

    def _write_records(self, records: dict):
        with open(self.record_file, 'w', encoding='utf-8') as fp:
            json.dump(records, fp, ensure_ascii=False, indent=4)

    # ------------------------------------------------------------
    # 图床 API 相关
    # ------------------------------------------------------------
    def _get_key_for_room(self, room_name: str) -> Optional[str]:
        return self._read_records().get(room_name)

    def _save_key_for_room(self, room_name: str, key: str):
        records = self._read_records()
        records[room_name] = key
        self._write_records(records)
        _log.info(f"已记录寝室「{room_name}」最新图片 key: {key}")

    def _delete_image_by_key(self, key: str) -> bool:
        if not key:
            return True

        delete_url = self._make_url(f"/images/{key}")
        try:
            resp = self.session.delete(delete_url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get('status'):
                _log.info(f"成功删除旧图片: {key}")
                return True
            _log.warning(f"删除旧图片失败 (API): {data.get('message')}")
        except requests.RequestException as exc:
            _log.error(f"删除旧图片请求失败: {exc}")
        return False

    def _upload_image_file(self, file_path: str) -> Optional[dict]:
        if not os.path.exists(file_path):
            _log.error(f"待上传的图片文件不存在: {file_path}")
            return None

        upload_url = self._make_url('/upload')
        files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
        data = {'album_id': self.album_id} if self.album_id else {}

        _log.info(f"正在上传图片 '{os.path.basename(file_path)}'...")
        try:
            resp = self.session.post(upload_url, files=files, data=data, timeout=60)
            resp.raise_for_status()
            res_json = resp.json()
            if res_json.get('status'):
                image_data = res_json.get('data', {})
                key = image_data.get('key')
                url = image_data.get('links', {}).get('url')
                if key and url:
                    _log.info("图片上传成功。")
                    return {'key': key, 'url': url}
                _log.error("上传成功但响应缺少 key 或 url。")
            else:
                _log.error(f"图片上传失败 (API): {res_json.get('message')}")
        except requests.RequestException as exc:
            _log.error(f"上传图片请求失败: {exc}")
        finally:
            files['file'][1].close()

        return None

    # ------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------
    def manage_upload(self, room_name: str, image_path: str) -> dict:
        old_key = self._get_key_for_room(room_name)
        if old_key:
            self._delete_image_by_key(old_key)

        upload_result = self._upload_image_file(image_path)
        if not upload_result:
            return {"code": 201, "info": "上传图片到图床失败，请检查网络或联系管理员。"}

        new_key, new_url = upload_result['key'], upload_result['url']
        self._save_key_for_room(room_name, new_key)

        try:
            os.remove(image_path)
            _log.info(f"已删除本地临时图片: {image_path}")
        except OSError as exc:
            _log.error(f"删除本地临时图片失败: {exc}")

        return {"code": 200, "info": "操作成功", "url": new_url}
