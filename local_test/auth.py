import jwt
from datetime import datetime, timedelta

# JWT配置
JWT_SECRET = "douban-crawler-secret-key"
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 1

def generate_token(user_id):
    # 确保user_id是整数
    user_id = int(user_id)
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        # 直接返回整型 user_id
        return int(payload['user_id'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except (ValueError, TypeError):
        return None
