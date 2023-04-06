import database_model as dbm
from premade_db_content import CcrpBase
from stock_projection_2D import StockProjection, ProjectionATP, ProjectionCTP

from datetime import date, timedelta
import pandas as pd
from typing import List
import os
import uuid
from h2o_wave import site, Q, main, app, ui, data, copy_expando


current_date = date.today()
plotable_columns = ['demand', 'supply', 'inventory', 'ATP', 'CTP']
column_plot_styles = {
    'demand': {'color': 'red', 'type': 'interval'},
    'supply': {'color': 'blue', 'type': 'interval'},
    'inventory': {'color': 'teal', 'type': 'area'},
    'ATP': {'color': 'green', 'type': 'area'},
    'CTP': {'color': 'orange', 'type': 'area'}
}


def set_layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            breakpoint='xs',
            zones=[
                ui.zone('header_zone'),
                ui.zone('control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('control_zone_left', size='40%'),
                    ui.zone('control_zone_right', size='60%'),
                ]),
                ui.zone('bottom_zone'),
            ]
        )
    ])


@app('/ctp', mode='multicast')
async def serve_ctp(q: Q):
    """ Run once, on startup """

    if not q.client.initialized:
        set_layout(q)
        show_header(q)
        q.client.initialized = True

        q.user.db_engine = dbm.create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
        dbm.reset_db(q.user.db_engine)
        with dbm.Session(q.user.db_engine) as init_session:
            dbm.add_from_class(init_session, CcrpBase)
            init_session.commit()

            q.client.stockpoint = dbm.get_all(init_session, dbm.StockPoint)[1]
            q.args.stockpoint_choice_group = str(q.client.stockpoint.id)

        q.client.plot_length = 12
        q.client.plot_columns = plotable_columns

        show_plot_stockpoint_chooser(q)
        show_plot_controls(q)



    """ Rerun on user action """

    copy_expando(q.args, q.client)

    if q.args.pre_fill_db:
        with dbm.Session(q.user.db_engine) as fill_session:
            dbm.add_from_class_if_db_is_empty(fill_session, CcrpBase)

    """ UI response on user action """
    if q.args.stockpoint_choice_group:
        q.client.stockpoint = dbm.run_with_session(q.user.db_engine, dbm.get_by_id,
                                                   table=dbm.StockPoint, element_id=int(q.client.stockpoint_choice_group))

        with dbm.Session(q.user.db_engine) as plot_session:
            projection = ProjectionCTP(plot_session, q.client.stockpoint)
        native_plot(q, projection, plot_period=q.client.plot_length)

    elif q.args.matplotlib_plot_button:
        with dbm.Session(q.user.db_engine) as plot_session:
            projection = ProjectionCTP(plot_session, q.client.stockpoint, plot_period=q.client.plot_length)
        await mpl_plot(q, projection.plot)

    elif q.args.native_plot_button:
        with dbm.Session(q.user.db_engine) as plot_session:
            projection = ProjectionCTP(plot_session, q.client.stockpoint)
        native_plot(q, projection, plot_period=q.client.plot_length)

    else:
        show_plot_stockpoint_chooser(q)
        show_plot_controls(q)

    await q.page.save()


def show_header(q: Q):
    q.page['header'] = ui.header_card(box='header_zone', title='My app', subtitle='Routing demonstration', items=[
        ui.button(name='#data_page', label='Data', link=True),
        ui.button(name='#plot_page', label='Plotting', link=True),
        ui.button(name='#page3', label='Page 3', link=True),
    ])


# Data page functions
def show_db_controls(q: Q):
    q.page['data_page'] = ui.form_card(
        box='control_zone_left',
        items=[
            ui.text_xl("Database Controls"),
            ui.button(name='pre_fill_db', label='Prefill database')
        ]
    )


# Plotting page functions
def show_plot_stockpoint_chooser(q: Q):
    valid_stockpoints = dbm.run_with_session(q.user.db_engine, dbm.get_all, table=dbm.StockPoint)
    choices = [
        ui.choice(str(stockpoint.id), stockpoint.name)
    for stockpoint in valid_stockpoints]

    q.page['stockpoint_chooser'] = ui.form_card(
        box='control_zone_left',
        items=[
            ui.text_xl("Choose Stockpoint"),
            ui.choice_group(name='stockpoint_choice_group', label='Pick one',
                            value=q.args.stockpoint_choice_group, required=True, choices=choices)
        ]
    )


def show_plot_controls(q: Q):
    q.page['controls'] = ui.form_card(
        box='control_zone_right',
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
            box='bottom_zone',
            title='Quantity',
            data=data(fields=plot_frame.columns.tolist(), rows=plot_frame.values.tolist()),
            plot=ui.plot(marks=plot_marks)
        )
    else:
        show_plot_controls(q)


async def mpl_plot(q: Q, plot):
    q.page['plot'] = ui.markdown_card(box='bottom_zone', title='Projected inventory', content='')

    # Make temporary image file from the matplotlib plot
    image_filename = f'{str(uuid.uuid4())}.png'
    plot.savefig(image_filename)

    # Upload to server and clean up
    image_path, = await q.site.upload([image_filename])
    os.remove(image_filename)

    # Display:
    q.page['plot'].content = f'![plot]({image_path})'
