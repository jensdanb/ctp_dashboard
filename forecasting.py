# Basic common forecast: "We expect to sell X amount next month, and Y amount next 6 months".
import random
from database_model import *


def generate_random_requests(n, status, earliest_reg_date, last_reg_date, avg_requested_delivery_time,
                             quantity_distribution, *args, **rescale):
    """
    How the random components are made:

    Date of registration is uniformly distributed between earliest and last date (from arguments).

    Requested delivery time is beta distributed around the avg (from argument).
    Beta distribution returns values between 0 and 1. To transform this into dates around the avg, it is:
    Divided by the mean distribution output, thus moving the mean output to 1. Then Multiplied by avg_requested_delivery_time

    Quantity distribution can be any random.distribution functions.
    Pass the chosen distribution function as an argument, followed by any *args it needs.
    If the distribution by default returns values in its own range, such as 0 < x < 1, include rescale= at the end.
    """
    requests = []
    reg_period = last_reg_date - earliest_reg_date  # print(type(reg_period), reg_period.days) -> [<class 'datetime.timedelta'>, 350]

    for i in range(n):

        reg_date = earliest_reg_date + timedelta(days=random.randint(0, reg_period.days))
        a, b = 2, 4  # Alpha and Beta for the beta distribution
        requested_delivery_time = timedelta(days=int(float(((a + b)/ a) * random.betavariate(a, b)) * avg_requested_delivery_time))
        # It is necessary to cast to float first, as int() can cast the factors inside () before calc is completed.
        requested_delivery_date = reg_date + requested_delivery_time
        quantity = quantity_distribution(*args)
        if rescale:
            quantity = int(quantity * rescale['rescale'])
        requests.append(MoveRequest(date_of_registration=reg_date, expected_delivery_date=requested_delivery_date, quantity=quantity, quantity_delivered=quantity*status))

    return requests

