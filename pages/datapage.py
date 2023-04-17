import database_model as dbm
from premade_db_content import CcrpBase

from h2o_wave import site, Q, ui, data


""" DO NOT CHANGE header_zone WITHOUT ALSO CHANGING IT IN OTHER PAGES """
def layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            breakpoint='xs',
            zones=[
                ui.zone('header_zone'),
                ui.zone('data_bottom_zone'),
                ui.zone('control_zone', direction=ui.ZoneDirection.COLUMN, zones=[
                    ui.zone('control_zone_1', size='40%'),
                    ui.zone('control_zone_2', size='60%'),
                ]),
                ui.zone('table_zone'),
            ]
        ),
        ui.layout(
            breakpoint='m',
            zones=[
                ui.zone('header_zone'),
                ui.zone('data_bottom_zone'),
                ui.zone('control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('control_zone_1', size='40%'),
                    ui.zone('control_zone_2', size='60%'),
                ]),
                ui.zone('table_zone'),
            ]
        )
    ])


async def data_page(q: Q):
    if q.args.reset_db:
        with dbm.Session(q.user.db_engine) as fill_session:
            dbm.reset_db(q.user.db_engine)
            dbm.add_from_class_if_db_is_empty(fill_session, CcrpBase)
        show_db_controls(q)
    elif q.args.show_move_orders:
        await show_move_orders(q)
    else:
        show_db_controls(q)


# Data page functions
def show_db_controls(q: Q):
    q.page['db_controls'] = ui.form_card(
        box='data_bottom_zone',
        items=[
            ui.text_xl("Database Controls"),
            ui.button(name='reset_db', label='Reset Database'),
            ui.button(name='show_move_orders', label='Show All Move Orders')
        ]
    )


async def show_move_orders(q: Q):
    # Get data from db
    with dbm.Session(q.user.db_engine) as list_move_orders_session:
        all_orders = dbm.get_all(list_move_orders_session, dbm.MoveOrder)
        pending_orders = dbm.uncompleted_orders(all_orders)
        completed_orders = dbm.completed_orders(all_orders)

    # Convert to H2O Wave content
    pending_table = [
        ui.stat_table_item(
            label=str(order.id),
            values=['pending', str(order.quantity), order.order_date.isoformat(),
                    str(order.completion_status), str(order.request_id)],
            colors=['red'] + ['black'] * 4
        ) for order in pending_orders
    ]
    completed_table = [
        ui.stat_table_item(
            label=str(order.id),
            values=['completed', str(order.quantity), order.order_date.isoformat(),
                    str(order.completion_status), str(order.request_id)],
            colors=['red'] + ['black'] * 4
        ) for order in completed_orders
    ]

    full_table = pending_table + completed_table

    # Show H2O Wave content
    q.page['plot'] = ui.stat_table_card(
        box='table_zone',
        title='Move Orders',
        columns=['ID', 'completed/pending', 'Quantity', 'Planned Date', 'Completion Status', 'Request ID'],
        items=full_table
    )

