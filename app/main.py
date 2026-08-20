"""
电商后台管理系统 - 测试靶场
技术栈：FastAPI + SQLAlchemy + MariaDB
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    DECIMAL, Enum, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from typing import Optional, List
from datetime import datetime
import logging
import os
from urllib.parse import quote_plus

# ==================== 数据库配置 ====================
# 数据库连接信息支持通过环境变量覆盖，默认连接本机 127.0.0.1:3306
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")

# 密码做 URL 转义，兼容包含 # @ 等特殊字符的密码
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_size=10, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ecommerce")

# ==================== 数据库模型 ====================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    create_time = Column(DateTime, default=func.now())
    orders = relationship("Order", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, default=0)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    status = Column(Enum('在售', '下架'), default='在售')
    create_time = Column(DateTime, default=func.now())
    categories = relationship("Category", secondary="product_category", backref="products")
    order_items = relationship("OrderItem", back_populates="product")


class ProductCategory(Base):
    __tablename__ = "product_category"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint('product_id', 'category_id', name='uk_product_category'),)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum('待支付', '已支付', '已发货', '已完成', '已取消'), default='待支付')
    create_time = Column(DateTime, default=func.now())
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ==================== 请求/响应模型 ====================

class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=6, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator('username')
    @classmethod
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)


class UserResponse(BaseModel):
    id: int
    username: str
    phone: Optional[str]
    create_time: datetime
    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=50)
    price: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    status: str = Field("在售")
    category_ids: Optional[List[int]] = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('商品名称不能为空')
        return v.strip()

    @field_validator('status')
    @classmethod
    def status_valid(cls, v):
        if v not in ('在售', '下架'):
            raise ValueError('状态只能是"在售"或"下架"')
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    category_ids: Optional[List[int]] = None

    @field_validator('status')
    @classmethod
    def status_valid(cls, v):
        if v is not None and v not in ('在售', '下架'):
            raise ValueError('状态只能是"在售"或"下架"')
        return v


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    status: str
    create_time: datetime
    categories: List[dict] = []
    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: Optional[str] = None
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    create_time: datetime
    items: List[OrderItemResponse] = []
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=50)
    parent_id: int = Field(0)


class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: int
    class Config:
        from_attributes = True


# ==================== FastAPI 应用 ====================

app = FastAPI(title="电商后台管理系统 - 测试靶场", version="1.0.0")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 用户管理接口 ====================

@app.post("/api/users/", response_model=UserResponse, status_code=201, tags=["用户管理"])
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """添加用户"""
    logger.info(f"创建用户请求: username={user_data.username}")
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"用户名 '{user_data.username}' 已存在")
    new_user = User(username=user_data.username, password=user_data.password, phone=user_data.phone)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"用户创建成功: id={new_user.id}")
    return new_user


@app.get("/api/users/", response_model=List[UserResponse], tags=["用户管理"])
def get_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """查询用户列表（分页）"""
    return db.query(User).offset(skip).limit(limit).all()


@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["用户管理"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """查询单个用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    return user


@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["用户管理"])
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """修改用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    if user_data.username is not None and user_data.username != user.username:
        existing = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"用户名 '{user_data.username}' 已存在")
        user.username = user_data.username
    if user_data.password is not None:
        user.password = user_data.password
    if user_data.phone is not None:
        user.phone = user_data.phone
    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/users/{user_id}", response_model=MessageResponse, tags=["用户管理"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
    db.delete(user)
    db.commit()
    return MessageResponse(message=f"用户 '{user.username}' 删除成功")


# ==================== 商品管理接口 ====================

@app.post("/api/products/", response_model=ProductResponse, status_code=201, tags=["商品管理"])
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """添加商品"""
    logger.info(f"创建商品: name={product_data.name}")
    new_product = Product(name=product_data.name, price=product_data.price, stock=product_data.stock, status=product_data.status)
    db.add(new_product)
    db.flush()
    if product_data.category_ids:
        for cat_id in product_data.category_ids:
            cat = db.query(Category).filter(Category.id == cat_id).first()
            if not cat:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"分类ID {cat_id} 不存在")
            db.add(ProductCategory(product_id=new_product.id, category_id=cat_id))
    db.commit()
    db.refresh(new_product)
    return _build_product_response(new_product, db)


@app.get("/api/products/", response_model=List[ProductResponse], tags=["商品管理"])
def get_products(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), category_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """查询商品列表（分页+分类筛选）"""
    query = db.query(Product)
    if category_id is not None:
        query = query.join(ProductCategory).filter(ProductCategory.category_id == category_id)
    products = query.offset(skip).limit(limit).all()
    return [_build_product_response(p, db) for p in products]


@app.get("/api/products/{product_id}", response_model=ProductResponse, tags=["商品管理"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    """查询单个商品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品ID {product_id} 不存在")
    return _build_product_response(product, db)


