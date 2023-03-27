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
        inspector = inspect(test_engine)

        for orm_class in expected_db_orms:
            assert issubclass(orm_class, Base)
            assert orm_class.__tablename__ in inspector.get_table_names()

        with Session(test_engine) as test_config_session:
            # DB starts empty
            for orm_class in expected_db_orms:
                data_content = test_config_session.scalars(select(orm_class)).all()
                assert data_content == []

            # Can add content
            product_a = Product(name='product_a', price='50')
            stockpoint_a = StockPoint(product=product_a, name='stockpoint_a', current_stock=10)
            test_config_session.add_all([product_a, stockpoint_a])
            test_config_session.commit()

        # DB content persists to new session
        with Session(test_engine) as test_config_session_b:
            stockpoints_in_db = test_config_session_b.scalars(select(StockPoint)).all()
            assert len(stockpoints_in_db) == 1 and stockpoints_in_db[0].product.name == 'product_a'

        # DB content is emptied with reset()
        reset_db(test_engine)
        with Session(test_engine) as test_config_session_c:
            stockpoints_in_db = test_config_session_c.scalars(select(StockPoint)).all()
            assert stockpoints_in_db == []


class TestDBSupportFunctions:
    def test_add_from_class(self):
        with Session(test_engine) as test_afc_session_a:
            # Fill
            add_from_class(test_afc_session_a, CcrpBase)

            # Ensure it's been filled
            for table in expected_db_orms:
                table_contents = get_all(test_afc_session_a, table)
                assert isinstance(table_contents, list) and table_contents != []

            test_afc_session_a.commit()

        # Check content in new session
        with Session(test_engine) as test_afc_session_b:
            for table in expected_db_orms:
                table_contents = get_all(test_afc_session_b, table)
                assert table_contents != []

            premade_product = get_by_name(test_afc_session_b, Product, "ccrp_ip")
            db_products = get_all(test_afc_session_b, Product)
            assert premade_product in db_products

            stockpoint_names_in_db = [stockpoint.name for stockpoint in get_all(test_afc_session_b, StockPoint)]
            assert stockpoint_names_in_db == ["crp_raw", "crp_1501", "crp_shipped"]

            routes = get_all(test_afc_session_b, SupplyRoute)
            assert len(routes) == 2
            assert routes[0].sender.name == stockpoint_names_in_db[0]
            assert routes[0].receiver.name == routes[1].sender.name == stockpoint_names_in_db[1]
            assert routes[1].receiver.name == stockpoint_names_in_db[2]


class TestQueryFilters:
    def test_order_filtering(self):
        with Session(test_engine) as test_session:

            all_orders = get_all(test_session, MoveOrder)
            all_stockpoints = get_all(test_session, StockPoint)

            for stockpoint in all_stockpoints:
                incoming_orders = get_incoming_move_orders(test_session, stockpoint)
                outgoing_orders = get_outgoing_move_orders(test_session, stockpoint)

                assert set(incoming_orders) <= set(all_orders)
                assert set(outgoing_orders) <= set(all_orders)
                assert set(incoming_orders).isdisjoint(set(outgoing_orders))

                early_dates = [date.today(), date.today() + timedelta(days=5), date.today() + timedelta(days=30)]
                later_dates = [date.today() + timedelta(days=5), date.today() + timedelta(days=15), date.today() + timedelta(days=100)]

                for start_date in early_dates:

                    invalid_end_dates = list(filter(lambda d: d < start_date, later_dates))
                    for end_date in invalid_end_dates:
                        with pytest.raises(ValueError) as exc_info:
                            order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=True)

                    valid_end_dates = list(filter(lambda d: d >= start_date, later_dates))
                    for end_date in valid_end_dates:
                        incoming_these_dates = order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=False)
                        outgoing_these_dates = order_filter(test_session, stockpoint, start_date, end_date, incoming=False, outgoing=True)
                        all_orders_these_dates = order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=True)

                        assert set(incoming_these_dates) <= set(incoming_orders)
                        assert set(outgoing_these_dates) <= set(outgoing_orders)
                        assert set(all_orders_these_dates) <= set(all_orders)
                        assert set(incoming_these_dates) <= set(all_orders_these_dates) >= set(outgoing_these_dates)

                        # assert consistent result between single-step and two-step filtering
                        assert incoming_these_dates == filter_by_date(incoming_orders, start_date, end_date)
                        assert outgoing_these_dates == filter_by_date(outgoing_orders, start_date, end_date)
            # Does not commit


class TestMoveExecution:
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
            assert order.request.quantity_delivered == order.quantity

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


class TestNewRequests:
    def test_add_request(self):
        with Session(test_engine) as add_request_session:
            outgoing_route = get_all(add_request_session, SupplyRoute)[-1]

            id_of_last_premade_request = outgoing_route.move_requests[-1].id
            assert len(outgoing_route.move_requests) == 4
            new_request = add_request(outgoing_route, 4, 31)
            add_request_session.add(new_request)
            assert len(outgoing_route.move_requests) == 5

            add_request_session.commit()

        with Session(test_engine) as add_moves_session:
            # Ensure we have the new_request from previous session:
            last_request = get_all(add_moves_session, MoveRequest)[-1]
            assert last_request.id == id_of_last_premade_request + 1

            # Add MoveOrder that fulfills half the request
            partial_order = MoveOrder(request=last_request, order_date=date.today() + timedelta(days=2), quantity=last_request.quantity // 2)
            add_moves_session.add(partial_order)

            # The MoveOrder that automatically fills the remainder
            fill_order = fill_request(last_request)
            add_moves_session.add(fill_order)
            assert partial_order.quantity + fill_order.quantity == last_request.quantity

            # The MoveOrders are promised but not executed. Execute and check that delivery is complete.
            assert last_request.quantity_delivered == 0
            execute_move(add_moves_session, partial_order)
            execute_move(add_moves_session, fill_order)
            assert last_request.quantity_delivered == last_request.quantity


        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)


class TestOther:
    def test_capability(self):
        test_session = Session(test_engine)
        run_with_session(test_engine, add_from_class, input_class=CcrpBase)

        for db_table in expected_db_orms:
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

