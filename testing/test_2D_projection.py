import pandas as pd

from db_premade_content_for_testing import CcrpBase

from stock_projection_2D import *
import pytest
from sqlalchemy.orm import exc


def strictly_positive_and_increasing(values: pd.Series):
    differences = values.diff()
    positive = not any([value < 0 for value in values])
    increasing = not any([increase < 0 for increase in differences])
    return positive and increasing


class TestStockProjection:
    # Setup inputs

    def test_initialization(self):
        with Session(test_engine) as test_session:
            run_with_session(test_engine, add_from_class, input_class=CcrpBase)
            all_stockpoints = get_all(test_session, StockPoint)

            """ invalid arguments raise exceptions: """
            invalid_sessions = [test_engine, StockPoint, None, "foo"]
            for invalid_session in invalid_sessions:
                with pytest.raises(AttributeError):
                    projection = ProjectionATP(invalid_session, all_stockpoints[0])

            invalid_db_objects = []
            for table in all_db_tables - {StockPoint}:
                invalid_db_objects += get_all(test_session, table)

            for invalid_object in invalid_db_objects:
                with pytest.raises(AttributeError) as exc_info:
                    projection = ProjectionATP(test_session, invalid_object)

            """ valid arguments do not raise exceptions: """
            for stockpoint in all_stockpoints:
                projection = ProjectionATP(test_session, stockpoint)

                """ logic and content is correct for all stockpoints """
                assert projection.start_date < projection.final_date
                assert isinstance(projection.df, pd.DataFrame) and not projection.df.empty
                assert projection.plot

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)

    def test_post_init(self):
        # basic init, repeat of test_initialization
        with Session(test_engine) as test_session:
            run_with_session(test_engine, add_from_class, input_class=CcrpBase)
            test_sp = get_by_name(test_session, StockPoint, "crp_1501")
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

            # ATP is strictly positive and increasing
            assert strictly_positive_and_increasing(projection.df['ATP'])

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)


class TestCTP:
    def test_ctp(self):
        # Arrange setup
        with Session(test_engine) as init_sesssion:
            run_with_session(test_engine, add_from_class, input_class=CcrpBase)
            test_sp = get_by_name(init_sesssion, StockPoint, "crp_1501")
            projection = ProjectionCTP(init_sesssion, test_sp)

        with Session(test_engine) as ctp_session:
            inc_routes = get_incoming_routes(ctp_session, test_sp)
            out_routes = get_outgoing_routes(ctp_session, test_sp)

            # Outgoing route is invalid and raises error
            with pytest.raises(NotImplementedError):
                projection.project_ctp(out_routes[0])

            # Incoming route works
            assert 'ATP' in projection.df.keys()
            assert not projection.df.filter(like='CTP_route', axis=1).empty  # Proves new column for CTP was added

            # CTP is strictly positive and increasing.
            for column_name in projection.df.filter(like='CTP_route', axis=1):
                column = projection.df[column_name]
                assert strictly_positive_and_increasing(column)

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)
