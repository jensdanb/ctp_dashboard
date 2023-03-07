""" Database main_engine is initializes upon import!!! """
from database_model import *
from db_premade_content_for_testing import CcrpBase
from stock_projection_2D import ProjectionATP, ProjectionCTP


def premake_db(session, source_class):
    if not session.scalars(select(Product)).all():  # Statement triggers if db is empty. To be replaced.
        run_in_session(session, add_from_class, input_class=source_class)


def reset_db(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def execute_scheduled(session, date):
    scheduled_move_orders = get_scheduled_orders(session, date)
    for order in scheduled_move_orders:
        execute_move(session, order)


def study_stockpoint(session, stockpoint, *start_date):
    projection = ProjectionCTP(session, stockpoint, *start_date)
    projection.plot.show()
    print(projection.df.head(13))


def premade_test():
    current_date = date.today()
    main_engine = create_engine("sqlite+pysqlite:///ctp_database.sqlite", echo=False, future=True)
    reset_db(main_engine)

    # Make database, see initial content
    with Session(main_engine) as init_session:
        premake_db(init_session, CcrpBase)
        stockpoint_1501 = get_all(init_session, table=StockPoint)[1]

        study_stockpoint(init_session, stockpoint_1501)

    # Execute five days
    for i in range(5):
        with Session(main_engine) as action_session:
            execute_scheduled(action_session, current_date)
            action_session.commit()

            stockpoint_1501_refreshed = get_all(action_session, table=StockPoint)[1]
            print(f'Today is {current_date}. Stock is: {stockpoint_1501_refreshed.current_stock}')

        current_date += timedelta(days=1)

    with Session(main_engine) as study_session:
        stockpoint_1501_refreshed = get_all(action_session, table=StockPoint)[1]
        study_stockpoint(study_session, stockpoint_1501_refreshed, current_date)


if __name__ == "__main__":
    premade_test()

    # print(projection.project_ctp())

    # reset_db(main_engine)
"""
# Use for analysis

# Fetch and manage capability (routes and inventory)
input current inventory to projection

# Get and manage move orders
add new valid orders 
edit orders
validate and commit changes to db
# Later: version control the database

"""

"""
if not existing_orders:
    incoming_1501 = get_incoming_route(session, "crp_1501")
    db_action(session, initialize_move_orders, route=incoming_1501, move_orders=premade_1501_incoming)

    outgoing_1501 = get_outgoing_route(session, "crp_1501")
    db_action(session, initialize_move_orders, route=outgoing_1501, move_orders=premade_1501_sales)
"""

