# mm_pos/db.py
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

Base = declarative_base()


# --- Database Models ---
class MenuItemDB(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, default="General")


class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "waiter", "cashier", "admin"
    pin = Column(String, nullable=True)

    # relationships
    orders = relationship(
        "OrderDB", back_populates="user", cascade="all, delete-orphan"
    )
    payments = relationship(
        "PaymentDB", back_populates="user", cascade="all, delete-orphan"
    )

    # --- Role-based Permissions ---
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"

    def can_take_orders(self) -> bool:
        return self.role.lower() in ("waiter", "cashier", "admin")

    def can_process_payments(self) -> bool:
        return self.role.lower() in ("cashier", "admin")

    def can_view_reports(self) -> bool:
        return self.role.lower() == "admin"


class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_number = Column(Integer, nullable=True)
    takeout = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # ✅ add FK to TableDB
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)
    table = relationship("TableDB", back_populates="orders")

    # FK to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("UserDB", back_populates="orders")

    items = relationship(
        "OrderItemDB", back_populates="order", cascade="all, delete-orphan"
    )
    payments = relationship(
        "PaymentDB", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemDB(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    qty = Column(Integer, nullable=False, default=1)

    order = relationship("OrderDB", back_populates="items")
    menu_item = relationship("MenuItemDB")


class PaymentDB(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    method = Column(String, nullable=False)
    amount_given = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("OrderDB", back_populates="payments")
    user = relationship("UserDB", back_populates="payments")


class TableDB(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, unique=True, nullable=False)
    status = Column(String, default="open")  # open, occupied, closed

    orders = relationship(
        "OrderDB", back_populates="table", cascade="all, delete-orphan"
    )


# --- Setup Functions ---
def get_engine(db_url="sqlite:///mmpos.db"):
    return create_engine(db_url, echo=False)


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    elif isinstance(engine, str):
        engine = get_engine(engine)

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
