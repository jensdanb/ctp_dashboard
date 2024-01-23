from h2o_wave import Q, ui

from ..databasing import database_model as dbm
from ..databasing.premade_db_content import ProductA, FakeProduct, BranchingProduct
from ..databasing import relationship_graphing as graphing
from .shared_content import get_selected, product_dropdown, show_table



def layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            breakpoint='xs',
            zones=[
                ui.zone('header_zone'),  # DO NOT CHANGE header_zone WITHOUT ALSO CHANGING IT IN OTHER PAGES
                ui.zone('sc_control_zone', direction=ui.ZoneDirection.COLUMN, zones=[
                    ui.zone('sc_control_zone_a', size='50%'),
                    ui.zone('sc_control_zone_b', size='50%'),
                ]),
                ui.zone('graph_zone'),
                ui.zone('table_zone'),

            ]
        ),
        ui.layout(
            breakpoint='l',
            zones=[
                ui.zone('header_zone'),
                ui.zone('sc_control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('sc_control_zone_a', size='40%'),
                    ui.zone('sc_control_zone_b', size='60%'),
                ]),
                ui.zone('graph_zone'),
                ui.zone('table_zone'),

            ]
        )
    ])


async def serve_supply_chain_page(q: Q):
    if q.args.reset_db:
        with dbm.Session(q.user.db_engine) as session:
            dbm.reset_and_fill_db(q.user.db_engine, session, [ProductA, FakeProduct, BranchingProduct])
            session.commit()

            update_sc_cards(q, session)

    elif q.args.show_graph:
        with dbm.Session(q.user.db_engine) as session:
            show_graph(q, session)
    else:
        with dbm.Session(q.user.db_engine) as session:
            update_sc_cards(q, session)


def update_sc_cards(q: Q, session):
    show_graph(q, session)
    show_table(q, session, dbm.SupplyRoute, box='sc_control_zone_b')
    show_sc_controls(q)


def show_sc_controls(q: Q):
    with dbm.Session(q.user.db_engine) as session:
        product_selector = product_dropdown(q, session, trigger=True)
    q.page['sc_controls'] = ui.form_card(
        box='sc_control_zone_a',
        items=[
            ui.text_xl('Controls'),
            ui.button(name='reset_db', label='New Randomized Database'),
            product_selector,
            ui.button(name='show_supply_routes', label='Table: Supply Routes', value='SupplyRoute'),
            ui.button(name='show_graph', label='Graph: Supply Routes'),
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

