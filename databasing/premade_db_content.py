from databasing.database_model import *

import itertools
from random import randint, choice, randrange
from faker import Faker
from faker.providers import lorem, color


class CcrpBase():
    def __init__(self):
        self.product = Product(
            name="Product A",
            price=100,
        )
        self.stock_points=[
               StockPoint(product=self.product, name="Unfinished goods", current_stock=630),
               StockPoint(product=self.product, name="Finished goods", current_stock=150),
               StockPoint(product=self.product, name="Shipped Product A", current_stock=0)
            ]
        self.route1 = SupplyRoute(
            product=self.product,
            sender=self.stock_points[0],
            receiver=self.stock_points[1],
            move_requests = [
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today() + timedelta(days=4),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today() + timedelta(days=4))]
                    ),
                MoveRequest(quantity=160,
                            date_of_registration=date.today(),
                            requested_delivery_date=date.today() + timedelta(days=4),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today() + timedelta(days=9)),
                                         MoveOrder(quantity=60, order_date=date.today() + timedelta(days=9))]
                    )
            ],
            capacity=20
        )
        self.route2 = SupplyRoute(
            product=self.product,
            sender=self.stock_points[1],
            receiver=self.stock_points[2],
            move_requests = [
                MoveRequest(quantity=60, date_of_registration=date.today(), requested_delivery_date=date.today()+timedelta(days=2),
                            move_orders=[MoveOrder(quantity=60, order_date=date.today()+timedelta(days=2))]),
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today()+timedelta(days=6),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today()+timedelta(days=6))]),
                MoveRequest(quantity=50, date_of_registration=date.today(), requested_delivery_date=date.today()+timedelta(days=7),
                            move_orders=[MoveOrder(quantity=50, order_date=date.today()+timedelta(days=7))]),
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today() + timedelta(days=11, ),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today()+timedelta(days=11))])
            ],
        )


class ProductB():
    def __init__(self):
        self.product = Product(
            name="Product B",
            price=200,
        )
        self.stock_points=[
               StockPoint(product=self.product, name="Unfinished goods", current_stock=630),
               StockPoint(product=self.product, name="Finished goods", current_stock=150),
               StockPoint(product=self.product, name="Shipped Product B", current_stock=0)
            ]
        self.route1 = SupplyRoute(
            product=self.product,
            sender=self.stock_points[0],
            receiver=self.stock_points[1],
            move_requests = [
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today() + timedelta(days=4),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today() + timedelta(days=4))]
                    ),
                MoveRequest(quantity=160, quantity_delivered=100,
                            date_of_registration=date.today(),
                            requested_delivery_date=date.today() + timedelta(days=-4),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today() + timedelta(days=4), completion_status=1),
                                         MoveOrder(quantity=60, order_date=date.today() + timedelta(days=9))]
                    )
            ],
            capacity=20
        )
        self.route2 = SupplyRoute(
            product=self.product,
            sender=self.stock_points[1],
            receiver=self.stock_points[2],
            move_requests = [
                MoveRequest(quantity=60, date_of_registration=date.today(), requested_delivery_date=date.today()+timedelta(days=2),
                            move_orders=[MoveOrder(quantity=60, order_date=date.today()+timedelta(days=2))]),
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today()+timedelta(days=6),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today()+timedelta(days=6))]),
                MoveRequest(quantity=50, date_of_registration=date.today(), requested_delivery_date=date.today()+timedelta(days=7),
                            move_orders=[MoveOrder(quantity=50, order_date=date.today()+timedelta(days=7))]),
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today() + timedelta(days=11, ),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today()+timedelta(days=11))])
            ],
        )


class FakeProduct():
    def __init__(self):
        fake = Faker()
        fake.add_provider(lorem)
        fake.add_provider(color)

        self.product = Product(
            name=fake.word().capitalize() + ' ' + fake.safe_color_name().capitalize(),
            price=randint(20, 200),
        )
        self.stock_points = [
            StockPoint(product=self.product, name="Stockpoint " + str(s+1), current_stock=choice([0, randrange(100, 1000, 50)]))
            for s in range(randint(3, 5))
        ]
        self.supply_routes = []
        for upstream, downstream in itertools.pairwise(self.stock_points):
            self.supply_routes.append(
                SupplyRoute(
                    product=self.product,
                    sender=upstream,
                    receiver=downstream,
                    capacity=randrange(10, 100, 10)
                )
            )
        for route in self.supply_routes:
            route.move_requests = []
            n_requests = randint(0, 5)
            for request_n in range(n_requests):
                quantity = randrange(40, 200, 20)
                delivery_time = randint(2, 12)
                route.move_requests.append(
                    MoveRequest(quantity=quantity,
                                date_of_registration=date.today(),
                                requested_delivery_date=date.today()+timedelta(days=delivery_time),
                                move_orders=[
                                    MoveOrder(quantity=quantity, order_date=date.today()+timedelta(days=delivery_time))
                                    ]
                                )
                )
