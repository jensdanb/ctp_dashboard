from databasing import database_model as dbm
from databasing.premade_db_content import CcrpBase, ProductB, FakeProduct

from h2o_wave import Q, ui


def get_selected(q: Q, session, table):
    match table:
        case dbm.Product:
            return dbm.get_by_id(session, dbm.Product, int(q.client.product_selection))
        case dbm.StockPoint:
            return dbm.get_by_id(session, dbm.StockPoint, int(q.client.stockpoint_selection))
        case dbm.SupplyRoute:
            raise NotImplementedError('No selection implemented for SupplyRoute!')
        case dbm.MoveRequest:
            raise NotImplementedError('No selection implemented for MoveRequest!')
        case dbm.MoveOrder:
            raise NotImplementedError('No selection implemented for MoveOrder!')
        case _:
            raise ValueError(f'Table argument {table} is not in {dbm.expected_orms_in_db}')


def product_dropdown(q: Q, session, trigger=False):
    products = dbm.get_all(session, dbm.Product)
    product_choices = [
        ui.choice(name=str(product.id), label=product.name)
        for product in products
    ]
    return ui.dropdown(name='product_selection',
                       label='Select Product',
                       value=q.client.product_selection,
                       choices=product_choices,
                       trigger=trigger)


def stockpoint_choice_group(q: Q, session, trigger=False):
    product = get_selected(q, session, dbm.Product)
    valid_stockpoints = product.stock_points
    stockpoint_choices = [
        ui.choice(name=str(stockpoint.id), label=stockpoint.name)
        for stockpoint in valid_stockpoints
    ]
    return ui.choice_group(name='stockpoint_selection',
                           label='Select Stockpoint',
                            value=q.client.stockpoint_selection,
                           choices=stockpoint_choices,
                           trigger=trigger)
