from databasing import database_model as dbm
from projection import StockProjection, ProjectionCTP
from pages.shared_content import get_selected, product_dropdown, stockpoint_choice_group

import os
import uuid
import pandas as pd
from h2o_wave import Q, ui, data


plotable_columns = ['demand', 'supply', 'inventory', 'ATP', 'CTP']
column_plot_styles = {
    'demand': {'color': 'red', 'type': 'interval'},
    'supply': {'color': 'blue', 'type': 'interval'},
    'inventory': {'color': 'teal', 'type': 'area'},
    'ATP': {'color': 'green', 'type': 'area'},
    'CTP': {'color': 'orange', 'type': 'area'}
}


def layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            breakpoint='xs',
            zones=[
                ui.zone('header_zone'),  # DO NOT CHANGE header_zone WITHOUT ALSO CHANGING IT IN OTHER PAGES
                ui.zone('inv_control_zone', direction=ui.ZoneDirection.COLUMN, zones=[
                    ui.zone('inv_control_zone_a', size='42%'),
                    ui.zone('inv_control_zone_b', size='58%'),
                ]),
                ui.zone('plot_zone'),
            ]
        ),
        ui.layout(
            breakpoint='m',
            zones=[
                ui.zone('header_zone'),
                ui.zone('inv_control_zone', direction=ui.ZoneDirection.ROW, zones=[
                    ui.zone('inv_control_zone_a', size='33%'),
                    ui.zone('inv_control_zone_b', size='66%'),
                ]),
                ui.zone('plot_zone'),
            ]
        )
    ])


async def serve_inventory_page(q: Q):
    if q.args.matplotlib_plot_button:
        with dbm.Session(q.user.db_engine) as plot_session:
            projection = project_plot_stockpoint_selection(q, plot_session)
        await mpl_plot(q, projection.plot)

    elif q.args.native_plot_button:
        with dbm.Session(q.user.db_engine) as plot_session:
            projection = project_plot_stockpoint_selection(q, plot_session)
        native_plot(q, projection, plot_period=q.client.plot_length)

    elif q.args.show_sp_move_orders:
        await show_sp_move_orders(q)

    else:
        show_plot_stockpoint_chooser(q, 'inv_control_zone_a', trigger1=True)
        show_plot_controls(q)


def project_plot_stockpoint_selection(q, session, projection_class=ProjectionCTP):
    stockpoint = get_selected(q, session, dbm.StockPoint)
    return projection_class(session, stockpoint, plot_period=q.client.plot_length)


def show_plot_stockpoint_chooser(q: Q, box, trigger1=True, trigger2=False):
    with dbm.Session(q.user.db_engine) as session:
        product_chooser = product_dropdown(q, session, trigger=trigger1)
        stockpoint_chooser = stockpoint_choice_group(q, session, trigger=trigger2)

    q.page['stockpoint_chooser'] = ui.form_card(
        box=box,
        items=[
            product_chooser,
            stockpoint_chooser
        ]
    )


def show_plot_controls(q: Q):
    q.page['controls'] = ui.form_card(
        box='inv_control_zone_b',
        items=[
            ui.text_xl("Make Plot"),
            ui.buttons([
                ui.button(name='matplotlib_plot_button', label='Plot with Matplotlib'),
                ui.button(name='native_plot_button', label='Plot with WebApp Plot'),
                ui.button(name='show_sp_move_orders', label='Show Incoming/Outgoing Orders')
            ]),

            ui.slider(name='plot_length', label='Number of days in plot', min=10, max=50, step=1, value=q.client.plot_length),
            ui.checklist(name='plot_columns', label='Data columns in plot', inline=True,
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
            box='plot_zone',
            title=projection.__str__(),
            data=data(fields=plot_frame.columns.tolist(), rows=plot_frame.values.tolist()),
            plot=ui.plot(marks=plot_marks)
        )
    else:
        q.page['plot'] = ui.markdown_card(
            box='plot_zone',
            title='No columns selected',
            content='No data column selected. Select at least one.'
        )


async def mpl_plot(q: Q, plot):
    q.page['plot'] = ui.markdown_card(box='plot_zone', title='Projected inventory', content='')

    # Make temporary image file from the matplotlib plot
    image_filename = f'{str(uuid.uuid4())}.png'
    plot.savefig(image_filename)

    # Upload to server and clean up
    image_path, = await q.site.upload([image_filename])
    os.remove(image_filename)

    # Display:
    q.page['plot'].content = f'![plot]({image_path})'


async def show_sp_move_orders(q: Q):
    # Get data from db
    with dbm.Session(q.user.db_engine) as list_move_orders_session:
        stockpoint = get_selected(q, list_move_orders_session, dbm.StockPoint)

        incoming_moves = dbm.get_incoming_move_orders(list_move_orders_session, stockpoint)
        outgoing_moves = dbm.get_outgoing_move_orders(list_move_orders_session, stockpoint)
        pending_incoming = dbm.uncompleted_orders(incoming_moves)
        pending_outgoing = dbm.uncompleted_orders(outgoing_moves)

    # Convert to H2O Wave content
    incoming_table = [
        ui.stat_table_item(
            label=str(order.id),
            values=['incoming', str(order.quantity), order.order_date.isoformat(),
                    str(order.completion_status), str(order.request_id)],
            colors=['blue'] + ['black'] * 4
        ) for order in pending_incoming
    ]
    outgoing_table = [
        ui.stat_table_item(
            label=str(order.id),
            values=['outgoing', str(order.quantity), order.order_date.isoformat(),
                    str(order.completion_status), str(order.request_id)],
            colors=['red'] + ['black'] * 4
        ) for order in pending_outgoing
    ]

    full_table = incoming_table + outgoing_table

    # Show H2O Wave content
    q.page['plot'] = ui.stat_table_card(
        box='plot_zone',
        title='Move Orders',
        columns=['ID', 'incoming/outgoing', 'Quantity', 'Planned Date', 'Completion Status', 'Request ID'],
        items=full_table
    )
