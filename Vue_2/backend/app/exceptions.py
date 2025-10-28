# app/exceptions.py
class UsernameTakenError(Exception):
    """用户名已存在异常"""
    pass