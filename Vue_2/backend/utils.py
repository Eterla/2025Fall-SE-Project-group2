import os
import uuid
from flask import jsonify
from datetime import datetime

# 发送成功响应
# 格式: { "ok": true, "data": ... }
def make_response_ok(data=None, status_code=200):
    if status_code == 204:
        return ("", 204)
    return jsonify({"ok": True, "data": data}), status_code

# 发送错误响应
# 格式: { "ok": false, "error": { "code": ..., "message": ..., "details": ... } }
def error_response(code, message, details=None, status_code=400):
    body = {
        "ok": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    if details:
        body["error"]["details"] = details
    from flask import jsonify
    return jsonify(body), status_code

# 保存上传的文件并返回保存路径
def save_uploaded_file(file, upload_folder):
    os.makedirs(upload_folder, exist_ok=True) # 确保上传目录存在
    ext = os.path.splitext(file.filename)[1] # 获取文件扩展名
    filename = f"{uuid.uuid4().hex}{ext}" # 生成唯一文件名
    path = os.path.join(upload_folder, filename) # 构建保存路径
    file.save(path) # 保存文件
    return path.replace("\\", "/") # 返回相对路径，适应不同操作系统

# 获取当前时间的 ISO 格式字符串
def isoformat_now():
    return datetime.utcnow().isoformat() + 'Z'