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
            move_orders=[
                MoveOrder(quantity=100, date=date.today()+timedelta(days=4), date_of_registration=date.today()),
                MoveOrder(quantity=160, date=date.today()+timedelta(days=9), date_of_registration=date.today())
            ],
            capacity=20
        )
        self.route2 = SupplyRoute(
            product=self.product,
            sender=self.stock_points[1],
            receiver=self.stock_points[2],
            move_orders=[
                MoveOrder(quantity=60, date=date.today()+timedelta(days=2), date_of_registration=date.today()),
                MoveOrder(quantity=100, date=date.today()+timedelta(days=6), date_of_registration=date.today()),
                MoveOrder(quantity=50, date=date.today()+timedelta(days=7), date_of_registration=date.today()),
                MoveOrder(quantity=100, date=date.today()+timedelta(days=11), date_of_registration=date.today())
            ]
        )

