from sqlalchemy import inspect
import pytest

from ..databasing.database_model import *
from ..databasing.premade_db_content import ProductA, FakeProduct, BranchingProduct


def capture_sql_exception(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except exc.SQLAlchemyError as e:
        return e


class TestConfig:
    def test_config(self):
        inspector = inspect(test_engine)

        for orm_class in expected_orms_in_db:
            assert issubclass(orm_class, Base)
            assert orm_class.__tablename__ in inspector.get_table_names()

        with Session(test_engine) as test_config_session:
            # DB starts empty
            for orm_class in expected_orms_in_db:
                data_content = test_config_session.scalars(select(orm_class)).all()
                assert data_content == []

            # Can add content
            product_b = Product(name='Product C', price='50')
            stockpoint_b = StockPoint(product=product_b, name='stockpoint_c', current_stock=10)
            test_config_session.add_all([product_b, stockpoint_b])
            test_config_session.commit()

        # DB content persists to new session
        with Session(test_engine) as test_config_session_b:
            stockpoints_in_db = test_config_session_b.scalars(select(StockPoint)).all()
            assert len(stockpoints_in_db) == 1 and stockpoints_in_db[0].product.name == 'Product C'

        # DB content is emptied with reset()
        reset_db(test_engine)
        with Session(test_engine) as test_config_session_c:
            stockpoints_in_db = test_config_session_c.scalars(select(StockPoint)).all()
            assert stockpoints_in_db == []


class TestDBSupportFunctions:
    def test_add_from_classes(self):
        highest_id_numbers = [0] * len(expected_orms_in_db)
        for product_class in [ProductA, FakeProduct, BranchingProduct]:
            with Session(test_engine) as afc_test_session:
                add_from_class(afc_test_session, product_class)
                afc_test_session.commit()

            with Session(test_engine) as content_test_sesison:
                highest_id_numbers = self.added_content_tester(content_test_sesison, product_class, highest_id_numbers)

    def added_content_tester(self, session, product_class: Base, old_highest_id_numbers):
        # There is new content in all tables
        new_highest_id_numbers = [get_all(session, table)[-1].id for table in expected_orms_in_db]

        for new, old in zip(new_highest_id_numbers, old_highest_id_numbers):
            assert new > old

        latest_product_in_db = get_all(session, Product)[-1]
        stockpoint_names_in_db = [stockpoint.name for stockpoint in latest_product_in_db.stock_points]
        routes = latest_product_in_db.supply_routes

        # Number of routes and last id number match
        assert routes[-1].id == len(get_all(session, SupplyRoute))

        if product_class in (ProductA, FakeProduct):
            # Routing between stockpoints is as follows: route1{sp1 -> sp2}, route2{sp2 -> sp3}
            assert routes[0].sender.name == stockpoint_names_in_db[0]
            assert routes[0].receiver.name == routes[1].sender.name == stockpoint_names_in_db[1]
            assert routes[1].receiver.name == stockpoint_names_in_db[2]

        new_product_instance = product_class()
        if product_class is not FakeProduct:
            # Names in db match names in fresh product instance
            assert set(stockpoint_names_in_db) == set([stockpoint.name for stockpoint in new_product_instance.stock_points])
            assert len(routes) == len(new_product_instance.product.supply_routes)

        # ... but the actual objects are *not* the same
        assert set(latest_product_in_db.stock_points) != set(new_product_instance.stock_points)

        return new_highest_id_numbers


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
                later_dates = [date.today() + timedelta(days=5), date.today() + timedelta(days=15),
                               date.today() + timedelta(days=100)]

                for start_date in early_dates:

                    invalid_end_dates = list(filter(lambda d: d < start_date, later_dates))
                    for end_date in invalid_end_dates:
                        with pytest.raises(ValueError) as exc_info:
                            order_filter(test_session, stockpoint, start_date, end_date, incoming=True, outgoing=True)

                    valid_end_dates = list(filter(lambda d: d >= start_date, later_dates))
                    for end_date in valid_end_dates:
                        incoming_these_dates = order_filter(test_session, stockpoint, start_date, end_date,
                                                            incoming=True, outgoing=False)
                        outgoing_these_dates = order_filter(test_session, stockpoint, start_date, end_date,
                                                            incoming=False, outgoing=True)
                        all_orders_these_dates = order_filter(test_session, stockpoint, start_date, end_date,
                                                              incoming=True, outgoing=True)

                        assert set(incoming_these_dates) <= set(incoming_orders)
                        assert set(outgoing_these_dates) <= set(outgoing_orders)
                        assert set(all_orders_these_dates) <= set(all_orders)
                        assert set(all_orders_these_dates) == set(incoming_these_dates + outgoing_these_dates)

                        # assert consistent result between single-step and two-step filtering
                        assert incoming_these_dates == filter_by_date(incoming_orders, start_date, end_date)
                        assert outgoing_these_dates == filter_by_date(outgoing_orders, start_date, end_date)
            # Does not commit


class TestMoveExecution:
    def test_execute_moves(self):
        with Session(test_engine) as test_session_1:
            products = get_all(test_session_1, Product)
            for product in products:
                self.execute_move_tester(test_session_1, product)
            test_session_1.commit()

        with Session(test_engine) as test_session_2:
            self.execute_move_2(test_session_2)


    def execute_move_tester(self, session, product):
        for route in product.supply_routes:
            stockpoint = route.sender
            requests = route.move_requests
            for request in requests:
                simulated_request_fulfillment = request.quantity_delivered
                for order in request.move_orders:
                    # Status before execution
                    stock_before_this_order = stockpoint.current_stock
                    completion_status_before_execution = order.completion_status

                    # Assert that guardrails work
                    if order.quantity > stock_before_this_order:
                        with pytest.raises(ValueError) as exc_info:
                            execute_move(session, order)
                        assert "Cannot move more than the sender has!" in exc_info.value.args[0]
                        assert order.completion_status == completion_status_before_execution
                        assert stockpoint.current_stock == stock_before_this_order
                        assert simulated_request_fulfillment == order.request.quantity_delivered
                    elif order.completion_status != 0:
                        with pytest.raises(ValueError) as exc_info:
                            execute_move(session, order)
                        assert "Order is completed or invalid" in exc_info.value.args[0]
                        assert stockpoint.current_stock == stock_before_this_order
                        assert simulated_request_fulfillment == order.request.quantity_delivered

                    else:
                        execute_move(session, order)

                        # Expected effects
                        assert stockpoint.current_stock == stock_before_this_order - order.quantity
                        assert order.completion_status == 1 != completion_status_before_execution
                        assert order.request.quantity_delivered == simulated_request_fulfillment + order.quantity
                        simulated_request_fulfillment += order.quantity

                        # Cannot be executed again
                        with pytest.raises(ValueError) as exc_info:
                            execute_move(session, order)
                        assert "Order is completed or invalid" in exc_info.value.args[0]

    def execute_move_2(self, session):
        print('Started testing execute_move_2')
        for order in get_all(session, MoveOrder):
            # Cannot execute order_1 again
            with pytest.raises(ValueError) as exc_info:
                execute_move(session, order)
            assert "Order is completed or invalid" in exc_info.value.args[0] or "more than the sender has" in exc_info.value.args[0]


class TestAddItems:
    def test_add_requests(self):
        with Session(test_engine) as init_session:
            reset_and_fill_db(test_engine, init_session, [ProductA, FakeProduct, BranchingProduct])
            route_id_list = [route.id for route in get_all(init_session, SupplyRoute)]
            init_session.commit()
            last_premade_request_id = get_all(init_session, MoveRequest)[-1].id

        for route_id in route_id_list:
            with Session(test_engine) as add_request_session:
                route_from_db = get_by_id(add_request_session, SupplyRoute, route_id)
                add_request(add_request_session, route_from_db, date.today() + timedelta(days=4), 51)
                add_request_session.commit()

        with Session(test_engine) as session:
            # Ensure we have new requests
            assert get_all(session, MoveRequest)[-1].id > last_premade_request_id

    def test_add_moves(self):
        with Session(test_engine) as add_moves_session:
            for request in get_all(add_moves_session, MoveRequest):
                unanswered_quantity = request.unanswered_quantity()

                # Add two MoveOrder that together fulfills the request
                partial_order = MoveOrder(request=request, order_date=date.today() + timedelta(days=2), quantity=request.quantity // 2)
                add_moves_session.add(partial_order)

                fill_request(add_moves_session, request)
                fill_order = get_all(add_moves_session, MoveOrder)[-1]

                assert partial_order.quantity + fill_order.quantity == unanswered_quantity

            add_moves_session.commit()

        with Session(test_engine) as execute_moves_session:
            guard_clause_triggered = False
            for request in get_all(execute_moves_session, MoveRequest):
                assert request.unanswered_quantity() == 0
                no_moves_blocked = True
                for move in request.move_orders:
                    if move.completion_status != 0 or move.quantity > request.route.sender.current_stock:
                        guard_clause_triggered = True
                        no_moves_blocked = False
                        with pytest.raises(ValueError):
                            execute_move(execute_moves_session, move)
                    elif move.quantity < 0 and abs(move.quantity) > request.route.receiver.current_stock:
                        no_moves_blocked = False
                        with pytest.raises(ValueError):
                            execute_move(execute_moves_session, move)
                    else:
                        execute_move(execute_moves_session, move)

                if no_moves_blocked:
                    assert request.quantity_delivered == request.quantity
                    assert request.unanswered_quantity() == 0
            assert guard_clause_triggered



class TestOther:
    def test_capability(self):
        with Session(test_engine) as test_session:
            reset_and_fill_db(test_engine, test_session, [ProductA, FakeProduct, BranchingProduct])

        for route in get_all(test_session, SupplyRoute):
            # Should raise exceptions:
            incorrect_arguments = [-1, 0.3, "foo", date.today()]
            for arg in incorrect_arguments:
                with pytest.raises(ValueError) as exc_info:
                    deliverable = route.capability(arg)
                assert "Days to delivery must be a positive integer or zero." in exc_info.value.args[0]

            correct_arguments = [0, 1, 4, 60]
            for arg in correct_arguments:
                deliverable = route.capability(arg)
                assert isinstance(deliverable, int) and deliverable >= 0

        reset_db(test_engine)
