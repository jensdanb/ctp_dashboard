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
                ui.zone('control_zone', direction=ui.ZoneDirection.COLUMN, zones=[
                    ui.zone('control_zone_1', size='40%'),
                    ui.zone('control_zone_2', size='60%'),
                ]),
                ui.zone('data_bottom_zone'),
            ]
        ),
        ui.layout(
            breakpoint='m',
            zones=[
                ui.zone('header_zone'),
                ui.zone('control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('control_zone_1', size='40%'),
                    ui.zone('control_zone_2', size='60%'),
                ]),
                ui.zone('data_bottom_zone'),
            ]
        )
    ])


async def data_page(q: Q):
    if q.args.pre_fill_db:
        with dbm.Session(q.user.db_engine) as fill_session:
            dbm.add_from_class_if_db_is_empty(fill_session, CcrpBase)
        show_db_controls(q)
    else:
        show_db_controls(q)

# Data page functions
def show_db_controls(q: Q):
    q.page['db_controls'] = ui.form_card(
        box='data_bottom_zone',
        items=[
            ui.text_xl("Database Controls"),
            ui.button(name='pre_fill_db', label='Prefill database')
        ]
    )

