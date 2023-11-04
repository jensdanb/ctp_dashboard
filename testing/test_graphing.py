from databasing.relationship_graphing import *

import pytest


def test_product_graph():
    with dbm.Session(dbm.test_engine) as init_session:
        dbm.reset_and_fill_db(dbm.test_engine, init_session, [ProductA, FakeProduct])
        init_session.commit()

    with dbm.Session(dbm.test_engine) as test_session:
        for product in dbm.get_all(test_session, dbm.Product):
            graph = product_to_graph(test_session, product)

            # Graph has correct content
            assert isinstance(graph, nx.DiGraph)
            assert set(graph.nodes) == set([stockpoint.id for stockpoint in product.stock_points])
            assert set(graph.edges) == set([(route.sender_id, route.receiver_id) for route in product.supply_routes])

            # And no duplicates
            assert len(set(graph.nodes)) == len(graph.nodes)
            assert len(set(graph.edges)) == len(graph.edges)


def test_graph_conversion():
    with dbm.Session(dbm.test_engine) as test_session:
        for product in dbm.get_all(test_session, dbm.Product):

            graph = product_to_graph(test_session, product)
            net = graph_to_net(graph)
            assert isinstance(net, Network)


def test_html_result():
    with dbm.Session(dbm.test_engine) as test_session:
        for product in dbm.get_all(test_session, dbm.Product):

            graph = product_to_graph(test_session, product)
            net = graph_to_net(graph)
            html_string = net_to_html_str(net)

            assert isinstance(html_string, str)
            assert html_string[:6] == '<html>' and html_string[-7:] == '</html>'

            # product_to_html_str() does all the above in one function
            assert product_to_html_str(test_session, product) == html_string

