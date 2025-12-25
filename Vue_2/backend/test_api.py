import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_auth():
    """测试认证相关API"""
    print("=== 测试认证API ===")
    
    # 注册新用户
    register_data = {
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
        "phone": "1234567890"
    }
    
    print("\n1. 注册新用户:")
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 登录
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    
    print("\n2. 用户登录:")
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"状态码: {response.status_code}")
    login_response = response.json()
    print(f"响应: {json.dumps(login_response, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        token = login_response["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 获取当前用户信息
        print("\n3. 获取当前用户信息:")
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return token
    
    return None

def test_items(token):
    """测试商品相关API"""
    if not token:
        print("需要先登录获取token")
        return
    
    print("\n=== 测试商品API ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取商品
    print("\n1. 发布商品:")
    item_data = {
        "title": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99,
        "tags": "测试,示例"
    }
    
    # 使用表单数据上传（模拟文件上传）
    response = requests.post(
        f"{BASE_URL}/items", 
        data=item_data,
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    item_id = None
    if response.status_code == 201:
        item_id = response.json()["data"]["id"]
    
    # 获取商品列表
    print("\n2. 获取商品列表:")
    response = requests.get(f"{BASE_URL}/items")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 获取商品详情
    if item_id:
        print(f"\n3. 获取商品详情 (ID: {item_id}):")
        response = requests.get(f"{BASE_URL}/items/{item_id}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 获取用户发布的商品
    print("\n4. 获取用户发布的商品:")
    response = requests.get(f"{BASE_URL}/user/items", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_favorites(token):
    """测试收藏相关API"""
    if not token:
        print("需要先登录获取token")
        return
    
    print("\n=== 测试收藏API ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先获取一个商品ID
    print("\n1. 获取商品列表:")
    response = requests.get(f"{BASE_URL}/items")
    if response.status_code == 200:
        items = response.json()["data"]
        if items:
            item_id = items[0]["id"]
            
            # 添加收藏
            print(f"\n2. 添加收藏 (商品ID: {item_id}):")
            favorite_data = {"item_id": item_id}
            response = requests.post(f"{BASE_URL}/favorites", json=favorite_data, headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            # 获取收藏列表
            print("\n3. 获取收藏列表:")
            response = requests.get(f"{BASE_URL}/favorites", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            # 取消收藏
            print(f"\n4. 取消收藏 (商品ID: {item_id}):")
            response = requests.delete(f"{BASE_URL}/favorites/{item_id}", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_messages(token):
    """测试消息相关API"""
    if not token:
        print("需要先登录获取token")
        return
    
    print("\n=== 测试消息API ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先获取一个商品ID和另一个用户ID（这里简化测试，实际应该有多个用户）
    print("\n1. 获取商品列表:")
    response = requests.get(f"{BASE_URL}/items")
    if response.status_code == 200:
        items = response.json()["data"]
        if items:
            item_id = items[0]["id"]
            other_user_id = items[0]["seller_id"]
            
            # 发送消息
            print(f"\n2. 发送消息 (用户ID: {other_user_id}, 商品ID: {item_id}):")
            message_data = {
                "to_user_id": other_user_id,
                "item_id": item_id,
                "content": "您好，这个商品还在吗？"
            }
            
            response = requests.post(f"{BASE_URL}/messages", json=message_data, headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            # 获取消息列表
            print("\n3. 获取消息列表:")
            response = requests.get(f"{BASE_URL}/messages/conversations", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            # 获取聊天记录
            print(f"\n4. 获取聊天记录 (用户ID: {other_user_id}, 商品ID: {item_id}):")
            response = requests.get(f"{BASE_URL}/messages/conversations/{other_user_id}/{item_id}", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    print("开始测试API...")
    
    # 测试认证API
    token = test_auth()
    
    # 如果登录成功，继续测试其他API
    if token:
        test_items(token)
        test_favorites(token)
        test_messages(token)
    
    print("\nAPI测试完成！")
