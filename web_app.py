from databasing import database_model as dbm
from databasing.premade_db_content import ProductA, FakeProduct, BranchingProduct

from pages import order_page as homepage
from pages import supply_chain_page as datapage
from pages import inventory_page as plotpage

from h2o_wave import main, Q, app, ui, copy_expando


@app('/', mode='unicast')
async def serve_ctp(q: Q):

    """ Run once, on startup """
    if not q.client.initialized:
        q.client.initialized = True

        # Database  initialization
        q.user.db_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
        dbm.reset_db(q.user.db_engine)
        with dbm.Session(q.user.db_engine) as init_session:
            dbm.add_from_class(init_session, ProductA)
            dbm.add_from_class(init_session, FakeProduct)
            dbm.add_from_class(init_session, BranchingProduct)
            init_session.commit()

        # UI initialization
        q.client.product_selection = '1'
        q.client.stockpoint_selection = '1'  # Warning! Do not set to id number that could be outside initially selected product!
        q.client.supply_route_selection = '1'
        q.client.plot_length = 12
        q.client.plot_columns = plotpage.plotable_columns

    """ Data updates on user action """
    copy_expando(q.args, q.client)

    """ UI response on user action """
    page_hash = q.args['#']

    if page_hash == 'order_page':
        homepage.layout(q)
        await homepage.serve_order_page(q)
    elif page_hash == 'inventory_page':
        plotpage.layout(q)
        await plotpage.serve_inventory_page(q)
    else:  # -> page_hash == None or 'sc_page'
        datapage.layout(q)
        await datapage.serve_supply_chain_page(q)

    show_header(q)
    await q.page.save()


def show_header(q: Q):
    page_hash = q.args['#']
    hash_to_label = {
        'sc_page': 'Supply Chain',
        'order_page': 'Orders',
        'inventory_page': 'Inventories',
    }
    pagination_items = [ui.button(name=f'#{hash}',label=hash_to_label[hash], link=True)
                        for hash in hash_to_label]
    q.page['header'] = ui.header_card(box='header_zone',
                                      title=hash_to_label[page_hash] if page_hash else 'Supply Chain',
                                      subtitle='',
                                      items=pagination_items
                                      )
