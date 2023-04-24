from databasing.premade_db_content import ProductB, FakeProduct
import databasing.database_model as dbm

from pyvis.network import Network
import networkx as nx


def graph_supply_chain(session, product: dbm.Product):
    graph = nx.DiGraph()

    node_list = [(stockpoint.id, {'label': stockpoint.name, 'y': 100 * stockpoint.id}) for stockpoint in product.stock_points]
    graph.add_nodes_from(node_list)

    edge_list = [(route.sender_id, route.receiver_id, {'label': f'Route {route.id}'}) for route in product.supply_routes]
    graph.add_edges_from(edge_list)

    # Visual placement


    return graph


if __name__ == "__main__":
    graph_test_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    with dbm.Session(graph_test_engine) as init_session:
        dbm.reset_db(graph_test_engine)
        dbm.add_from_class(init_session, ProductB)
        init_session.commit()



    with dbm.Session(graph_test_engine) as netting_session:
        product_b: dbm.Product = dbm.get_by_id(netting_session, dbm.Product, 1)
        graph_b = graph_supply_chain(netting_session, product_b)

    net_b = Network('500px', '500px')
    net_b.from_nx(graph_b)
    net_b.show('nx.html')