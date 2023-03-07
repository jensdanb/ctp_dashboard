from typing import List, Optional

from sqlalchemy import Column, String, Table, Date
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine, select, exc
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy import update

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session

from datetime import date, timedelta

# make database
Base = declarative_base()


# For discrete (countable) goods, such as screws, tires,
class Product(Base):
    __tablename__ = "product_base"

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

    # Relationships
    stock_points: Mapped[List["StockPoint"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    supply_routes: Mapped[List["SupplyRoute"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    # Variables
    price: Mapped[Optional[int]]  # In euro-cents. 100 = 1 EUR, display as 1.00 to user.

    def __repr__(self):
        return f"Product {self.name}."


class StockPoint(Base):
    __tablename__ = "stock_point"

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

    # Relationships
    product_id = mapped_column(ForeignKey("product_base.id"), nullable=False)
    product: Mapped[Product] = relationship(back_populates="stock_points")

    # Variables
    current_stock: Mapped[int] = mapped_column(CheckConstraint("current_stock >= 0"))

    # outgoing_supply_routes = relationship("SupplyRoute")

    # upstream_stock = Column(
    # planned_receipts = relationship("MoveOrder", back_populates="receiver")
    # planned_sends = relationship("MoveOrder", back_populates="source")

    def __repr__(self):
        return f"Stock point {self.name}, holding {self.current_stock} of item {self.product.name}."


# For one-to-one bom structure

class SupplyRoute(Base):
    __tablename__ = "supply_route"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="Not_route_to_self"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    product_id = mapped_column(ForeignKey("product_base.id"), nullable=False)
    product: Mapped[Product] = relationship(back_populates="supply_routes")

    sender_id: Mapped[int] = mapped_column(ForeignKey("stock_point.id"))
    sender: Mapped[StockPoint] = relationship(foreign_keys=sender_id)

    receiver_id: Mapped[int] = mapped_column(ForeignKey("stock_point.id"))
    receiver: Mapped[StockPoint] = relationship(foreign_keys=receiver_id)

    move_orders: Mapped[List["MoveOrder"]] = relationship(back_populates="route")
    has_moved_total: Mapped[int] = mapped_column(default=0)

    # Capability
    capacity: Mapped[int] = mapped_column(CheckConstraint("capacity >= 0"), default=0)
    lead_time: Mapped[int] = mapped_column(CheckConstraint("lead_time >= 0"), default=2)  # day

    def capability(self, day):
        if not isinstance(day, int) or day < 0:
            raise ValueError("Days to delivery must be an integer and not negative.")
        if day < self.lead_time:
            capability = 0
        else:
            capability = self.capacity * (day + 1 - self.lead_time)
        return capability

    def __repr__(self):
        return f"Supply route for {self.product.name} from {self.sender.name} to {self.receiver.name}. " \
               f"Capacity {self.capacity} with Lead Time {self.lead_time}"


class MoveOrder(Base):
    __tablename__ = "move_order"

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    route_id = mapped_column(ForeignKey("supply_route.id"), nullable=False)
    route: Mapped[SupplyRoute] = relationship(back_populates="move_orders")

    # Variables
    quantity: Mapped[int]

    date = Column(Date)  # Dates do not yet use the modern Mapped ORM style from sqlA. v.2
    date_of_registration = Column(Date)  # Insert current-start_date
    completion_status: Mapped[int] = mapped_column(default=0)  # 0: Not completed. 1: Completed.

    def __repr__(self):
        return f"Move {self.quantity} {self.route.product.name} from {self.route.sender.name} to " \
               f"{self.route.receiver.name} on date {self.date}."





all_db_tables = {Product, StockPoint, SupplyRoute, MoveOrder}  # {} means it is a set

test_engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)  # In-memory database. Not persistent.
Base.metadata.create_all(test_engine)


"""
Database definition ended. 
Database interface functions starts.

Call functions as function()
If not already in a session, use run_with_session() as wrapper to run function with a temporary session. 
"""


def run_in_session(session, func, **kwargs):
    try:
        return_statement = func(session, **kwargs)
        if return_statement is not None:
            return return_statement
        else:
            session.commit()
    except exc.SQLAlchemyError:
        session.rollback()
        raise


def run_with_session(engine, func, **kwargs):
    with Session(engine) as session:
        return_statement = run_in_session(session, func, **kwargs)
        if return_statement is not None:
            return return_statement


def execute_move(session: Session, move: MoveOrder):
    sender: StockPoint = move.route.sender
    receiver: StockPoint = move.route.receiver

    # Validity checks
    if move.completion_status != 0:
        raise ValueError("Cannot execute. Order is completed or invalid. ")
    elif not sender.current_stock >= move.quantity:
        raise ValueError("Cannot move more than the sender has!")

    # Execution
    else:

        sender.current_stock -= move.quantity
        receiver.current_stock += move.quantity
        move.completion_status = 1


def add_from_class(session, input_class):
    class_instance = input_class()  # Create a new object of class input_class
    session.add(class_instance.product)
    # if class_instance not in session.scalars(select(Product)).all():


def get_by_name(session, table, element_name: str):
    stmt = select(table).where(table.name == element_name)
    return session.scalars(stmt).one()


def get_all(session, table):
    stmt = select(table)
    return session.scalars(stmt).all()


def get_scheduled_orders(session, day: date):
    stmt = select(MoveOrder).where(MoveOrder.date == day).where(MoveOrder.completion_status == 0)
    return session.scalars(stmt).all()


def get_incoming_routes(session, stockpoint):
    stmt = select(SupplyRoute).where(SupplyRoute.receiver == stockpoint)
    return session.scalars(stmt).all()


def get_outgoing_routes(session, stockpoint):
    stmt = select(SupplyRoute).where(SupplyRoute.sender == stockpoint)
    return session.scalars(stmt).all()


def get_incoming_move_orders(session, stockpoint):
    stmt = (
        select(MoveOrder).
        join(MoveOrder.route).
        where(SupplyRoute.receiver == stockpoint)
    )
    return session.scalars(stmt).all()


def get_outgoing_move_orders(session, stockpoint):
    stmt = (
        select(MoveOrder).
        join(MoveOrder.route).
        where(SupplyRoute.sender == stockpoint)
    )
    return session.scalars(stmt).all()


def pending_orders(orders):
    return list(filter(lambda order: order.completion_status == 0, orders))


def filter_by_date(orders, start_date: date, end_date: date):
    if end_date < start_date:
        raise ValueError(f"End date ({end_date}) cannot be earlier than Start date ({start_date})")
    else:
        return list(filter(lambda order: start_date <= order.date <= end_date, orders))


def order_filter(session, stockpoint, start_date, end_date, incoming: bool, outgoing: bool):
    orders = []
    if incoming:
        orders += get_incoming_move_orders(session, stockpoint)
    if outgoing:
        orders += get_outgoing_move_orders(session, stockpoint)
    return filter_by_date(orders, start_date, end_date)


def order_filter_v2(session, stockpoint, start_date, end_date, incoming: bool, outgoing: bool):
    orders = []
    if incoming:
        orders += get_incoming_move_orders(session, stockpoint)
    if outgoing:
        orders += get_outgoing_move_orders(session, stockpoint)
    orders = filter_by_date(orders, start_date, end_date)
    return pending_orders(orders)
