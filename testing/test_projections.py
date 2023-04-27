from databasing.premade_db_content import ProductA, FakeProduct
from projection import *

import pytest
from sqlalchemy.orm import exc


def strictly_increasing(values: pd.Series):
    differences = values.diff()
    increasing = not any([diff < 0 for diff in differences])
    return increasing


def universal_projection_assertions(session, projection):
    stockpoint_in_db = get_by_name(session, StockPoint, projection.stockpoint_name)
    # Consistency with database:
    assert projection.stockpoint_id == stockpoint_in_db.id
    assert isinstance(projection.start_date, date)
    assert projection.start_date < projection.final_date
    assert isinstance(projection.df, pd.DataFrame) and not projection.df.empty


class TestStockProjection:
    # Setup inputs
    def test_initialization(self):
        for product_class in [ProductA, FakeProduct]:
            run_with_session(test_engine, add_from_class, input_class=product_class)
            with Session(test_engine) as init_session:
                all_stockpoints = get_all(init_session, StockPoint)

                """ invalid arguments raise exceptions: """
                invalid_sessions = [test_engine, StockPoint, None, "foo"]
                for invalid_session in invalid_sessions:
                    with pytest.raises(AttributeError):
                        projection = StockProjection(invalid_session, all_stockpoints[0])

                invalid_db_objects = [get_all(init_session, table) for table in expected_orms_in_db - {StockPoint}]
                for invalid_object in invalid_db_objects:
                    with pytest.raises(AttributeError) as exc_info:
                        projection = StockProjection(init_session, invalid_object)

                """ valid arguments do not raise exceptions: """
                for stockpoint in all_stockpoints:
                    projection = StockProjection(init_session, stockpoint)

    def test_post_init(self):
        with Session(test_engine) as test_session:
            test_sp = get_by_id(test_session, StockPoint, 2)  # In ProductA: "Finished goods"
            projection = ProjectionATP(test_session, test_sp)

        # check we are disconnected from database
        with pytest.raises(exc.DetachedInstanceError):
            print(test_sp)
        # yet the projection is still available:
        assert projection

        # and we can "reconnect" with a new session and the name attribute
        with Session(test_engine) as test_session:
            new_sp = get_by_name(test_session, StockPoint, projection.stockpoint_name)
            new_projection = ProjectionATP(test_session, new_sp)
            assert new_projection.df.equals(projection.df)

        # Finally, we test that "business logic" is correct for all stockpoints:
        with Session(test_engine) as test_session:
            all_stockpoints = get_all(test_session, StockPoint)
            for stockpoint in all_stockpoints:
                projection = StockProjection(test_session, stockpoint)
                universal_projection_assertions(test_session, projection)


class TestATP:
    def test_atp(self):
        # Arrange setup
        with Session(test_engine) as test_session:
            all_stockpoints = get_all(test_session, StockPoint)

            for stockpoint in all_stockpoints:
                projection = ProjectionATP(test_session, stockpoint)
                assert projection.plot
                assert strictly_increasing(projection.df['ATP'])


class TestCTP:
    def test_determined_ctp_projections(self):
        # Known stockpoints
        with Session(test_engine) as ctp_session1:
            sp_1 = get_by_name(ctp_session1, StockPoint, "Unfinished goods")
            sp_2 = get_by_name(ctp_session1, StockPoint, "Finished goods")
            projection1 = ProjectionCTP(ctp_session1, sp_1)
            projection2 = ProjectionCTP(ctp_session1, sp_2)

        # Stockpoint with nothing incoming:
        assert projection1.df['CTP'].equals(projection1.df['ATP'])

        with Session(test_engine) as ctp_session2:
            inc_routes = get_incoming_routes(ctp_session2, sp_2)
            out_routes = get_outgoing_routes(ctp_session2, sp_2)

            # Outgoing route is invalid and raises error
            with pytest.raises(NotImplementedError):
                projection2.project_ctp(out_routes)

    def test_randomised_projections(self):
        with Session(test_engine) as ctp_session_random:
            faked_product = get_by_id(ctp_session_random, Product, 2)
            for stockpoint in faked_product.stock_points:  # id 2 belonging to FakeProduct
                projection = ProjectionCTP(ctp_session_random, stockpoint)

                # Incoming route is valid and CTP column was created
                assert 'CTP' in projection.df.keys()
                ctp_column = projection.df['CTP']
                assert not ctp_column.empty

                # CTP is bigger than ATP and strictly increasing.
                bigger_than_ATP = ctp_column >= projection.df['ATP']
                assert bigger_than_ATP.all()

                if not strictly_increasing(ctp_column):
                    print('Inventory:')
                    # print(projection.df['supply'].to_string())
                    print(np.cumsum(projection.df['supply']).to_string())
                    print('CTP:')
                    print(ctp_column.to_string())
                assert strictly_increasing(ctp_column)

        reset_db(test_engine)
