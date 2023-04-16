import pandas as pd

from premade_db_content import CcrpBase

from stock_projection_2D import *
import pytest
from sqlalchemy.orm import exc


def strictly_positive_and_increasing(values: pd.Series):
    differences = values.diff()
    positive = not any([value < 0 for value in values])
    increasing = not any([increase < 0 for increase in differences])
    return positive and increasing


def universal_projection_assertions(session, projection):
    stockpoint_in_db = get_by_name(session, StockPoint, projection.stockpoint_name)
    # Consistency with database:
    assert projection.stockpoint_id == stockpoint_in_db.id
    assert projection.start


    assert projection.start_date < projection.final_date
    assert isinstance(projection.df, pd.DataFrame) and not projection.df.empty

class TestStockProjection:
    # Setup inputs

    def test_initialization(self):
        run_with_session(test_engine, add_from_class, input_class=CcrpBase)
        with Session(test_engine) as test_session:
            all_stockpoints = get_all(test_session, StockPoint)

            """ invalid arguments raise exceptions: """
            invalid_sessions = [test_engine, StockPoint, None, "foo"]
            for invalid_session in invalid_sessions:
                with pytest.raises(AttributeError):
                    projection = StockProjection(invalid_session, all_stockpoints[0])

            invalid_db_objects = []
            for table in expected_db_orms - {StockPoint}:
                invalid_db_objects += get_all(test_session, table)

            for invalid_object in invalid_db_objects:
                with pytest.raises(AttributeError) as exc_info:
                    projection = StockProjection(test_session, invalid_object)

            """ valid arguments do not raise exceptions: """
            for stockpoint in all_stockpoints:
                projection = StockProjection(test_session, stockpoint)

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)

    def test_post_init(self):
        # basic init, repeat of test_initialization
        run_with_session(test_engine, add_from_class, input_class=CcrpBase)
        with Session(test_engine) as test_session:
            test_sp = get_by_name(test_session, StockPoint, "finished goods")
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
                assert projection.start_date < projection.final_date
                assert isinstance(projection.df, pd.DataFrame) and not projection.df.empty

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)


class TestATP:
    def test_atp(self):
        # Arrange setup
        run_with_session(test_engine, add_from_class, input_class=CcrpBase)
        with Session(test_engine) as test_session:
            all_stockpoints = get_all(test_session, StockPoint)

            for stockpoint in all_stockpoints:
                projection = ProjectionATP(test_session, stockpoint)
                assert projection.plot
                assert strictly_positive_and_increasing(projection.df['ATP'])

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)


class TestCTP:
    def test_ctp(self):
        # Arrange setup
        run_with_session(test_engine, add_from_class, input_class=CcrpBase)
        with Session(test_engine) as init_sesssion:
            sp_1 = get_by_name(init_sesssion, StockPoint, "unfinished goods")
            sp_2 = get_by_name(init_sesssion, StockPoint, "finished goods")
            projection1 = ProjectionCTP(init_sesssion, sp_1)
            projection2 = ProjectionCTP(init_sesssion, sp_2)

        # Stockpoint with nothing incoming:
        with Session(test_engine) as ctp_session1:
            assert projection1.df['CTP'].equals(projection1.df['ATP'])

        with Session(test_engine) as ctp_session2:
            inc_routes = get_incoming_routes(ctp_session2, sp_2)
            out_routes = get_outgoing_routes(ctp_session2, sp_2)

            # Outgoing route is invalid and raises error
            with pytest.raises(NotImplementedError):
                projection2.project_ctp(out_routes[0])

            # Incoming route works
            assert 'ATP' in projection2.df.keys()
            assert not projection2.df.filter(like='CTP', axis=1).empty  # Proves new column for CTP was added

            # CTP is strictly positive and increasing.
            for column_name in projection2.df.filter(like='CTP', axis=1):
                column = projection2.df[column_name]
                assert strictly_positive_and_increasing(column)

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)
