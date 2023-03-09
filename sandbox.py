""" Database engine is initializes upon import!!! """
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


def check_CTP_plots(engine, date):
    with Session(engine) as init_session:
        print_and_plot(init_session, ProjectionATP)

    # Execute five days
    for i in range(5):
        with Session(engine) as action_session:
            execute_scheduled(action_session, date)
            action_session.commit()
            # Check changes:
            # stockpoint_1501 = get_all(action_session, table=StockPoint)[1]
            # print(f'Today is {date}. Stock is: {stockpoint_1501.current_stock}')
        date += timedelta(days=1)

    with Session(engine) as end_session:
        print_and_plot(end_session, ProjectionCTP)


def check_order_history():
    pass

if __name__ == "__main__":
    global_date = date.today()
    main_engine = create_engine("sqlite+pysqlite:///ctp_database.sqlite", echo=False, future=True)
    Base.metadata.create_all(main_engine)
    with Session(main_engine) as init_session:
        premake_db(init_session, CcrpBase)

    check_CTP_plots(main_engine, global_date)
    print(f'Today is {date.today()} and global_date is {global_date}') # See if global_date was mutated


    reset_db(main_engine)
