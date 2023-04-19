import database_model as dbm
from premade_db_content import CcrpBase

from h2o_wave import site, Q, ui, data, StatTableItem


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
        await show_move_orders(q, dbm.MoveOrder)
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


async def show_move_orders(q: Q, db_table: dbm.Base):

    with dbm.Session(q.user.db_engine) as list_move_orders_session:
        all_orders = dbm.get_all(list_move_orders_session, db_table)

    conversion_dict  = conversion_dicts[db_table]
    formatting_dict = formatting_dicts[db_table]

    title = db_table.__name__
    columns = list(conversion_dict.keys())
    items = build_stat_table(all_orders, conversion_dict, 'Move Order nr.')

    format_stat_table(items, formatting_dict)

    q.page['db_table'] = ui.stat_table_card(box='table_zone', title=title, columns=columns, items=items)


def build_stat_table(items, conversion_dict, label_arg):
    conversion_dict = conversion_dict.copy()
    label_attribute = conversion_dict.pop(label_arg)

    colors = ['black'] * len(conversion_dict)
    stat_table = []
    for item in items:
        label = str(item.__dict__[label_attribute])
        values = [str(item.__dict__[attribute]) for attribute in conversion_dict.values()]

        stat_table.append(ui.stat_table_item(label=label, values=values, colors=colors))

    return stat_table


def format_stat_table(stat_table_items, formating_dict):
    for target_index in formating_dict.keys():
        sub_dict = formating_dict[target_index]
        for item in stat_table_items:
            value = item.values[target_index]
            if value in sub_dict:
                item.values[target_index] = sub_dict[value]['display_value']
                item.colors[target_index] = sub_dict[value]['color']


conversion_dicts = {
    dbm.MoveOrder: {  # 'Column name': 'attribute name in db'.
        'Move Order nr.': 'id',
        'Completed/Pending': 'completion_status',
        'Quantity': 'quantity',
        'Planned Date': 'order_date',
        'Request ID': 'request_id'
    }
}

formatting_dicts = {
    dbm.MoveOrder: {
         0: {  # target_index 0
            '0': {'display_value': 'Pending', 'color': 'red'},
            '1': {'display_value': 'Completed', 'color': 'blue'}
        }
    }
}

