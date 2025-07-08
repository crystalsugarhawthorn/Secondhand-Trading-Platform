# 密码哈希测试脚本，生成管理员密码哈希
import bcrypt
password = 'admin@1234'  # 确保与登录时输入的完全一致
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(hashed.decode('utf-8'))  # 复制这个新哈希到SQL中