from main import *
import pytest


def capture_sql(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except exc.SQLAlchemyError as e:
        return e


def test_database_initializes_():
    with Session(test_engine) as test_session:

        assert get_all(test_session, Product) == []
        premake_db(test_session, CcrpBase)
        assert get_all(test_session, Product)

        # Product ccrp is in
        assert get_by_name(test_session, Product, "ccrp_ip") in get_all(test_session, Product)
        assert [stockpoint.name for stockpoint in get_all(test_session, StockPoint)] == ["crp_raw", "crp_1501", "crp_shipped"]
        assert get_all(test_session, SupplyRoute) and len(get_all(test_session, SupplyRoute)) == 2

        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)

