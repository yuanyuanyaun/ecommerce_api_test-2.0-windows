-- 创建电商数据库，若不存在则创建，默认使用utf8mb4字符集与通用排序规则
create database if not exists ecommerce_db
    default character set utf8mb4
    default collate utf8mb4_general_ci;

-- 切换到电商数据库
use ecommerce_db;

-- 按外键依赖倒序删除已存在的表，避免外键约束导致删除失败
drop table if exists order_items;
drop table if exists orders;
drop table if exists product_category;
drop table if exists categories;
drop table if exists products;
drop table if exists users;

-- 用户表：存储系统用户的账号与基础信息
create table users (
    id int auto_increment primary key comment '用户ID',
    username varchar(50) not null comment '用户名',
    password varchar(255) not null comment '密码',
    phone varchar(20) default null comment '手机号',
    create_time datetime default current_timestamp comment '创建时间',
    unique key uk_username (username)
) engine=innodb default charset=utf8mb4 comment='用户表';

-- 商品分类表：维护商品分类的层级关系，支持多级分类
create table categories (
    id int auto_increment primary key comment '分类ID',
    name varchar(50) not null comment '分类名称',
    parent_id int default 0 comment '父分类ID，0表示顶级'
) engine=innodb default charset=utf8mb4 comment='商品分类表';

-- 商品表：存储商品的核心信息、价格与库存状态
create table products (
    id int auto_increment primary key comment '商品ID',
    name varchar(50) not null comment '商品名称',
    price decimal(10,2) not null comment '商品价格',
    stock int not null default 0 comment '库存',
    status enum('在售','下架') default '在售' comment '商品状态',
    create_time datetime default current_timestamp comment '创建时间',
    constraint chk_price check (price > 0),
    constraint chk_stock check (stock >= 0)
) engine=innodb default charset=utf8mb4 comment='商品表';

-- 商品-分类关联表：实现商品与分类的多对多关联关系
create table product_category (
    id int auto_increment primary key comment '关联ID',
    product_id int not null comment '商品ID',
    category_id int not null comment '分类ID',
    unique key uk_product_category (product_id, category_id),
    constraint fk_pc_product foreign key (product_id) references products(id) on delete cascade,
    constraint fk_pc_category foreign key (category_id) references categories(id) on delete cascade
) engine=innodb default charset=utf8mb4 comment='商品-分类关联表';

-- 订单表：存储订单主单信息，关联对应用户
create table orders (
    id int auto_increment primary key comment '订单ID',
    user_id int not null comment '用户ID',
    total_amount decimal(10,2) not null comment '订单总金额',
    status enum('待支付','已支付','已发货','已完成','已取消') default '待支付' comment '订单状态',
    create_time datetime default current_timestamp comment '创建时间',
    constraint chk_total_amount check (total_amount > 0),
    constraint fk_order_user foreign key (user_id) references users(id)
) engine=innodb default charset=utf8mb4 comment='订单表';

-- 订单明细表：存储订单内的商品明细，一条订单对应多条明细
create table order_items (
    id int auto_increment primary key comment '明细ID',
    order_id int not null comment '订单ID',
    product_id int not null comment '商品ID',
    quantity int not null comment '购买数量',
    price decimal(10,2) not null comment '成交单价',
    constraint chk_quantity check (quantity > 0),
    constraint fk_item_order foreign key (order_id) references orders(id) on delete cascade,
    constraint fk_item_product foreign key (product_id) references products(id)
) engine=innodb default charset=utf8mb4 comment='订单明细表';

-- ==================== 插入测试数据 ====================

-- 插入用户测试数据
insert into users (username, password, phone) values
('zhangsan', '123456', '13800138001'),
('lisi', '654321', '13800138002'),
('wangwu', 'abc123', '13800138003');

-- 插入商品分类测试数据，包含两级分类
insert into categories (name, parent_id) values
('电子产品', 0),
('服装', 0),
('手机', 1),
('电脑', 1),
('男装', 2),
('女装', 2);

-- 插入商品测试数据，覆盖在售、下架多种状态
insert into products (name, price, stock, status) values
('iPhone 15 Pro', 8999.00, 100, '在售'),
('华为Mate 60', 6999.00, 80, '在售'),
('联想ThinkPad X1', 12999.00, 50, '在售'),
('Nike运动鞋', 599.00, 200, '在售'),
('优衣库T恤', 99.00, 500, '在售'),
('小米14', 4299.00, 60, '在售'),
('vivoY600', 1299.00, 70, '在售'),
('已下架商品', 10.00, 0, '下架');

-- 插入商品与分类的关联关系
insert into product_category (product_id, category_id) values
(1, 3), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3), (7, 3);

-- 插入订单主单测试数据，覆盖全部订单状态
insert into orders (user_id, total_amount, status) values
(1, 12999.00, '已支付'),
(2, 599.00, '待支付'),
(1, 99.00, '已完成'),
(2, 4299.00, '已取消'),
(1, 1299.00, '已发货');

-- 插入订单明细测试数据
insert into order_items (order_id, product_id, quantity, price) values
(1, 3, 1, 12999.00),
(2, 4, 1, 599.00),
(3, 5, 1, 99.00),
(4, 6, 1, 4299.00),
(5, 7, 1, 1299.00);
