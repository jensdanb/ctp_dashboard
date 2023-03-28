from database_model import *
from db_premade_content_for_testing import CcrpBase
from stock_projection_2D import StockProjection, ProjectionATP, ProjectionCTP

import pandas as pd
from typing import List
import os
import uuid
from h2o_wave import Q, main, app, ui, data


ppath = '/home/jensd/PycharmProjects/ctp_dashboard'

current_date = date.today()
server_engine = create_engine("sqlite+pysqlite:///server_db.sqlite", echo=False, future=True)
Base.metadata.create_all(server_engine)
with Session(server_engine) as session:
    add_from_class_if_db_is_empty(session, CcrpBase)

# reset_db(engine)


@app('/ctp', mode='multicast')
async def serve_ctp(q: Q):
    # My WebApp starts here
    if not q.client.initialized:
        q.client.initialized = True

        show_controls(q)
        q.page['plot'] = ui.markdown_card(box=plot_box, title='Projected inventory', content='')

    if q.args.make_plot:
        with Session(server_engine) as plot_session:
            stockpoint = get_all(plot_session, StockPoint)[1]
            projection = ProjectionCTP(session, stockpoint)
        await make_plot(q, projection.plot)

    await q.page.save()


plot_control_box = '3 1 2 4'
plot_box = '1 5 7 4'


def show_controls(q: Q):
    q.page['controls'] = ui.form_card(
        box=plot_control_box,
        items=[
            ui.text_xl("Let's make some plots"),
            ui.button(name='make_plot', label='Make plot', primary=True)
            # ui.slider(name='alpha', label='Alpha', min=5, max=100, step=1, value=q.client.alpha, trigger=True),
        ]
    )


async def make_plot(q: Q, plot):
    # Make temporary image file from the matplotlib plot
    image_filename = f'{str(uuid.uuid4())}.png'
    plot.savefig(image_filename)

    # Upload to server and clean up
    image_path, = await q.site.upload([image_filename])
    os.remove(image_filename)

    # Display:
    q.page['plot'].content = f'![plot]({image_path})'


# Not in use
def show_plot(q: Q, df: pd.DataFrame):
    q.page['example'] = ui.plot_card(
        box=plot_box,
        title='Inventory',
        data=data(
            fields=['day'] + df.columns.tolist(),
            rows=[[i for i in row] for row in df.itertuples()],
            pack=True
        ),
        plot=ui.plot(marks=[ui.mark(
            type='interval',
            x='=day', x_title='Date',
            y='=demand', y_title='Demand',
        )])
    )


