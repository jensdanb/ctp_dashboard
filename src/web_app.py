from h2o_wave import main, Q, app, ui, copy_expando

from .databasing import database_model as dbm
from .databasing.premade_db_content import ProductA, FakeProduct, BranchingProduct
from .pages.shared_content import get_selected, DbContent, force_select_child_in_selected_parent
from .pages import order_page as orderpage
from .pages import supply_chain_page as sc_page
from .pages import inventory_page as plotpage


@app('/', mode='unicast')
async def serve_ctp(q: Q):

    """ Run once, on startup """
    if not q.client.initialized:
        q.client.initialized = True

        # Database  initialization
        url_object = dbm.URL.create(
            "sqlite+pysqlite",
            username=None,
            password=None,  # plain (unescaped) text
            host=None,
            database="memory",
        ) # "sqlite+pysqlite:///:memory:"
        q.user.db_engine = dbm.create_engine(url_object, echo=False, future=True)
        
        dbm.reset_db(q.user.db_engine)
        with dbm.Session(q.user.db_engine) as init_session:
            dbm.add_from_class(init_session, ProductA)
            dbm.add_from_class(init_session, FakeProduct)
            dbm.add_from_class(init_session, BranchingProduct)
            init_session.commit()

        # UI initialization
        q.client.product_selection = 1
        q.client.stockpoint_selection = 2  # Warning! Do not set to id number that could be outside initially selected product!
        q.client.supply_route_selection = 1
        q.client.plot_length = 12
        q.client.plot_columns = plotpage.plotable_columns

    with dbm.Session(q.user.db_engine) as ui_session:

        """ Data updates on user action """
        copy_expando(q.args, q.client)

        db_content = DbContent(q, ui_session)

        """ UI response on user action """
        page_hash = q.args['#']

        if page_hash == 'sc_page':
            sc_page.layout(q)
            await sc_page.serve_supply_chain_page(q, ui_session)

        elif page_hash == 'order_page':  # ->
            orderpage.layout(q)
            await orderpage.serve_order_page(q, ui_session)

        elif page_hash == 'inventory_page' or page_hash is None:  #
            plotpage.layout(q)
            await plotpage.serve_inventory_page(q, ui_session, db_content)

        show_header(q)
        await q.page.save()


def show_header(q: Q):
    page_hash = q.args['#']
    hash_to_label = {
        'sc_page': 'Supply Chain',
        'order_page': 'Orders',
        'inventory_page': 'Inventories',
    }
    pagination_items = [ui.button(name=f'#{page_hash}',label=hash_to_label[page_hash], link=True)
                        for page_hash in hash_to_label]
    q.page['header'] = ui.header_card(box='header_zone',
                                      title=hash_to_label[page_hash] if page_hash else 'Inventories',
                                      subtitle='',
                                      items=pagination_items
                                      )
