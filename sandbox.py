""" Database engine is initializes upon import!!! """
from pprint import pprint

import pandas as pd
import numpy as np
import random

from database_model import *
from premade_db_content import CcrpBase, ProductB
from stock_projection_2D import StockProjection, ProjectionATP, ProjectionCTP
from forecasting import generate_random_requests


def wave_list_experiments(df: pd.DataFrame):
    sub_df= df.loc[:, ['demand', 'supply']].iloc[:30]
    print(sub_df.head(8))
    print('')
    print(f'fields = {["date"] + sub_df.columns.tolist()}')
    rows = [[i for i in row] for row in sub_df.itertuples()]
    print(f'Rows: {rows}')
    print('')

    n = 12
    df = pd.DataFrame(dict(
        length=np.random.rand(n),
        width=np.random.rand(n),
        data_type=np.random.choice(a=['Train', 'Test'], size=n, p=[0.8, 0.2])
    ))
    df_agg = df.groupby(['data_type']).mean().reset_index()
    print(f'df fields: {df.columns.tolist()}')
    print(f'df rows: {df.values.tolist()}')


def print_and_plot(session, stockpoint, projection_type): # projection_type can be ProjectionATP or ProjectionCTP
    projection = projection_type(session, stockpoint)
    print(projection.df.head(13))
    projection.plot.show()


def check_ctp_plots(engine, stockpoint_id):
    with Session(engine) as init_session:
        stockpoint = get_by_id(init_session, StockPoint, stockpoint_id)
        print_and_plot(init_session, stockpoint, ProjectionATP)

    # Execute orders in next five days
    day = date.today()
    with Session(engine) as action_session:
        for i in range(5):
            execute_scheduled(action_session, day)
            day += timedelta(days=1)
        action_session.commit()

    with Session(engine) as end_session:
        stockpoint = get_by_id(end_session, StockPoint, stockpoint_id)
        print_and_plot(end_session, stockpoint, ProjectionCTP)


def fake_order_history():
    with Session(sandbox_engine) as requests_generation_session:
        # Setup
        route = get_all(requests_generation_session, SupplyRoute)[1] # Second route in the DB
        first_date = date.today() - timedelta(days=365)
        last_date = first_date + timedelta(days=350)

        # Generate an order history
        new_requests = generate_random_requests(20, 1, first_date, last_date, 8, random.betavariate, 2, 5, rescale=200)
        route.move_requests += new_requests
        requests_generation_session.commit()


def inspect_order_history():
    with Session(sandbox_engine) as history_inspection_session:
        # Find the content made in previous session
        route = get_all(history_inspection_session, SupplyRoute)[1]
        stmt = select(MoveRequest).where(MoveRequest.quantity_delivered == MoveRequest.quantity).where(
            MoveRequest.requested_delivery_date <= date.today())
        completed_orders = history_inspection_session.scalars(stmt).all()

        # Inspect order history
        print(route.move_requests[-1])
        for request in completed_orders:
            delivery_time = request.requested_delivery_date - request.date_of_registration
            print(f'Delivery: {delivery_time.days} days. Quantity: {request.quantity} units.')


if __name__ == "__main__":
    global_date = date.today()
    sandbox_engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(sandbox_engine)
    with Session(sandbox_engine) as init_session:
        add_from_class_if_db_is_empty(init_session, CcrpBase)
        stockpoint = get_all(init_session, StockPoint)[1]

    check_ctp_plots(sandbox_engine, stockpoint.id)
    print(f'Today is {date.today()} and global_date is {global_date}') # See if global_date was mutated
    fake_order_history()
    inspect_order_history()


    reset_db(sandbox_engine)
