from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from extensions import db
from auth.forms import RegisterForm, LoginForm, SellForm, ReviewForm, PayForm
import sqlalchemy.exc
import bcrypt
import uuid
from datetime import datetime, timedelta
from extensions import db
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import case

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# 默认路由重定向到登录
@app.route('/')
def index_redirect():
    return redirect(url_for('login'))

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        from models import Buyer, Seller, Admin
        if Buyer.query.filter_by(UserID=current_user.UserID).first():
            return redirect(url_for('index'))
        elif Seller.query.filter_by(UserID=current_user.UserID).first():
            return redirect(url_for('index'))
        elif Admin.query.filter_by(UserID=current_user.UserID).first():
            return redirect(url_for('admin'))
    
    form = LoginForm()
    if form.validate_on_submit():
        from models import User, Buyer, Seller, Admin
        try:
            user = User.query.filter_by(手机号=form.手机号.data).first()
            if not user:
                app.logger.warning(f'登录失败: 用户不存在 - 手机号: {form.手机号.data}')
                flash('手机号或密码错误', 'error')
                return render_template('login.html', form=form)
            
            # 调试密码验证
            input_pw = form.密码.data.encode('utf-8')
            stored_pw = user.密码.encode('utf-8')
            pw_match = bcrypt.checkpw(input_pw, stored_pw)
            
            app.logger.debug(f'密码验证: 输入: {input_pw}, 存储: {stored_pw}, 结果: {pw_match}')
            
            if not pw_match:
                app.logger.warning(f'登录失败: 密码错误 - 用户: {user.UserID}')
                flash('手机号或密码错误', 'error')
                return render_template('login.html', form=form)
            
            # 验证角色
            role = form.角色.data
            is_buyer = Buyer.query.filter_by(UserID=user.UserID).first()
            is_seller = Seller.query.filter_by(UserID=user.UserID).first()
            is_admin = Admin.query.filter_by(UserID=user.UserID).first()
            
            if (role == '买家' and not is_buyer) or \
               (role == '卖家' and not is_seller) or \
               (role == '管理员' and not is_admin):
                app.logger.warning(f'角色不匹配: 用户: {user.UserID}, 选择角色: {role}')
                flash('角色选择错误，请选择正确的用户角色', 'error')
                return render_template('login.html', form=form)
            
            # 登录成功
            login_user(user)
            app.logger.info(f'登录成功: 用户: {user.UserID}, 角色: {role}')
            flash(f'欢迎回来, {user.姓名}!', 'success')
            
            if role == '管理员':
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
            
        except Exception as e:
            app.logger.error(f'登录过程中出错: {str(e)}')
            flash('登录过程中发生错误，请重试', 'error')
            return render_template('login.html', form=form)
    
    # 显示表单验证错误
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text} {error}', 'error')
    
    return render_template('login.html', form=form)

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        from models import Buyer, Seller, Admin
        if Buyer.query.filter_by(UserID=current_user.UserID).first():
            return redirect(url_for('index'))
        elif Seller.query.filter_by(UserID=current_user.UserID).first():
            return redirect(url_for('index'))
        elif Admin.query.filter_by(UserID=current_user.UserID).first():
            return redirect(url_for('admin'))
    form = RegisterForm()
    if form.validate_on_submit():
        # 开始事务
        from models import User, Buyer, Seller, Admin
        if User.query.filter_by(学号=form.学号.data).first():
            flash('学号已存在', 'error')
            return render_template('register.html', form=form)
        if User.query.filter_by(手机号=form.手机号.data).first():
            flash('手机号已注册', 'error')
            return render_template('register.html', form=form)
        user_id = str(uuid.uuid4())
        hashed_password = bcrypt.hashpw(form.密码.data.encode('utf-8'), bcrypt.gensalt())
        user = User(
            UserID=user_id,
            学号=form.学号.data,
            姓名=form.姓名.data,
            手机号=form.手机号.data,
            密码=hashed_password.decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        # 事务提交成功
        role = form.角色.data
        if role == '买家':
            buyer = Buyer(UserID=user_id)
            db.session.add(buyer)
        elif role == '卖家':
            seller = Seller(UserID=user_id, 证件号='ID' + form.学号.data, 实名状态='未实名')
            db.session.add(seller)
        elif role == '管理员':
            admin = Admin(UserID=user_id)
            db.session.add(admin)
        db.session.commit()
        # 事务提交成功
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# 主页
@app.route('/index')
def index():
    try:
        from models import Product, Category, Buyer, Seller
        search_query = request.args.get('search', '')
        category_id = request.args.get('category', default=None, type=int)
        query = db.session.query(Product, Seller)\
            .join(Seller, Product.卖家_UserID == Seller.UserID)\
            .filter(Product.审核状态 == '已审核')
        if search_query:
            query = query.filter(Product.名称.contains(search_query))
        if category_id:
            query = query.filter(Product.CategoryID == category_id)
        results = query.all()
        products = []
        for product, seller in results:
            products.append({
                'product': product,
                'seller': seller
            })
        categories = Category.query.all()
        is_buyer = current_user.is_authenticated and Buyer.query.filter_by(UserID=current_user.UserID).first()
        is_seller = current_user.is_authenticated and Seller.query.filter_by(UserID=current_user.UserID).first()
        return render_template('index.html', 
                             products=products, 
                             categories=categories,
                             search_query=search_query, 
                             current_category=category_id,
                             is_buyer=is_buyer,
                             is_seller=is_seller)
    except sqlalchemy.exc.OperationalError:
        return render_template('index.html', error='数据库连接失败，请检查 MySQL 服务')

# 售出商品
@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    from models import Seller, Category
    if not Seller.query.filter_by(UserID=current_user.UserID).first():
        flash('仅卖家可发布商品', 'error')
        return redirect(url_for('index'))
    form = SellForm()
    categories = Category.query.all()
    form.分类.choices = [(c.CategoryID, c.分类名称) for c in categories]
    
    if form.validate_on_submit():
        from models import Product, Category
        product_id = str(uuid.uuid4())
        
        # 处理自定义分类
        category_id = form.分类.data
        if category_id == '8':  # 假设"其他"是第8个选项
            custom_name = request.form.get('custom_category', '').strip()
            if custom_name:
                # 创建新分类
                new_category = Category(分类名称=custom_name)
                db.session.add(new_category)
                db.session.flush()  # 获取新分类ID
                category_id = new_category.CategoryID
        
        product = Product(
            ProductID=product_id,
            名称=form.名称.data,
            描述=form.描述.data,
            价格=form.价格.data,
            上架时间=datetime.utcnow(),
            审核状态='待审核',
            CategoryID=category_id,
            卖家_UserID=current_user.UserID
        )
        db.session.add(product)
        db.session.commit()
        flash('商品已提交，待审核', 'success')
        return redirect(url_for('index'))
    return render_template('sell.html', form=form)

# 购买商品
@app.route('/buy/<product_id>', methods=['POST'])
@login_required
def buy(product_id):
    from models import Product, Buyer, Order
    if not Buyer.query.filter_by(UserID=current_user.UserID).first():
        flash('仅买家可购买商品', 'error')
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    if product.审核状态 != '已审核' or product.买家_UserID:
        flash('商品不可购买', 'error')
        return redirect(url_for('index'))
    order_id = str(uuid.uuid4())[:32]
    order = Order(
        OrderID=order_id,
        UserID=current_user.UserID,
        总金额=product.价格,
        交易状态='待付款',
        ProductID=product.ProductID
    )
    product.买家_UserID = current_user.UserID
    db.session.add(order)
    db.session.commit()
    # 事务提交成功
    flash('订单已生成，请支付', 'success')
    return redirect(url_for('pay', order_id=order_id))

# 付款
@app.route('/pay/<order_id>', methods=['GET', 'POST'])
@login_required
def pay(order_id):
    from models import Order, Product, Buyer
    if not Buyer.query.filter_by(UserID=current_user.UserID).first():
        flash('仅买家可访问', 'error')
        return redirect(url_for('index'))
    order = Order.query.get_or_404(order_id)
    if order.UserID != current_user.UserID:
        flash('无权访问此订单', 'error')
        return redirect(url_for('index'))
    product = Product.query.filter_by(买家_UserID=current_user.UserID).first()
    if not product:
        flash('未找到相关商品', 'error')
        return redirect(url_for('index'))
    form = PayForm()
    if form.validate_on_submit():
        try:
            # 开始事务
            if order.交易状态 != '待付款':
                flash('订单已支付或状态异常', 'error')
                return redirect(url_for('index'))
            order.交易状态 = '已付款'
            product = Product.query.get(order.ProductID)
            if product:
                product.审核状态 = '已售出'
            db.session.commit()
            # 事务提交成功
            app.logger.info(f'支付成功: OrderID={order_id}, UserID={current_user.UserID}')
            flash('支付成功，请对商品进行评价', 'success')
            return redirect(url_for('review', order_id=order_id))
        except sqlalchemy.exc.OperationalError as e:
            db.session.rollback()
            # 事务回滚
            app.logger.error(f'支付失败: {str(e)}')
            flash('支付失败，请重试', 'error')
            return redirect(url_for('index'))
    return render_template('pay.html', form=form, order=order, product=product)

# 评价订单
@app.route('/review/<order_id>', methods=['GET', 'POST'])
@login_required
def review(order_id):
    from models import Order, Review, Buyer, Product
    if not Buyer.query.filter_by(UserID=current_user.UserID).first():
        flash('仅买家可评价', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    if order.UserID != current_user.UserID:
        flash('无权评价此订单', 'error')
        return redirect(url_for('index'))
    
    if order.交易状态 != '已付款':
        flash('只有已付款订单可以评价', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.filter_by(买家_UserID=current_user.UserID).first()
    if not product:
        flash('未找到相关商品', 'error')
        return redirect(url_for('index'))
    
    if Review.query.filter_by(OrderID=order_id).first():
        flash('该订单已评价过', 'error')
        return redirect(url_for('order_history'))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            OrderID=order_id,
            评分=form.评分.data,
            评论文本=form.评论文本.data
        )
        db.session.add(review)
        db.session.commit()
        flash('评价已提交', 'success')
        return redirect(url_for('order_history'))
    
    return render_template('review.html', form=form, order_id=order_id)

# 订单历史
@app.route('/order_history')
@login_required
def order_history():
    from models import Order, Buyer, Product
    if not Buyer.query.filter_by(UserID=current_user.UserID).first():
        flash('仅买家可查看订单历史', 'error')
        return redirect(url_for('index'))
    
    orders = Order.query\
        .filter_by(UserID=current_user.UserID)\
        .options(db.joinedload(Order.product))\
        .order_by(Order.创建时间.desc())\
        .all()
    
    return render_template('order_history.html', orders=orders)

@app.route('/order_detail/<order_id>')
@login_required
def order_detail(order_id):
    from models import Order, Buyer, Product
    if not Buyer.query.filter_by(UserID=current_user.UserID).first():
        flash('仅买家可查看订单详情', 'error')
        return redirect(url_for('index'))
    
    order = Order.query\
        .options(db.joinedload(Order.product))\
        .options(db.joinedload(Order.reviews))\
        .get_or_404(order_id)
    
    if order.UserID != current_user.UserID:
        flash('无权查看此订单', 'error')
        return redirect(url_for('index'))
        
    return render_template('order_detail.html', order=order)

# 评价中心功能已禁用
# @app.route('/review_center')
# @login_required
# def review_center():
#     from models import Review, Buyer
#     buyer = Buyer.query.filter_by(UserID=current_user.UserID).first()
#     if not buyer:
#         flash('仅买家可查看评价中心', 'error')
#         return redirect(url_for('index'))
#    
#     reviews = Review.query.filter_by(用户ID=current_user.UserID)\
#                         .join(Review.order)\
#                         .join(Review.user)\
#                         .order_by(Review.timestamp.desc())\
#                         .all()
#     return render_template('review_center.html', reviews=reviews)

@app.route('/seller/orders')
@login_required
def seller_orders():
    from models import Order, Seller, Product, Buyer, User
    seller = Seller.query.filter_by(UserID=current_user.UserID).first()
    if not seller:
        flash('仅卖家可查看商品订单', 'error')
        return redirect(url_for('index'))
    
    status = request.args.get('status', '')
    query = db.session.query(Order, User)\
        .join(Product, Order.ProductID == Product.ProductID)\
        .join(Buyer, Order.UserID == Buyer.UserID)\
        .join(User, Buyer.UserID == User.UserID)\
        .filter(Product.卖家_UserID == current_user.UserID)\
        .options(db.joinedload(Order.product))
    
    if status:
        query = query.filter(Order.交易状态 == status)
    
    results = query.order_by(Order.创建时间.desc()).all()
    # 将查询结果转换为可以直接访问属性的对象
    orders = []
    for order, user in results:
        order_dict = {
            'OrderID': order.OrderID,
            'product': {
                '名称': order.product.名称,
                '价格': order.product.价格
            },
            '总金额': order.总金额,
            '交易状态': order.交易状态,
            '创建时间': order.创建时间,
            'buyer': {
                '姓名': user.姓名,
                '学号': user.学号
            },
            'reviews': order.reviews
        }
        orders.append(order_dict)
    return render_template('seller_orders.html', orders=orders)

@app.route('/seller/order/<order_id>')
@login_required
def seller_order_detail(order_id):
    from models import Order, Seller, Product, Buyer, User
    seller = Seller.query.filter_by(UserID=current_user.UserID).first()
    if not seller:
        flash('仅卖家可查看订单详情', 'error')
        return redirect(url_for('index'))
    
    order, buyer, buyer_info = db.session.query(Order, User, Buyer)\
        .join(Product, Order.ProductID == Product.ProductID)\
        .join(Buyer, Order.UserID == Buyer.UserID)\
        .join(User, Buyer.UserID == User.UserID)\
        .options(db.joinedload(Order.product))\
        .options(db.joinedload(Order.reviews))\
        .filter(Order.OrderID == order_id,
               Product.卖家_UserID == current_user.UserID)\
        .first_or_404()
    
    # 构造包含买家信息的order_dict
    order_dict = {
        'OrderID': order.OrderID,
        '总金额': order.总金额,
        '交易状态': order.交易状态,
        '创建时间': order.创建时间,
        'product': order.product,
        'reviews': order.reviews,
        'buyer': {
            '姓名': buyer.姓名,
            '学号': buyer.学号,
            '手机号': buyer.手机号,
            '实名状态': buyer_info.实名状态
        }
    }
    
    return render_template('seller_order_detail.html', order=order_dict)

# 管理员仪表板
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    from models import Admin, Product
    from auth.forms import AdminReviewForm
    if not Admin.query.filter_by(UserID=current_user.UserID).first():
        flash('仅管理员可访问', 'error')
        return redirect(url_for('index'))
    
    form = AdminReviewForm()
    products = Product.query.order_by(Product.上架时间.desc()).all()
    
    if form.validate_on_submit():
        product = Product.query.get(request.form.get('product_id'))
        if product:
            product.审核状态 = form.审核状态.data
            db.session.commit()
            flash('审核状态已更新', 'success')
        return redirect(url_for('admin'))
    
    return render_template('admin.html', products=products, form=form)

# 实名审批页面
@app.route('/admin/approval')
@login_required
def admin_approval():
    from models import Admin, User, Seller, Buyer
    if not Admin.query.filter_by(UserID=current_user.UserID).first():
        flash('仅管理员可访问', 'error')
        return redirect(url_for('index'))
    
    # 获取筛选条件
    role_filter = request.args.get('role', 'all')
    
    # 获取所有用户信息，确保实名状态不为空
    # 获取所有非管理员用户
    admin_ids = [admin.UserID for admin in Admin.query.all()]
    query = db.session.query(
        User,
        db.func.coalesce(
            case(
                (Seller.UserID.isnot(None), Seller.实名状态),
                (Buyer.UserID.isnot(None), Buyer.实名状态),
                else_='未实名'
            )
        ).label('status'),
        db.func.coalesce(Seller.证件号, 'N/A').label('id_number'),
        db.func.coalesce(Seller.UserID.isnot(None), False).label('is_seller'),
        db.func.coalesce(Buyer.UserID.isnot(None), False).label('is_buyer')
    ).outerjoin(Seller, User.UserID == Seller.UserID)\
     .outerjoin(Buyer, User.UserID == Buyer.UserID)\
     .filter(User.UserID.notin_(admin_ids))  # 排除管理员
    
    # 应用筛选条件
    if role_filter == 'seller':
        query = query.filter(Seller.UserID.isnot(None))
    elif role_filter == 'buyer':
        query = query.filter(Buyer.UserID.isnot(None))
    
    users = query.order_by(User.学号).all()
    
    return render_template('admin_approval.html', users=users)

# 审批通过
@app.route('/admin/approve/<user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    from models import Admin, Seller, Buyer
    if not Admin.query.filter_by(UserID=current_user.UserID).first():
        flash('仅管理员可操作', 'error')
        return redirect(url_for('index'))
    
    try:
        # 开始事务
        seller = Seller.query.get(user_id)
        if seller:
            seller.实名状态 = '已实名'
        else:
            buyer = Buyer.query.get(user_id)
            if buyer:
                buyer.实名状态 = '已实名'
        db.session.commit()
        # 事务提交成功
        flash('实名认证已通过', 'success')
    except Exception as e:
        db.session.rollback()
        # 事务回滚
        app.logger.error(f'审批失败: {str(e)}')
        flash('审批失败，请重试', 'error')
    return redirect(url_for('admin_approval'))

# 审批拒绝
@app.route('/admin/reject/<user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    from models import Admin, Seller, Buyer
    if not Admin.query.filter_by(UserID=current_user.UserID).first():
        flash('仅管理员可操作', 'error')
        return redirect(url_for('index'))
    
    # 尝试获取卖家记录
    seller = Seller.query.get(user_id)
    if seller:
        seller.实名状态 = '校外人员'
        db.session.commit()
        app.logger.info(f'卖家标记为校外人员: {user_id}')
        flash('卖家已标记为校外人员', 'warning')
    else:
        # 尝试获取买家记录
        buyer = Buyer.query.get(user_id)
        if buyer:
            buyer.实名状态 = '校外人员'
            db.session.commit()
            app.logger.info(f'买家标记为校外人员: {user_id}')
            flash('买家已标记为校外人员', 'warning')
        else:
            app.logger.warning(f'拒绝审批用户不存在: {user_id}')
            flash('用户不存在', 'error')
    
    return redirect(url_for('admin_approval'))

# 商品列表 API
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        from models import Product, Admin
        from sqlalchemy.orm import joinedload
        is_admin = current_user.is_authenticated and Admin.query.filter_by(UserID=current_user.UserID).first()
        search_query = request.args.get('search', '')
        category_id = request.args.get('category', default=None, type=int)
        if is_admin:
            query = Product.query.options(joinedload(Product.Category))
        else:
            query = Product.query.filter_by(审核状态='已审核').options(joinedload(Product.Category))
        if search_query:
            query = query.filter(Product.名称.contains(search_query))
        if category_id:
            query = query.filter_by(CategoryID=category_id)
        products = query.all()
        return jsonify([{
            'ProductID': p.ProductID,
            '名称': p.名称,
            '价格': float(p.价格),
            '分类': p.Category.分类名称 if p.Category else '无',
            '上架时间': p.上架时间.strftime('%Y-%m-%d'),
            '审核状态': p.审核状态,
            '买家_UserID': p.买家_UserID
        } for p in products])
    except sqlalchemy.exc.OperationalError:
        return jsonify({'error': '数据库连接失败'}), 500

# 退出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('login'))

@app.route('/order/cancel/<order_id>')
@login_required
def cancel_order(order_id):
    """取消订单"""
    from models import Order, Product
    order = Order.query.get_or_404(order_id)
    
    if order.UserID != current_user.UserID:
        flash('无权取消此订单', 'error')
        return redirect(url_for('index'))
    
    if order.交易状态 != '待付款':
        flash('只有待付款订单可以取消', 'error')
        return redirect(url_for('index'))
    
    try:
        # 开始事务
        product = Product.query.get(order.ProductID)
        if product:
            product.买家_UserID = None
            product.审核状态 = '已审核'
        db.session.delete(order)
        db.session.commit()
        # 事务提交成功
        flash('订单已取消', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        # 事务回滚
        app.logger.error(f'取消订单失败: {str(e)}')
        flash('取消订单失败', 'error')
        return redirect(url_for('pay', order_id=order_id))

@app.route('/product/<product_id>')
def product_detail(product_id):
    """商品详情页"""
    from models import Product, Seller, Buyer
    product, seller = db.session.query(Product, Seller)\
        .join(Seller, Product.卖家_UserID == Seller.UserID)\
        .filter(Product.ProductID == product_id)\
        .first_or_404()
    
    # 判断当前用户角色
    is_buyer = False
    is_seller = False
    if current_user.is_authenticated:
        is_buyer = Buyer.query.filter_by(UserID=current_user.UserID).first() is not None
        is_seller = Seller.query.filter_by(UserID=current_user.UserID).first() is not None
    
    return render_template('product_detail.html', 
                         product=product,
                         seller=seller,
                         is_buyer=is_buyer,
                         is_seller=is_seller)

def check_expired_orders():
    """检查并处理超时未支付的订单"""
    from models import Order, Product
    with app.app_context():
        try:
            # 开始事务
            expired_time = datetime.utcnow() - timedelta(minutes=5)
            expired_orders = Order.query.filter(
                Order.交易状态 == '待付款',
                Order.创建时间 < expired_time
            ).all()
            
            for order in expired_orders:
                # 恢复商品状态
                product = Product.query.get(order.ProductID)
                if product:
                    product.买家_UserID = None
                    product.审核状态 = '已审核'
                    app.logger.info(f'恢复商品状态: ProductID={product.ProductID}')
                
                # 更新订单状态为已取消
                order.交易状态 = '已取消'
                app.logger.info(f'标记订单为已取消: OrderID={order.OrderID}')
            
            if expired_orders:
                db.session.commit()
                # 事务提交成功
                app.logger.info(f'已处理{len(expired_orders)}个超时订单')
        except Exception as e:
            db.session.rollback()
            # 事务回滚
            app.logger.error(f'取消超时订单失败: {str(e)}')

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_expired_orders,
    trigger='interval',
    minutes=5,
    id='order_check_job'
)

if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True, host='127.0.0.1', port=8080)

# 项目主入口，所有路由和业务逻辑都在这里