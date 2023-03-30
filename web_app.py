import database_model as dbm
from premade_db_content import CcrpBase
from stock_projection_2D import StockProjection, ProjectionATP, ProjectionCTP

from datetime import date, timedelta
import pandas as pd
from typing import List
import os
import uuid
from h2o_wave import Q, main, app, ui, data, copy_expando


current_date = date.today()
server_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
dbm.reset_db(server_engine)

plotable_columns = ['demand', 'supply', 'inventory', 'ATP', 'CTP_route_1']
column_plot_styles = {
    'demand': {'color': 'red', 'type': 'interval'},
    'supply': {'color': 'blue', 'type': 'interval'},
    'inventory': {'color': 'teal', 'type': 'area'},
    'ATP': {'color': 'green', 'type': 'area'},
    'CTP_route_1': {'color': 'orange', 'type': 'area'}
}

@app('/ctp', mode='multicast')
async def serve_ctp(q: Q):
    """ Runs once, on startup """
    if not q.client.initialized:
        q.client.initialized = True

        with dbm.Session(server_engine) as init_session:
            dbm.add_from_class(init_session, CcrpBase)
            init_session.commit()

        q.client.plot_length = 12

    """ Rerun on user action """
    stockpoint = dbm.run_with_session(server_engine, dbm.get_all, table=dbm.StockPoint)[1]
    copy_expando(q.args, q.client)

    if q.args.pre_fill_db:
        with dbm.Session(server_engine) as fill_session:
            dbm.add_from_class_if_db_is_empty(fill_session, CcrpBase)

    """ UI response on user action """
    if q.args.matplotlib_plot_button:
        with dbm.Session(server_engine) as plot_session:
            projection = ProjectionCTP(plot_session, stockpoint, plot_period=q.client.plot_length)
        await mpl_plot(q, projection.plot)
    elif q.args.native_plot_button:
        with dbm.Session(server_engine) as plot_session:
            projection = ProjectionCTP(plot_session, stockpoint)
        native_plot(q, projection, plot_period=q.client.plot_length)
    else:
        show_db_controls(q)
        show_plot_controls(q)

    await q.page.save()

db_box = '1 1 2 4'
plot_control_box = '3 1 3 4'
plot_box = '1 5 6 4'


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
            ui.button(name='matplotlib_plot_button', label='Matplotlib plot'),
            ui.button(name='native_plot_button', label='Native plot'),
            ui.slider(name='plot_length', label='Plot Length', min=10, max=50, step=1, value=q.client.plot_length),
            ui.checklist(name='plot_columns', label='Choose columns to plot', inline=True,
                         choices=[ui.choice(name=col_name, label=col_name) for col_name in plotable_columns])
        ]
    )


def native_plot(q: Q, projection: StockProjection, plot_period: int):
    selected_columns = q.client.plot_columns
    if selected_columns:
        plot_frame: pd.DataFrame = projection.df.loc[projection.df.index[:plot_period], selected_columns].copy()

        y_min = min(0, int(plot_frame.to_numpy().min() * 1.1))
        y_max = max(20, int(plot_frame.to_numpy().max() * 1.1))

        date_strings = [date.isoformat() for date in projection.dates_range[:plot_period]]
        plot_frame['date'] = [date_string[:10] for date_string in date_strings]

        plot_marks = []
        for column_name in selected_columns:
            type = column_plot_styles[column_name]['type']
            color = column_plot_styles[column_name]['color']
            plot_marks.append(
                ui.mark(
                    type=type,
                    x='=date', x_title='Date',
                    y=f'={column_name}', y_title=f'',
                    color=color,
                    dodge='auto',
                    y_min=y_min, y_max=y_max
                )
            )

        q.page['plot'] = ui.plot_card(
            box=plot_box,
            title='Quantity',
            data=data(fields=plot_frame.columns.tolist(), rows=plot_frame.values.tolist()),
            plot=ui.plot(marks=plot_marks)
        )
    else:
        show_plot_controls(q)


async def mpl_plot(q: Q, plot):
    q.page['plot'] = ui.markdown_card(box=plot_box, title='Projected inventory', content='')

    # Make temporary image file from the matplotlib plot
    image_filename = f'{str(uuid.uuid4())}.png'
    plot.savefig(image_filename)

    # Upload to server and clean up
    image_path, = await q.site.upload([image_filename])
    os.remove(image_filename)

    # Display:
    q.page['plot'].content = f'![plot]({image_path})'

