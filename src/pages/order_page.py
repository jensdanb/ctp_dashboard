import datetime

import src.databasing.database_model as dbm
from src.pages.shared_content import get_selected, show_children, product_dropdown, supply_route_choice_group
from h2o_wave import Q, ui


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
            show_children(q, session, dbm.MoveRequest, box='order_table_zone', parent=get_selected(q, session, dbm.SupplyRoute))
    elif q.args.show_move_orders:
        with dbm.Session(q.user.db_engine) as session:
            show_children(q, session, dbm.MoveOrder, box='order_table_zone', parent=get_selected(q, session, dbm.SupplyRoute))
    elif q.args.make_request:
        make_request(q)
    elif q.args.submit_request:
        with dbm.Session(q.user.db_engine) as session:
            submit_request(q, session)
            show_order_controls(q, session)
    else:
        with dbm.Session(q.user.db_engine) as session:
            show_order_controls(q, session)


def show_order_controls(q: Q, session, message=''):
    product_selector = product_dropdown(q, session, trigger=True)
    route_selector = supply_route_choice_group(q, session, trigger=False)
    q.page['sc_controls'] = ui.form_card(
        box='order_control_zone_a',
        items=[
            ui.text_l(message),
            product_selector,
            route_selector,
            ui.button(name='make_request', label='Make Request'),
            ui.button(name='show_move_requests', label='Table: Move Requests'),
            ui.button(name='show_move_orders', label='Table: Move Orders')
        ]
    )


def make_request(q: Q, message=''):
    route_id = int(q.client.supply_route_selection)
    default_date = datetime.date.today()
    date_value = default_date.isoformat()
    q.page['sc_controls'] = ui.form_card(
        box='order_control_zone_a',
        items=[
            ui.text_m(message),
            ui.text_l(f'Add Request to route {route_id}'),
            ui.date_picker(name='request_date_picker', label='Requested Delivery', value=date_value),
            ui.spinbox(name='request_quantity', label='Requested Quantity', min=0, max=10000, value=30, step=1),
            ui.button(name='submit_request', label='Submit Request')
        ]
    )


def submit_request(q, session):
    picked_date_str = q.client.request_date_picker
    day_picked = datetime.date.fromisoformat(picked_date_str)
    quantity = int(q.client.request_quantity)
    if day_picked >= datetime.date.today() and quantity in range(-1000, 10000):
        route = get_selected(q, session, dbm.SupplyRoute)
        dbm.add_request(session, route, req_date=day_picked, quantity=quantity)
        session.commit()
    else:
        pass


def show_welcome(q: Q):
    q.page['welcome'] = ui.form_card(box='order_control_zone_b', items=[
        ui.text_l(f'Welcome, this page is empty'),
        ui.text(f"Nothing to see here yet. Please navigate to the other pages with the navigation header up top. ")
    ])