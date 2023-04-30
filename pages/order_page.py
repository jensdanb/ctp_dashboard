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

    show_sc_controls(q)
    show_welcome(q)


def show_sc_controls(q: Q):
    q.page['sc_controls'] = ui.form_card(
        box='order_control_zone_a',
        items=[
            ui.text_l("Database Controls"),

            ui.button(name='show_move_requests', label='Table: Move Requests'),
            ui.button(name='show_move_orders', label='Table: Move Orders')
        ]
    )


def show_welcome(q: Q):
    q.page['welcome'] = ui.form_card(box='order_control_zone_b', items=[
        ui.text_l(f'Welcome, this page is empty'),
        ui.text(f"Nothing to see here yet. Please navigate to the other pages with the navigation header up top. ")
    ])