""" Database engine is initializes upon import!!! """
import random
import pandas as pd
import numpy as np

from database_model import *
from db_premade_content_for_testing import CcrpBase
from stock_projection_2D import StockProjection, ProjectionATP, ProjectionCTP


def print_and_plot(session, projection_type): # projection_type can be ProjectionATP or ProjectionCTP
    stockpoint_1501 = get_all(session, table=StockPoint)[1]
    projection = projection_type(session, stockpoint_1501)
    print(projection.df.head(13))
    projection.plot.show()


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


def check_CTP_plots(engine, day):
    with Session(engine) as init_session:
        print_and_plot(init_session, ProjectionATP)

    # Execute five days
    for i in range(5):
        with Session(engine) as action_session:
            execute_scheduled(action_session, day)
            action_session.commit()
            # Check changes:
            # stockpoint_1501 = get_all(action_session, table=StockPoint)[1]
            # print(f'Today is {day}. Stock is: {stockpoint_1501.current_stock}')
        day += timedelta(days=1)

    with Session(engine) as end_session:
        print_and_plot(end_session, ProjectionCTP)


def generate_random_move_orders(n, status, first_date, max_registration_delay, max_execution_delay,
                                quantity_distribution, *args, **rescale):
    # Accepts random.distribution functions and its required *args.
    # If the distribution by default returns values in its own range, such as 0 < x < 1, include rescale= at the end.
    orders = []
    for i in range(n):
        reg_date = first_date + timedelta(days=random.randint(0, max_registration_delay))
        exe_date = reg_date + timedelta(days=random.randint(0, max_execution_delay))
        quantity = quantity_distribution(*args)
        if rescale:
            quantity = int(quantity * rescale['rescale'])
        orders.append(MoveOrder(quantity=quantity, date=exe_date, date_of_registration=reg_date, completion_status=status))

    return orders


if __name__ == "__main__":
    global_date = date.today()
    main_engine = create_engine("sqlite+pysqlite:///ctp_database.sqlite", echo=False, future=True)
    Base.metadata.create_all(main_engine)
    with Session(main_engine) as init_session:
        premake_db(init_session, CcrpBase)

    #check_CTP_plots(main_engine, global_date)
    print(f'Today is {date.today()} and global_date is {global_date}') # See if global_date was mutated

    with Session(main_engine) as history_session:
        # Setup
        route = get_all(history_session, SupplyRoute)[1] # Second route in the DB
        first_date = date.today() - timedelta(days=365)

        # Generate an order history
        new_orders = generate_random_move_orders(3, 1, first_date, 350, 8, random.betavariate, 2, 5, rescale=60)
        route.move_orders += new_orders
        history_session.commit()

        # Inspect order history
        print(route.move_orders[-1])
        stmt = select(MoveOrder).where(MoveOrder.completion_status == 1).where(MoveOrder.date <= date.today())
        completed_orders = history_session.scalars(stmt).all()
        for order in completed_orders:
            delivery_time = order.date - order.date_of_registration
            print(f'Delivery: {delivery_time.days} days. Quantity: {order.quantity} units.')

    reset_db(main_engine)
