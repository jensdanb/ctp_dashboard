import database_model as dbm
from premade_db_content import CcrpBase, ProductB

from pages import homepage as homepage
from pages import datapage as datapage
from pages import plotpage as plotpage

from datetime import date, timedelta
from h2o_wave import site, Q, main, app, ui, data, copy_expando


@app('/', mode='unicast')
async def serve_ctp(q: Q):

    """ Run once, on startup """
    if not q.client.initialized:
        q.client.initialized = True

        # Database  initialization
        q.user.db_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
        dbm.reset_db(q.user.db_engine)
        with dbm.Session(q.user.db_engine) as init_session:
            dbm.add_from_class(init_session, CcrpBase)
            dbm.add_from_class(init_session, ProductB)
            init_session.commit()

        # UI initialization
        q.client.plot_product_selection = '1'
        q.client.plot_stockpoint_selection = '1'  # Warning! Do not set to id number that could be outside initially selected product!
        q.client.plot_length = 12
        q.client.plot_columns = plotpage.plotable_columns

    """ Data updates on user action """
    copy_expando(q.args, q.client)

    """ UI response on user action """
    page_hash = q.args['#']

    if page_hash == 'data_page':
        datapage.layout(q)
        await datapage.data_page(q)
    elif page_hash == 'plot_page':
        plotpage.layout(q)
        await plotpage.plot_page(q)
    else:
        homepage.layout(q)
        await homepage.home_page(q)

    show_header(q)
    await q.page.save()


def show_header(q: Q):
    q.page['header'] = ui.header_card(box='header_zone', title='Inventory Projections', subtitle='', items=[
        ui.button(name='#home_page', label='Home', link=True),
        ui.button(name='#data_page', label='Data', link=True),
        ui.button(name='#plot_page', label='Plotting', link=True),
        ])
