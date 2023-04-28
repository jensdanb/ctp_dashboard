from typing import List, Optional
from datetime import date, timedelta

from sqlalchemy import Column, String, Table, Date, ForeignKey
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy import create_engine, select, exc, update

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session


Base = declarative_base()


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

    def __repr__(self):
        return f"Stock point {self.name}, holding {self.current_stock} of item {self.product.name}."


# For one-to-one BOM architecture
class SupplyRoute(Base):
    __tablename__ = "supply_route"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="Not_route_to_self"),)

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    product_id = mapped_column(ForeignKey("product_base.id"), nullable=False)
    product: Mapped[Product] = relationship(back_populates="supply_routes")

    sender_id: Mapped[int] = mapped_column(ForeignKey("stock_point.id"))
    sender: Mapped[StockPoint] = relationship(foreign_keys=sender_id)

    receiver_id: Mapped[int] = mapped_column(ForeignKey("stock_point.id"))
    receiver: Mapped[StockPoint] = relationship(foreign_keys=receiver_id)

    move_requests: Mapped[List["MoveRequest"]] = relationship(back_populates="route")

    # Variables
    capacity: Mapped[int] = mapped_column(CheckConstraint("capacity >= 0"), default=0)  # units per day
    lead_time: Mapped[int] = mapped_column(CheckConstraint("lead_time >= 0"), default=2)  # days of delay

    def capability(self, day):  # Not the same as capacity!
        if not isinstance(day, int) or day < 0:
            raise ValueError("Days to delivery must be a positive integer or zero.")
        if day < self.lead_time:
            capability = 0
        else:
            capability = self.capacity * (day + 1 - self.lead_time)
        return capability

    def __repr__(self):
        return f"Supply route from {self.sender.name} to {self.receiver.name}. "


class MoveRequest(Base):
    __tablename__ = "move_request"

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    route_id = mapped_column(ForeignKey("supply_route.id"), nullable=False)
    route: Mapped[SupplyRoute] = relationship(back_populates="move_requests")

    move_orders: Mapped[List["MoveOrder"]] = relationship(back_populates="request")

    # Variables
    date_of_registration = Column(Date)  # Dates do not yet use the modern Mapped ORM style from sqlA. v.2
    requested_delivery_date = Column(Date)
    quantity: Mapped[int]
    quantity_delivered: Mapped[int] = mapped_column(default=0)

    def unanswered_quantity(self):
        return self.quantity - sum([order.quantity for order in self.move_orders])

    def __repr__(self):
        return f"Request {self.quantity} {self.route.product.name} from {self.route.sender.name} to " \
               f"{self.route.receiver.name} for delivery by {self.requested_delivery_date}."


class MoveOrder(Base):
    __tablename__ = "move_order"

    # Identity
    id: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    request_id = mapped_column(ForeignKey("move_request.id"), nullable=False)
    request: Mapped[MoveRequest] = relationship(back_populates="move_orders")

    # Variables
    quantity: Mapped[int]
    order_date = Column(Date)  # Dates do not yet use the modern Mapped ORM style from sqlA. v.2
    completion_status: Mapped[int] = mapped_column(default=0)  # Not completed: 0. Completed: 1

    def __repr__(self):
        return f"Move {self.quantity} along route {self.request.route} on {self.order_date} for request {self.request.id}"


expected_orms_in_db = {Product, StockPoint, SupplyRoute, MoveRequest, MoveOrder}

test_engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
Base.metadata.create_all(test_engine)


""" Core database functions """


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


def reset_db(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def get_by_name(session, table, element_name: str):
    stmt = select(table).where(table.name == element_name)
    return session.scalars(stmt).one()


def get_by_id(session, table, element_id: int):
    stmt = select(table).where(table.id == element_id)
    return session.scalars(stmt).one()


def get_all(session, table):
    stmt = select(table)
    return session.scalars(stmt).all()


""" Database modification functions """


def add_from_class(session, input_class):
    class_instance = input_class()  # Create a new object of class input_class
    session.add(class_instance.product)
    # if class_instance not in session.scalars(select(Product)).all():


def reset_and_fill_db(engine, session, input_classes):
    reset_db(engine)
    for input_class in input_classes:
        add_from_class(session, input_class)


def add_from_class_if_db_is_empty(session, input_class):
    if not session.scalars(select(Product)).all():
        run_in_session(session, add_from_class, input_class=input_class)


def add_request(session, route, delivery_time, quantity):
    reg_date = date.today()
    req_date = reg_date + timedelta(days=delivery_time)
    request = MoveRequest(route=route, date_of_registration=reg_date, requested_delivery_date=req_date, quantity=quantity)

    session.add(request)
    return request


def fill_request(request):
    quantity = request.unanswered_quantity()
    order = MoveOrder(request=request, order_date=request.requested_delivery_date, quantity=quantity)
    return order


def execute_move(session: Session, move: MoveOrder):
    request = move.request
    sender: StockPoint = request.route.sender
    receiver: StockPoint = request.route.receiver

    # Validity checks
    if move.completion_status != 0:
        raise ValueError("Cannot execute. Order is completed or invalid. ")
    elif not sender.current_stock >= move.quantity:
        raise ValueError("Cannot move more than the sender has!")
    elif move.quantity < 0 and abs(move.quantity) > receiver.current_stock:
        raise ValueError("Cannot reverse move more than the receiver has!")
    # Execution
    else:
        sender.current_stock -= move.quantity
        receiver.current_stock += move.quantity
        move.completion_status = 1
        request.quantity_delivered += move.quantity


def execute_scheduled(session, day):
    scheduled_move_orders = get_scheduled_orders(session, day)
    for order in scheduled_move_orders:
        execute_move(session, order)


""" Filtered queries: """


def get_scheduled_orders(session, day: date):
    stmt = select(MoveOrder).where(MoveOrder.order_date == day).where(MoveOrder.completion_status == 0)
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
        join(MoveOrder.request).
        join(MoveRequest.route).
        where(SupplyRoute.receiver == stockpoint)
    )
    return session.scalars(stmt).all()


def get_outgoing_move_orders(session, stockpoint):
    stmt = (
        select(MoveOrder).
        join(MoveOrder.request).
        join(MoveRequest.route).
        where(SupplyRoute.sender == stockpoint)
    )
    return session.scalars(stmt).all()


def completed_orders(orders: list[MoveOrder]):
    return list(filter(lambda order: order.completion_status == 1, orders))


def uncompleted_orders(orders: list[MoveOrder]):
    return list(filter(lambda order: order.completion_status == 0, orders))


def filter_by_date(orders, start_date: date, end_date: date):
    if end_date < start_date:
        raise ValueError(f"End date ({end_date}) cannot be earlier than Start date ({start_date})")
    else:
        return list(filter(lambda order: start_date <= order.order_date <= end_date, orders))


def order_filter(session, stockpoint, start_date, end_date, incoming: bool, outgoing: bool, completed_or_pending=None):
    orders = []
    if incoming:
        orders += get_incoming_move_orders(session, stockpoint)
    if outgoing:
        orders += get_outgoing_move_orders(session, stockpoint)

    orders = filter_by_date(orders, start_date, end_date)

    if completed_or_pending == 'completed':
        return completed_orders(orders)
    elif completed_or_pending == 'pending':
        return uncompleted_orders(orders)
    else:
        return orders
