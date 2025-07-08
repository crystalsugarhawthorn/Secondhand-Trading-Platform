import datetime
from extensions import db
from flask_login import UserMixin

# ORM模型定义，对应数据库所有表

class User(db.Model, UserMixin):
    __tablename__ = '用户'
    UserID = db.Column(db.String(36), primary_key=True)  # 用户唯一标识
    学号 = db.Column(db.String(20), nullable=False, unique=True)  # 学号
    姓名 = db.Column(db.String(50), nullable=False)  # 姓名
    手机号 = db.Column(db.String(11), nullable=False)  # 手机号
    密码 = db.Column(db.String(255), nullable=False)  # 密码（加密存储）

    def get_id(self):
        return self.UserID

class Buyer(db.Model):
    __tablename__ = '买家'
    UserID = db.Column(db.String(36), db.ForeignKey('用户.UserID', ondelete='CASCADE'), primary_key=True)
    实名状态 = db.Column(db.Enum('未实名', '已实名', '校外人员'), nullable=False, default='未实名')

class Seller(db.Model):
    __tablename__ = '卖家'
    UserID = db.Column(db.String(36), db.ForeignKey('用户.UserID', ondelete='CASCADE'), primary_key=True)
    证件号 = db.Column(db.String(20), nullable=False, unique=True)
    实名状态 = db.Column(db.Enum('未实名', '已实名', '校外人员'), nullable=False, default='未实名')

class Admin(db.Model):
    __tablename__ = '管理员'
    UserID = db.Column(db.String(36), db.ForeignKey('用户.UserID', ondelete='CASCADE'), primary_key=True)

class Category(db.Model):
    __tablename__ = '商品分类'
    CategoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    分类名称 = db.Column(db.String(50), nullable=False)

class Product(db.Model):
    __tablename__ = '商品'
    ProductID = db.Column(db.String(36), primary_key=True)
    名称 = db.Column(db.String(100), nullable=False)
    描述 = db.Column(db.Text)
    价格 = db.Column(db.DECIMAL(12, 2), nullable=False)
    上架时间 = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    审核状态 = db.Column(db.Enum('待审核', '已审核', '未通过', '已售出'), nullable=False, default='待审核')
    CategoryID = db.Column(db.Integer, db.ForeignKey('商品分类.CategoryID', ondelete='SET NULL'))
    卖家_UserID = db.Column(db.String(36), db.ForeignKey('卖家.UserID', ondelete='CASCADE'), nullable=False)
    买家_UserID = db.Column(db.String(36), db.ForeignKey('买家.UserID', ondelete='SET NULL'))

class Review(db.Model):
    __tablename__ = '评价'
    ReviewID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OrderID = db.Column(db.String(32), db.ForeignKey('订单.OrderID', ondelete='SET NULL'))
    用户ID = db.Column(db.String(36), db.ForeignKey('买家.UserID', ondelete='SET NULL'))
    评分 = db.Column(db.SmallInteger, nullable=False)
    评论文本 = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    order = db.relationship('Order', backref=db.backref('reviews'))
    user = db.relationship('Buyer', backref=db.backref('reviews'))

class Order(db.Model):
    __tablename__ = '订单'
    OrderID = db.Column(db.String(32), primary_key=True)
    UserID = db.Column(db.String(36), db.ForeignKey('买家.UserID', ondelete='CASCADE'), nullable=False)
    总金额 = db.Column(db.DECIMAL(12, 2), nullable=False)
    交易状态 = db.Column(db.Enum('待付款', '已付款', '已完成', '已取消'), nullable=False, default='待付款')
    ProductID = db.Column(db.String(36), db.ForeignKey('商品.ProductID', ondelete='SET NULL'))
    创建时间 = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    product = db.relationship('Product', backref=db.backref('orders'))
    user = db.relationship('Buyer', backref=db.backref('orders'))