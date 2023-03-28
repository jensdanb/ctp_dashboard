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
reset_db(server_engine)



@app('/ctp', mode='multicast')
async def serve_ctp(q: Q):
    # My WebApp starts here
    if not q.client.initialized:
        q.client.initialized = True

        with Session(server_engine) as init_session:
            add_from_class(init_session, CcrpBase)
            init_session.commit()

        q.client.plot_length = 12
        show_db_controls(q)
        show_plot_controls(q)

    stockpoint = run_with_session(server_engine, get_all, table=StockPoint)[1]
    if q.args.plot_length is not None:
        q.client.plot_length = q.args.plot_length

    # Database controls triggered
    if q.args.pre_fill_db:
        with Session(server_engine) as fill_session:
            add_from_class_if_db_is_empty(fill_session, CcrpBase)
        show_db_controls(q)

    # Plot controls triggered
    elif q.args.matplotlib_plot:
        with Session(server_engine) as plot_session:
            projection = ProjectionCTP(plot_session, stockpoint, plot_period=q.client.plot_length)
        await make_plot(q, projection.plot)
    elif q.args.native_plot:
        with Session(server_engine) as plot_session:
            projection = ProjectionCTP(plot_session, stockpoint)
        show_h2o_plot(q, projection, plot_period=q.client.plot_length)


    await q.page.save()

db_box = '1 1 2 4'
plot_control_box = '3 1 2 4'
plot_box = '1 5 7 4'


def show_db_controls(q: Q):
    q.page['db_controls'] = ui.form_card(
        box=db_box,
        items=[
            ui.text_xl("Database Controls"),
            ui.button(name='pre_fill_db', label='Prefill database')
        ]
    )

def show_plot_controls(q: Q):
    q.page['controls'] = ui.form_card(
        box=plot_control_box,
        items=[
            ui.text_xl("Plot Controls"),
            ui.button(name='matplotlib_plot', label='Matplotlib plot'),
            ui.button(name='native_plot', label='Native plot'),
            ui.slider(name='plot_length', label='Plot Length', min=10, max=50, step=1, value=q.client.points)
            # ui.slider(name='alpha', label='Alpha', min=5, max=100, step=1, value=q.client.alpha, trigger=True),
        ]
    )


async def make_plot(q: Q, plot):
    q.page['plot'] = ui.markdown_card(box=plot_box, title='Projected inventory', content='')

    # Make temporary image file from the matplotlib plot
    image_filename = f'{str(uuid.uuid4())}.png'
    plot.savefig(image_filename)

    # Upload to server and clean up
    image_path, = await q.site.upload([image_filename])
    os.remove(image_filename)

    # Display:
    q.page['plot'].content = f'![plot]({image_path})'


def show_h2o_plot(q: Q, projection: StockProjection, plot_period: int):
    df = projection.df.loc[projection.df.index[:plot_period], ['demand', 'supply']].copy()

    # Convert dates to textstrings, and shorten to just date info (10 first characters)
    date_strings = [date.isoformat() for date in projection.dates_range[:plot_period]]
    df['date'] = [date_string[:10] for date_string in date_strings]

    y_min = int(min(df['demand']) * 1.1)
    y_max = int(max(df['supply']) * 1.1)

    q.page['plot'] = ui.plot_card(
        box=plot_box,
        title='Demand/Supply',
        data=data(
            fields=df.columns.tolist(),
            rows=df.values.tolist(),
            pack=True
        ),
        plot=ui.plot(marks=[
            ui.mark(
                type='interval',
                x='=date', x_title='Date',
                y='=demand', y_title='Demand',
                color='red',
                dodge='auto',
                y_min=y_min, y_max=y_max
            ),
            ui.mark(
                type='interval',
                x='=date',
                y='=supply',
                color='blue',
                dodge='auto',
                y_min=y_min, y_max=y_max
            )
        ])
    )


