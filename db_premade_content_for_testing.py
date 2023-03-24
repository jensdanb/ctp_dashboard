from database_model import *


# Add crp and cys to database
class CcrpBase():
    def __init__(self):
        self.product = Product(
            name="ccrp_ip",
            price=100,
        )
        self.stock_points=[
               StockPoint(product=self.product, name="crp_raw", current_stock=630),
               StockPoint(product=self.product, name="crp_1501", current_stock=150),
               StockPoint(product=self.product, name="crp_shipped", current_stock=0)
            ]
        self.route1 = SupplyRoute(
            product=self.product,
            sender=self.stock_points[0],
            receiver=self.stock_points[1],
            move_requests = [
                MoveRequest(quantity=100, date_of_registration=date.today(), requested_delivery_date=date.today() + timedelta(days=4),
                            move_orders=[MoveOrder(quantity=100, order_date=date.today() + timedelta(days=4))]
                    ),
                MoveRequest(quantity=160, date_of_registration=date.today(), requested_delivery_date=date.today() + timedelta(days=4),
                            move_orders=[MoveOrder(quantity=160, order_date=date.today() + timedelta(days=9))]
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
