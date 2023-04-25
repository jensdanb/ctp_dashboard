from databasing.premade_db_content import ProductB, FakeProduct
import databasing.database_model as dbm

from pyvis.network import Network
import networkx as nx
from os import remove


def graph_supply_chain(session, product: dbm.Product):
    graph = nx.DiGraph()

    node_list = [(stockpoint.id, {'label': stockpoint.name, 'y': 100 * stockpoint.id}) for stockpoint in product.stock_points]
    graph.add_nodes_from(node_list)

    edge_list = [(route.sender_id, route.receiver_id, {'label': f'Route {route.id}'}) for route in product.supply_routes]
    graph.add_edges_from(edge_list)

    return graph


def graph_to_net(graph: nx.DiGraph):
    pixel_height = str(50 + 100 * len(graph.nodes))
    net = Network(f'{pixel_height}px', f'350px')
    net.from_nx(graph)
    return net


def net_to_html_str(net: Network):
    filename = 'net.html'
    net.write_html(filename)

    text = """"""
    for line in open(filename):
        text += line
    # remove(filename)
    return text


def save_net_as_html(net: Network, filename):
    net.save_graph(filename)


if __name__ == "__main__":
    graph_test_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    with dbm.Session(graph_test_engine) as init_session:
        dbm.reset_db(graph_test_engine)
        dbm.add_from_class(init_session, ProductB)
        dbm.add_from_class(init_session, FakeProduct)
        init_session.commit()



    with dbm.Session(graph_test_engine) as netting_session:
        fake_product: dbm.Product = dbm.get_by_id(netting_session, dbm.Product, 2)
        graph_b = graph_supply_chain(netting_session, fake_product)

    net_b = graph_to_net(graph_b)
    content = net_to_html_str(net_b)

    print(content)

