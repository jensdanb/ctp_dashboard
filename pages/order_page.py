import databasing.database_model as dbm
from pages.shared_content import show_table, product_dropdown, supply_route_choice_group
from h2o_wave import site, Q, ui


def layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(breakpoint='xs',
            zones=[
                ui.zone('header_zone'),  # DO NOT CHANGE header_zone WITHOUT ALSO CHANGING IT IN OTHER PAGES
                ui.zone('order_control_zone', direction=ui.ZoneDirection.COLUMN, zones=[
                    ui.zone('order_control_zone_a', size='50%'),
                    ui.zone('order_control_zone_b', size='50%'),
                ]),
                ui.zone('order_table_zone'),

            ]
        ),
        ui.layout(
            breakpoint='m',
            zones=[
                ui.zone('header_zone'),
                ui.zone('order_control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('order_control_zone_a', size='50%'),
                    ui.zone('order_control_zone_b', size='50%'),
                ]),
                ui.zone('order_table_zone'),

            ]
        )
    ])


async def serve_order_page(q:Q):
    if q.args.show_move_requests:
        with dbm.Session(q.user.db_engine) as session:
            show_table(q, session, dbm.MoveRequest, box='order_table_zone')
    elif q.args.show_move_orders:
        with dbm.Session(q.user.db_engine) as session:
            show_table(q, session, dbm.MoveOrder, box='order_table_zone')
    else:
        with dbm.Session(q.user.db_engine) as session:
            show_sc_controls(q, session)


def show_sc_controls(q: Q, session):
    product_selector = product_dropdown(q, session, trigger=True)
    route_selector = supply_route_choice_group(q, session, trigger=False)
    q.page['sc_controls'] = ui.form_card(
        box='order_control_zone_a',
        items=[
            ui.text_l("Database Controls"),
            product_selector,
            route_selector,
            ui.button(name='show_move_requests', label='Table: Move Requests'),
            ui.button(name='show_move_orders', label='Table: Move Orders')
        ]
    )


def show_welcome(q: Q):
    q.page['welcome'] = ui.form_card(box='order_control_zone_b', items=[
        ui.text_l(f'Welcome, this page is empty'),
        ui.text(f"Nothing to see here yet. Please navigate to the other pages with the navigation header up top. ")
    ])