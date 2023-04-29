from databasing import database_model as dbm

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
    stockpoint_choices = assemble_choices(q, session, dbm.Product, 'stock_points')
    return ui.choice_group(name='stockpoint_selection',
                           label='Select Stockpoint',
                           value=q.client.stockpoint_selection,
                           choices=stockpoint_choices,
                           trigger=trigger)


def supply_route_choice_group(q: Q, session, trigger=False):
    supply_routes_choices = assemble_choices(q, session, dbm.Product, 'supply_routes')
    return ui.choice_group(name='supply_route_selection',
                           label='Select Route',
                           value=q.client.stockpoint_selection,
                           choices=supply_routes_choices,
                           trigger=trigger)


def assemble_choices(q: Q, session, owner_category: dbm.Base, target_attr_in_owner):
    match (owner_category, target_attr_in_owner):
        case (dbm.Product, 'stock_points'):
            owner = get_selected(q, session, owner_category)
            items = getattr(owner, target_attr_in_owner)
            choices = [
                ui.choice(name=str(item.id), label=item.name)
                for item in items
            ]
            return choices

        case (dbm.Product, 'supply_routes') | (dbm.SupplyRoute, 'move_requests') | (dbm.MoveRequest, 'move_orders'):
            owner = get_selected(q, session, owner_category)
            items = getattr(owner, target_attr_in_owner)
            choices = [
                ui.choice(name=str(item.id), label=item.id)
                for item in items
            ]
            return choices

        case _:
            raise ValueError(f'{owner_category} and {target_attr_in_owner} is not a valid combination.')
