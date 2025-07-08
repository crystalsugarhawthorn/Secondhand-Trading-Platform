# 南开大学二手闲置交易平台

---

## 项目简介
<!-- 项目介绍，功能说明 -->

本项目为南开大学校园二手闲置物品交易平台，基于 Flask 框架开发，支持买家、卖家、管理员三种角色，涵盖商品发布、审核、购买、支付、评价、实名审批等完整流程。前端采用 Jinja2 模板，界面风格贴合南开大学主题。

---

## 目录结构

```
Secondhand_Trading_Platform/
│
├── app.py                # 主程序入口，包含所有路由和业务逻辑
├── config.py             # Flask 配置文件
├── extensions.py         # Flask 扩展初始化（如 SQLAlchemy）
├── models.py             # 数据库模型定义
├── schema.sql            # MySQL 数据库建表及初始化脚本
├── requirements.txt      # Python 依赖包列表
├── test.py               # 密码哈希测试脚本
│
├── auth/
│   └── forms.py          # WTForms 表单定义
│
├── static/
│   ├── css/
│   │   └── style.css     # 前端样式表
│   └── js/
│       └── script.js     # 前端交互脚本
│
└── templates/
    ├── admin.html                # 管理员商品审核页面
    ├── admin_approval.html       # 管理员实名审批页面
    ├── index.html                # 首页/商品浏览
    ├── login.html                # 登录页面
    ├── order_detail.html         # 买家订单详情
    ├── order_history.html        # 买家订单历史
    ├── pay.html                  # 支付页面
    ├── product_detail.html       # 商品详情页
    ├── register.html             # 注册页面
    ├── review.html               # 订单评价页面
    ├── sell.html                 # 卖家发布商品页面
    ├── seller_order_detail.html  # 卖家订单详情
    └── seller_orders.html        # 卖家订单列表
```

---

## 环境依赖

- Python 3.8+
- MySQL 8.0+
- 推荐使用虚拟环境

### Python 依赖安装

```bash
pip install -r requirements.txt
```

### 数据库初始化

1. 创建数据库 `secondhand_trading`。
2. 使用 `schema.sql` 初始化表结构和基础数据：

    ```bash
    mysql -u root -p secondhand_trading < schema.sql
    ```

3. 修改 `config.py` 中的数据库连接信息为你的实际账号密码。

---

## 启动方法

1. 启动 MySQL 服务，确保数据库可用。
2. 运行主程序：

    ```bash
    python app.py
    ```

3. 访问 [http://127.0.0.1:8080](http://127.0.0.1:8080) 使用平台。

---

## 主要文件说明

### app.py

- **项目主入口**，包含所有 Flask 路由、业务逻辑、定时任务（订单超时自动取消）。
- 主要路由：
    - `/login` 登录
    - `/register` 注册
    - `/index` 商品浏览
    - `/sell` 发布商品
    - `/buy/<product_id>` 购买商品
    - `/pay/<order_id>` 支付订单
    - `/review/<order_id>` 订单评价
    - `/order_history` 买家订单历史
    - `/order_detail/<order_id>` 买家订单详情
    - `/seller/orders` 卖家订单列表
    - `/seller/order/<order_id>` 卖家订单详情
    - `/admin` 管理员商品审核
    - `/admin/approval` 管理员实名审批
    - `/admin/approve/<user_id>`、`/admin/reject/<user_id>` 实名审批操作
    - `/api/products` 商品API
    - `/logout` 退出登录
    - `/order/cancel/<order_id>` 取消订单
    - `/product/<product_id>` 商品详情
- **定时任务**：每5分钟自动取消超时未支付订单。

### config.py

- Flask 配置，包括数据库连接、密钥、SQLAlchemy参数等。

### extensions.py

- 初始化 Flask 扩展（如 SQLAlchemy）。

### models.py

- **ORM模型定义**，对应数据库所有表。
    - `User` 用户基础信息
    - `Buyer` 买家
    - `Seller` 卖家
    - `Admin` 管理员
    - `Category` 商品分类
    - `Product` 商品
    - `Order` 订单
    - `Review` 评价

### schema.sql

- MySQL 数据库建表脚本，包含所有表结构、外键、初始分类数据。

### requirements.txt

- Python 依赖包列表。

### test.py

- 用于生成 bcrypt 密码哈希，便于手动插入管理员等用户。

### auth/forms.py

- WTForms 表单定义：
    - `RegisterForm` 注册表单
    - `LoginForm` 登录表单
    - `SellForm` 发布商品表单
    - `AdminReviewForm` 管理员商品审核表单
    - `PayForm` 支付表单
    - `ReviewForm` 评价表单

### static/css/style.css

- 平台前端样式，包含主题色、响应式布局、卡片、按钮、表格、表单等样式。

### static/js/script.js

- 前端交互脚本，包括商品视图切换、订单倒计时、菜单切换等。

### templates/

- 所有前端页面模板，采用 Jinja2 语法，支持动态渲染。

---

## 主要函数/路由说明（app.py）

- `login()`：处理用户登录，校验手机号、密码、角色。
- `register()`：处理用户注册，支持买家/卖家/管理员角色。
- `index()`：商品浏览与搜索，支持分类筛选。
- `sell()`：卖家发布商品，支持自定义分类。
- `buy(product_id)`：买家购买商品，生成订单。
- `pay(order_id)`：订单支付，支付后商品状态变更。
- `review(order_id)`：买家对订单进行评价。
- `order_history()`：买家订单历史列表。
- `order_detail(order_id)`：买家订单详情。
- `seller_orders()`：卖家订单列表，支持状态筛选。
- `seller_order_detail(order_id)`：卖家订单详情。
- `admin()`：管理员商品审核，支持状态修改。
- `admin_approval()`：管理员实名审批页面，支持买家/卖家筛选。
- `approve_user(user_id)`/`reject_user(user_id)`：实名审批操作。
- `get_products()`：商品API，供前端动态刷新。
- `logout()`：退出登录。
- `cancel_order(order_id)`：买家取消订单，恢复商品状态。
- `product_detail(product_id)`：商品详情页。
- `check_expired_orders()`：定时任务，自动取消超时未支付订单。

---

## 常见问题

- **数据库连接失败**：请检查 MySQL 服务是否启动，`config.py` 数据库配置是否正确。
- **管理员初始密码**：可用 `test.py` 生成 bcrypt 哈希，插入数据库。
- **商品/订单状态异常**：请检查定时任务是否正常运行，或手动修正数据库状态。

---

## 贡献与许可

本项目仅供学习交流，禁止用于商业用途。欢迎同学们提出建议和改进！

