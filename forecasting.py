# Basic common forecast: "We expect to sell X amount next month, and Y amount next 6 months".
import random
from database_model import *


def generate_random_move_orders(n, status, first_date, max_registration_delay, expected_execution_time,
                                quantity_distribution, *args, **rescale):
    # Accepts random.distribution functions and its required *args.
    # If the distribution by default returns values in its own range, such as 0 < x < 1, include rescale= at the end.
    orders = []
    for i in range(n):
        reg_date = first_date + timedelta(days=random.randint(0, max_registration_delay))
        exe_time = timedelta(days=int(expected_execution_time*2*random.betavariate(2, 4)))  # Old version used int(random.triangular(0, expected_execution_time*2, expected_execution_time))
        exe_date = reg_date + exe_time
        quantity = quantity_distribution(*args)
        if rescale:
            quantity = int(quantity * rescale['rescale'])
        orders.append(MoveOrder(quantity=quantity, date=exe_date, date_of_registration=reg_date, completion_status=status))

    return orders

