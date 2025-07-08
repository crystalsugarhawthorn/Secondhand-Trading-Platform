/*==============================================================*/
/* DBMS name:      MySQL 8.0                                    */
/* Created on:     2025/5/14                                    */
/* Description:    Optimized schema for Secondhand_Trading_Platform */
/*==============================================================*/

-- 数据库建表及初始化脚本，所有表结构、外键、初始数据

-- 清理现有表
DROP TABLE IF EXISTS 评价;
DROP TABLE IF EXISTS 订单;
DROP TABLE IF EXISTS 商品;
DROP TABLE IF EXISTS 商品分类;
DROP TABLE IF EXISTS 买家;
DROP TABLE IF EXISTS 卖家;
DROP TABLE IF EXISTS 管理员;
DROP TABLE IF EXISTS 用户;

/*==============================================================*/
/* Table: 用户                                                    */
/*==============================================================*/
CREATE TABLE 用户 (
    UserID VARCHAR(36) NOT NULL COMMENT 'UUID格式用户ID',
    学号 VARCHAR(20) NOT NULL UNIQUE COMMENT '唯一学号',
    姓名 VARCHAR(50) NOT NULL,
    手机号 VARCHAR(11) NOT NULL,
    密码 VARCHAR(255) NOT NULL COMMENT '哈希密码',
    PRIMARY KEY (UserID),
    CHECK (手机号 REGEXP '^[0-9]{11}$')
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Table: 买家                                                    */
/*==============================================================*/
CREATE TABLE 买家 (
    UserID VARCHAR(36) NOT NULL,
    实名状态 ENUM('未实名', '已实名', '校外人员') NOT NULL DEFAULT '未实名',
    PRIMARY KEY (UserID),
    CONSTRAINT FK_Inheritance_1 FOREIGN KEY (UserID) REFERENCES 用户 (UserID) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Table: 卖家                                                    */
/*==============================================================*/
CREATE TABLE 卖家 (
    UserID VARCHAR(36) NOT NULL,
    证件号 VARCHAR(20) NOT NULL UNIQUE,
    实名状态 ENUM('未实名', '已实名', '校外人员') NOT NULL DEFAULT '未实名',
    PRIMARY KEY (UserID),
    CONSTRAINT FK_Inheritance_2 FOREIGN KEY (UserID) REFERENCES 用户 (UserID) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Table: 管理员                                                  */
/*==============================================================*/
CREATE TABLE 管理员 (
    UserID VARCHAR(36) NOT NULL,
    PRIMARY KEY (UserID),
    CONSTRAINT FK_Inheritance_3 FOREIGN KEY (UserID) REFERENCES 用户 (UserID) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Table: 商品分类                                                */
/*==============================================================*/
CREATE TABLE 商品分类 (
    CategoryID INT AUTO_INCREMENT NOT NULL,
    分类名称 VARCHAR(50) NOT NULL,
    PRIMARY KEY (CategoryID)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 添加常见大学生二手商品类别
INSERT INTO 商品分类 (分类名称) VALUES 
('教材书籍'),
('电子产品'),
('服装鞋帽'),
('生活用品'),
('体育用品'),
('乐器'),
('文具'),
('其他');

/*==============================================================*/
/* Table: 商品                                                    */
/*==============================================================*/
CREATE TABLE 商品 (
    ProductID VARCHAR(36) NOT NULL COMMENT 'UUID格式商品ID',
    名称 VARCHAR(100) NOT NULL,
    描述 TEXT,
    价格 DECIMAL(12,2) NOT NULL,
    上架时间 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    审核状态 ENUM('待审核', '已审核', '未通过', '已售出') NOT NULL DEFAULT '待审核',
    CategoryID INT,
    卖家_UserID VARCHAR(36) NOT NULL,
    买家_UserID VARCHAR(36),
    PRIMARY KEY (ProductID),
    CONSTRAINT FK_发布 FOREIGN KEY (卖家_UserID) REFERENCES 卖家 (UserID) ON DELETE CASCADE,
    CONSTRAINT FK_属于 FOREIGN KEY (CategoryID) REFERENCES 商品分类 (CategoryID) ON DELETE SET NULL,
    CONSTRAINT FK_购买 FOREIGN KEY (买家_UserID) REFERENCES 买家 (UserID) ON DELETE SET NULL,
    CHECK (价格 >= 0)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Table: 订单                                                    */
/*==============================================================*/
CREATE TABLE 订单 (
    OrderID VARCHAR(32) NOT NULL COMMENT '唯一订单ID',
    UserID VARCHAR(36) NOT NULL,
    总金额 DECIMAL(12,2) NOT NULL,
    交易状态 ENUM('待付款', '已付款', '已完成', '已取消') NOT NULL DEFAULT '待付款',
    ProductID VARCHAR(36),
    创建时间 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (OrderID),
    CONSTRAINT FK_发起 FOREIGN KEY (UserID) REFERENCES 买家 (UserID) ON DELETE CASCADE,
    CONSTRAINT FK_订单_商品 FOREIGN KEY (ProductID) REFERENCES 商品 (ProductID) ON DELETE SET NULL,
    CHECK (总金额 >= 0)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Table: 评价                                                    */
/*==============================================================*/
CREATE TABLE 评价 (
    ReviewID INT AUTO_INCREMENT NOT NULL,
    OrderID VARCHAR(32),
    用户ID VARCHAR(36),
    评分 SMALLINT NOT NULL,
    评论文本 TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ReviewID),
    CONSTRAINT FK_生成 FOREIGN KEY (OrderID) REFERENCES 订单 (OrderID) ON DELETE SET NULL,
    CONSTRAINT FK_评价_买家 FOREIGN KEY (用户ID) REFERENCES 买家 (UserID) ON DELETE SET NULL,
    CHECK (评分 BETWEEN 1 AND 5)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/*==============================================================*/
/* Indexes                                                       */
/*==============================================================*/
CREATE INDEX IDX_商品_名称 ON 商品 (名称);
CREATE INDEX IDX_用户_学号 ON 用户 (学号);

