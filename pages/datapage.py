from databasing import database_model as dbm
from databasing.premade_db_content import ProductA, FakeProduct, BranchingProduct
import databasing.relationship_graphing as graphing
from pages.shared_content import get_selected, product_dropdown

from h2o_wave import Q, ui


def layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            breakpoint='xs',
            zones=[
                ui.zone('header_zone'),  # DO NOT CHANGE header_zone WITHOUT ALSO CHANGING IT IN OTHER PAGES
                ui.zone('db_control_zone', direction=ui.ZoneDirection.COLUMN, zones=[
                    ui.zone('db_control_zone_a', size='50%'),
                    ui.zone('db_control_zone_b', size='50%'),
                ]),
                ui.zone('graph_zone'),
                ui.zone('table_zone'),

            ]
        ),
        ui.layout(
            breakpoint='m',
            zones=[
                ui.zone('header_zone'),
                ui.zone('db_control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('db_control_zone_a', size='50%'),
                    ui.zone('db_control_zone_b', size='50%'),
                ]),
                ui.zone('graph_zone'),
                ui.zone('table_zone'),

            ]
        )
    ])


async def data_page(q: Q):
    if q.args.reset_db:
        with dbm.Session(q.user.db_engine) as fill_session:
            dbm.reset_and_fill_db(q.user.db_engine, fill_session, [ProductA, FakeProduct, BranchingProduct])
            fill_session.commit()
        show_sc_overview(q)
    elif q.args.show_supply_routes:
        with dbm.Session(q.user.db_engine) as session:
            await show_db_contents(q, session, getattr(dbm, q.args.show_supply_routes))
    elif q.args.show_move_requests:
        with dbm.Session(q.user.db_engine) as session:
            await show_db_contents(q, session, dbm.MoveRequest)
    elif q.args.show_move_orders:
        with dbm.Session(q.user.db_engine) as session:
            await show_db_contents(q, session, dbm.MoveOrder)
    elif q.args.show_graph:
        with dbm.Session(q.user.db_engine) as session:
            show_graph(q, session)
    else:
        show_sc_overview(q)
        show_db_controls(q)


def show_sc_overview(q: Q):
    with dbm.Session(q.user.db_engine) as session:
        product_selector = product_dropdown(q, session, trigger=True)
    q.page['sc_overview'] = ui.form_card(
        box='db_control_zone_a',
        items=[
            ui.text_xl("Supply Chain Overview"),
            product_selector,
            ui.button(name='show_supply_routes', label='Table: Supply Routes', value='SupplyRoute'),
            ui.button(name='show_graph', label='Graph: Supply Routes'),
        ]
    )


def show_db_controls(q: Q):
    q.page['db_controls'] = ui.form_card(
        box='db_control_zone_b',
        items=[
            ui.text_xl("Database Controls"),
            ui.button(name='reset_db', label='Reset Database'),
            ui.button(name='show_move_requests', label='Table: Move Requests'),
            ui.button(name='show_move_orders', label='Table: Move Orders')
        ]
    )


def show_graph(q: Q, session):
    selected_product: dbm.Product = get_selected(q, session, dbm.Product)
    html_content = graphing.product_to_html_str(session, selected_product)

    graph_pixels = 250 +len(selected_product.supply_routes) * 50
    q.page['graph'] = ui.form_card(
        box='graph_zone',
        items=[
            ui.text_xl('Graph: Supply Chain for product ' + selected_product.name),
            ui.frame(content=html_content, height=f'{str(graph_pixels)}px', width=f'{str(graph_pixels)}px')
        ]
    )



async def show_db_contents(q: Q, session, db_table: dbm.Base):
    title = db_table.__name__
    all_items = dbm.get_all(session, db_table)

    conversion_dict  = conversion_dicts[db_table]
    columns = [title] + list(conversion_dict.keys())
    items = build_stat_table(all_items, conversion_dict)

    items = format_stat_table(items, db_table)

    q.page['db_table'] = ui.stat_table_card(box='table_zone', title=title+'s', columns=columns, items=items)


def build_stat_table(items, conversion_dict):
    colors = ['black'] * len(conversion_dict)
    stat_table = []
    for item in items:
        label = str(item.id)
        values = [str(getattr(item, attribute)) for attribute in conversion_dict.values()]

        stat_table.append(ui.stat_table_item(label=label, values=values, colors=colors.copy()))

    return stat_table


def format_stat_table(stat_table_items, item_type):
    if item_type is dbm.MoveOrder:
        return [format_table_item_move_order(item) for item in stat_table_items]
    elif item_type is dbm.MoveRequest:
        return [format_table_item_supply_route(item) for item in stat_table_items]
    else:
        print('No formatting function!')
        return stat_table_items


conversion_dicts = {
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


def format_table_item_supply_route(item):
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