@app.put("/api/products/{product_id}", response_model=ProductResponse, tags=["商品管理"])
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    """修改商品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品ID {product_id} 不存在")
    if product_data.name is not None:
        product.name = product_data.name
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.stock is not None:
        product.stock = product_data.stock
    if product_data.status is not None:
        product.status = product_data.status
    if product_data.category_ids is not None:
        db.query(ProductCategory).filter(ProductCategory.product_id == product_id).delete()
        for cat_id in product_data.category_ids:
            cat = db.query(Category).filter(Category.id == cat_id).first()
            if not cat:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"分类ID {cat_id} 不存在")
            db.add(ProductCategory(product_id=product_id, category_id=cat_id))
    db.commit()
    db.refresh(product)
    return _build_product_response(product, db)


@app.delete("/api/products/{product_id}", response_model=MessageResponse, tags=["商品管理"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除商品（检查未完成订单）"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品ID {product_id} 不存在")
    # 检查是否有未完成订单
    unfinished = db.query(OrderItem).join(Order).filter(
        OrderItem.product_id == product_id,
        Order.status.in_(['待支付', '已支付', '已发货'])
    ).first()
    if unfinished:
        raise HTTPException(status_code=400, detail=f"商品 '{product.name}' 存在未完成的订单，不允许删除")
    db.delete(product)
    db.commit()
    return MessageResponse(message=f"商品 '{product.name}' 删除成功")


# ==================== 订单管理接口 ====================

@app.post("/api/orders/", response_model=OrderResponse, status_code=201, tags=["订单管理"])
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """创建订单（含明细+扣库存）"""
    logger.info(f"创建订单: user_id={order_data.user_id}")
    user = db.query(User).filter(User.id == order_data.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail=f"用户ID {order_data.user_id} 不存在")

    total_amount = 0.0
    items_data = []
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"商品ID {item.product_id} 不存在")
        if product.status != '在售':
            raise HTTPException(status_code=400, detail=f"商品 '{product.name}' 已下架，无法购买")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"商品 '{product.name}' 库存不足，当前库存: {product.stock}，请求数量: {item.quantity}")
        total_amount += float(product.price) * item.quantity
        items_data.append({'product': product, 'quantity': item.quantity, 'price': float(product.price)})

    if total_amount <= 0:
        raise HTTPException(status_code=400, detail="订单金额必须大于0")

    new_order = Order(user_id=order_data.user_id, total_amount=round(total_amount, 2), status='待支付')
    db.add(new_order)
    db.flush()

    for item_data in items_data:
        db.add(OrderItem(order_id=new_order.id, product_id=item_data['product'].id, quantity=item_data['quantity'], price=item_data['price']))
        item_data['product'].stock -= item_data['quantity']
        logger.info(f"商品 '{item_data['product'].name}' 库存扣减: -{item_data['quantity']}，剩余: {item_data['product'].stock}")

    db.commit()
    db.refresh(new_order)
    return _build_order_response(new_order, db)


@app.get("/api/orders/", response_model=List[OrderResponse], tags=["订单管理"])
def get_orders(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), status: Optional[str] = Query(None), user_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """查询订单列表"""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if user_id:
        query = query.filter(Order.user_id == user_id)
    orders = query.order_by(Order.create_time.desc()).offset(skip).limit(limit).all()
    return [_build_order_response(o, db) for o in orders]


@app.get("/api/orders/{order_id}", response_model=OrderResponse, tags=["订单管理"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    """查询单个订单（含明细）"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"订单ID {order_id} 不存在")
    return _build_order_response(order, db)


@app.put("/api/orders/{order_id}/cancel", response_model=OrderResponse, tags=["订单管理"])
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """取消订单（仅限待支付）"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"订单ID {order_id} 不存在")
    if order.status != '待支付':
        raise HTTPException(status_code=400, detail=f"当前订单状态为 '{order.status}'，只有 '待支付' 状态的订单才能取消")
    # 恢复库存
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    order.status = '已取消'
    db.commit()
    db.refresh(order)
    return _build_order_response(order, db)


# ==================== 分类管理接口 ====================

@app.post("/api/categories/", response_model=CategoryResponse, status_code=201, tags=["分类管理"])
def create_category(cat_data: CategoryCreate, db: Session = Depends(get_db)):
    """添加分类"""
    if cat_data.parent_id != 0:
        parent = db.query(Category).filter(Category.id == cat_data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail=f"父分类ID {cat_data.parent_id} 不存在")
    new_cat = Category(name=cat_data.name, parent_id=cat_data.parent_id)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@app.get("/api/categories/", response_model=List[CategoryResponse], tags=["分类管理"])
def get_categories(db: Session = Depends(get_db)):
    """查询所有分类"""
    return db.query(Category).all()


# ==================== 辅助函数 ====================

def _build_product_response(product, db):
    """构建商品响应"""
    cats = db.query(Category).join(ProductCategory).filter(ProductCategory.product_id == product.id).all()
    return {
        "id": product.id, "name": product.name, "price": float(product.price),
        "stock": product.stock, "status": product.status, "create_time": product.create_time,
        "categories": [{"id": c.id, "name": c.name} for c in cats]
    }


def _build_order_response(order, db):
    """构建订单响应"""
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    items_data = []
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        items_data.append({"id": item.id, "product_id": item.product_id, "quantity": item.quantity, "price": float(item.price), "product_name": product.name if product else "未知"})
    return {
        "id": order.id, "user_id": order.user_id, "total_amount": float(order.total_amount),
        "status": order.status, "create_time": order.create_time, "items": items_data
    }


# ==================== 健康检查 ====================

@app.get("/", tags=["系统"])
def health_check():
    return {"status": "running", "message": "电商后台管理系统运行正常", "time": datetime.now().isoformat()}


@app.get("/api/db-check", tags=["系统"])
def db_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(func.now()).scalar()
        return {"status": "ok", "db_time": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
