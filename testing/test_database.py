import pytest

from database_model import *  # Import creates database with the test_engine, stored in memory
from db_premade_content_for_testing import CcrpBase
from sqlalchemy.orm import Session


# Arrange
def capture_sql_exception(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except exc.SQLAlchemyError as e:
        return e


class TestConfig:
    def test_config(self):
        for table in all_db_classes:
            assert issubclass(table, Base)


class TestDBModel:
    def test_add_from_class(self):
        with Session(test_engine) as test_session:

            # Ensure new database starts empty
            for db_table in all_db_classes:
                table_contents = get_all(test_session, db_table)
                assert table_contents == []

            # Fill
            add_from_class(test_session, CcrpBase)

            # Ensure it's been filled
            for db_table in all_db_classes:
                table_contents = get_all(test_session, db_table)
                assert isinstance(table_contents, list) and table_contents != []

            test_session.commit()

    def test_order_filtering(self):
        with Session(test_engine) as test_session:

            all_orders = get_all(test_session, MoveOrder)
            all_stockpoints = get_all(test_session, StockPoint)

            for stockpoint in all_stockpoints:
                all_incoming = get_incoming_move_orders(test_session, stockpoint)
                all_outgoing = get_outgoing_move_orders(test_session, stockpoint)

                assert set(all_incoming) <= set(all_orders)
                assert set(all_outgoing) <= set(all_orders)
                assert set(all_incoming).isdisjoint(set(all_outgoing))

                early_dates = [date.today(), date.today() + timedelta(days=5), date.today() + timedelta(days=30)]
                later_dates = [date.today() + timedelta(days=5), date.today() + timedelta(days=15), date.today() + timedelta(days=100)]

                for start_date in early_dates:

                    # end_date < start_date should be invalid
                    for end_date in list(filter(lambda d: d < start_date, later_dates)):
                        with pytest.raises(ValueError) as exc_info:
                            order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=True)

                    # start_date <= end_date ensured by filter, proceed to test:
                    for end_date in list(filter(lambda d: d >= start_date, later_dates)):
                        incoming_these_dates = order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=False)
                        outgoing_these_dates = order_filter(test_session, stockpoint, start_date, end_date, incoming=False, outgoing=True)
                        all_orders_these_dates = order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=True)

                        assert set(incoming_these_dates) <= set(all_incoming)
                        assert set(outgoing_these_dates) <= set(all_outgoing)
                        assert set(all_orders_these_dates) <= set(all_orders)
                        assert set(incoming_these_dates) <= set(all_orders_these_dates) >= set(outgoing_these_dates)

                        # assert consistent result between single-step and two-step filtering
                        assert incoming_these_dates == filter_by_date(all_incoming, start_date, end_date)
                        assert outgoing_these_dates == filter_by_date(all_outgoing, start_date, end_date)
            # Does not commit


class TestDBfunctions:
    def test_execute_move(self):
        with Session(test_engine) as test_session_1:
            # Status before execution
            stockpoint = get_by_name(test_session_1, StockPoint, "crp_1501")
            pre_stock = stockpoint.current_stock
            order = get_outgoing_move_orders(test_session_1, stockpoint)[0]
            print(f'Prestock: {stockpoint.current_stock}')

            # Execute
            execute_move(test_session_1, order)
            print(f'After_stock in session: {stockpoint.current_stock}')

            # Expected effects
            assert stockpoint.current_stock == pre_stock - order.quantity
            assert order.completion_status == 1

            # Cannot be executed twice
            with pytest.raises(ValueError) as exc_info:
                execute_move(test_session_1, order)
            assert "Order is completed or invalid" in exc_info.__str__()

            test_session_1.commit()

    def test_execute_move_2(self):
        with Session(test_engine) as test_session_2:
            stockpoint = get_by_name(test_session_2, StockPoint, "crp_1501")
            order_1 = get_outgoing_move_orders(test_session_2, stockpoint)[0]
            order_2 = get_outgoing_move_orders(test_session_2, stockpoint)[1]

            # Expected effects
            assert stockpoint.current_stock == 90  # Was 150 before order_1 in previous session
            assert order_1.completion_status == 1

            # Cannot execute order_1 again
            with pytest.raises(ValueError) as exc_info:
                execute_move(test_session_2, order_1)
            assert "Order is completed or invalid" in exc_info.__str__()

            # Cannot move more than the sender has
            order_2.quantity += stockpoint.current_stock
            with pytest.raises(ValueError) as exc_info:
                execute_move(test_session_2, order_2)
            assert "Cannot move more than the sender has!" in exc_info.__str__()

            # Assert no changes went through
            assert order_2.completion_status == 0
            assert stockpoint.current_stock == 90

            """ Tests for later"""
            """
            assert order_2.day == pre_date + timedelta(days=5)
            # Complete what you can
            order_2.execute_move('s')
            assert stockpoint.current_stock == 0
            assert order_2.completion_status == 1
            """
        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)

    def test_capability(self):
        test_session = Session(test_engine)
        run_with_session(test_engine, add_from_class, input_class=CcrpBase)

        for db_table in all_db_classes:
            table_contents = get_all(test_session, db_table)
            assert isinstance(table_contents, list) and table_contents != []
        route = get_all(test_session, SupplyRoute)[0]  # Route nr. [0] is from bulk to finished

        # Should raise exceptions:
        incorrect_arguments = [-1, 0.3, "foo"]
        for arg in incorrect_arguments:
            with pytest.raises(ValueError) as exc_info:
                deliverable = route.capability(arg)
            assert "Days to delivery must be an integer and not negative." in exc_info.__str__()

        correct_arguments = [0, 1, 4, 60]
        for arg in correct_arguments:
            deliverable = route.capability(arg)
            assert isinstance(deliverable, int) and deliverable >= 0

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)

