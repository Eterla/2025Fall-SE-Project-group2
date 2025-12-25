# app/exceptions.py
class UsernameTakenError(Exception):
    """用户名已存在异常"""
    pass

class InvalidPasswordError(Exception):
    """原密码错误异常"""
    pass