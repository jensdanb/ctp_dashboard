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
                           trigger=trigger, inline=True)


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
                ui.choice(name=str(item.id), label=str(item.id))
                for item in items
            ]
            return choices

        case _:
            raise ValueError(f'{owner_category} and {target_attr_in_owner} is not a valid combination.')


def show_table(q: Q, session, db_table: dbm.Base, box):
    title = db_table.__name__
    all_items = dbm.get_all(session, db_table)

    conversion_dict  = table_conversion_dicts[db_table]
    columns = [title] + list(conversion_dict.keys())
    items = build_stat_table(all_items, conversion_dict)

    items = format_stat_table(items, db_table)

    q.page['db_table'] = ui.stat_table_card(box=box, title=title+'s', columns=columns, items=items)


def build_stat_table(items, conversion_dict):
    colors = ['black'] * len(conversion_dict)
    stat_table = []
    for item in items:
        label = str(item.id)
        values = [str(getattr(item, attribute)) for attribute in conversion_dict.values()]

        stat_table.append(ui.stat_table_item(label=label, values=values, colors=colors.copy()))

    return stat_table


def format_stat_table(stat_table_items, item_type):
    match item_type:
        case dbm.MoveOrder:
            return [format_table_item_move_order(item) for item in stat_table_items]
        case dbm.MoveRequest:
            return [format_table_item_move_request(item) for item in stat_table_items]
        case _:
            print('No formatting function!')
            return stat_table_items


table_conversion_dicts = {
    dbm.Product: {  # 'Column name': 'attribute name in db'.
        'Name': 'name',
        'Price': 'price',
    },
    dbm.StockPoint: {  # 'Column name': 'attribute name in db'.
        'Name': 'name',
        'Product ID': 'product_id',
        'Current Stock': 'current_stock',
    },
    dbm.SupplyRoute: {  # 'Column name': 'attribute name in db'.
        'Product ID': 'product_id',
        'Sender Stockpoint ID': 'sender_id',
        'Receiver Stockpoint ID': 'receiver_id',
        'Capacity': 'capacity',
        'Lead Time': 'lead_time'
    },
    dbm.MoveRequest: {  # 'Column name': 'attribute name in db'.
        'Quantity Ordered': 'quantity',
        'Quantity Delivered': 'quantity_delivered',
        'Registered Date': 'date_of_registration',
        'Requested Delivery Date': 'requested_delivery_date',
        'Route ID': 'route_id',
    },
    dbm.MoveOrder: {  # 'Column name': 'attribute name in db'.
        'Completed/Pending': 'completion_status',
        'Quantity': 'quantity',
        'Planned Date': 'order_date',
        'Request ID': 'request_id'
    },
}


def format_table_item_move_request(item):
    quantity_ordered = int(item.values[0])
    quantity_delivered = int(item.values[1])
    if quantity_delivered < quantity_ordered // 2:
        item.colors[1] = 'red'
    elif quantity_delivered < quantity_ordered * 0.9:
        item.colors[1] = 'orange'
    elif quantity_delivered == quantity_ordered:
        item.colors[1] = 'blue'
    elif quantity_delivered > quantity_ordered:
        item.colors[1] = 'pink'
    return item


def format_table_item_move_order(item):
    completion_status = int(item.values[0])
    if completion_status == 0:
        item.values[0] = 'Pending'
        item.colors[0] = 'red'
    elif completion_status == 1:
        item.values[0] = 'Completed'
        item.colors[0] = 'blue'
    return item

