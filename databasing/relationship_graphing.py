from databasing.premade_db_content import ProductA, FakeProduct, BranchingProduct
import databasing.database_model as dbm

from pyvis.network import Network
import networkx as nx
from os import remove


def product_to_graph(session, product: dbm.Product):
    graph = nx.DiGraph()

    node_list = [(stockpoint.id, {'label': stockpoint.name}) for stockpoint in product.stock_points]  # , 'y': 100 * stockpoint.id
    graph.add_nodes_from(node_list)

    edge_list = [(route.sender_id, route.receiver_id, {'label': f'Route {route.id}'}) for route in product.supply_routes]
    graph.add_edges_from(edge_list)

    return graph


""" WARNING: Tests for these two functions are by default commented out from test_all, to avoid browser spam """
""" When changing these, make sure to reactivate and run the tests in test_all """


def graph_to_net(graph: nx.DiGraph):
    pixel_height = str(230 + 50 * len(graph.edges))
    net = Network(height=f'{pixel_height}px', width=f'{pixel_height}px', directed=True)
    net.toggle_physics(False)
    net.from_nx(graph)
    return net


def net_to_html_str(net: Network):
    filename = 'net.html'
    net.write_html(filename)
    text = """"""
    for line in open(filename):
        text += line
    remove(filename)
    return text


def product_to_html_str(session, product):
    sc_graph = product_to_graph(session, product)
    net = graph_to_net(sc_graph)
    html_string = net_to_html_str(net)
    return html_string


""" WARNING: Tests for these three functions are commented out by default, to avoid html spam when running test_all"""


def save_net_as_html(net: Network, filename):
    net.save_graph(filename)


if __name__ == "__main__":
    graph_test_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    with dbm.Session(graph_test_engine) as init_session:
        dbm.reset_db(graph_test_engine)
        dbm.add_from_class(init_session, ProductA)
        dbm.add_from_class(init_session, FakeProduct)
        init_session.commit()



    with dbm.Session(graph_test_engine) as netting_session:
        fake_product: dbm.Product = dbm.get_by_id(netting_session, dbm.Product, 2)
        graph_b = product_to_graph(netting_session, fake_product)

    net_b = graph_to_net(graph_b)
    net_b.show('name.html')

