# Flask配置文件，包含数据库连接、密钥等配置信息
class Config:
    # 数据库连接URI
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:050112@localhost/secondhand_trading'
    
    # 是否追踪对象的修改（一般设置为False以节省资源）
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 数据库引擎选项
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 10,        # 连接池超时时间（秒）
        'pool_recycle': 3600,      # 连接回收时间（秒）
        'pool_pre_ping': True      # 启用连接池的预检查功能
    }
    
    # 应用程序的密钥，用于加密会话等
    SECRET_KEY = 'my-secret-key'