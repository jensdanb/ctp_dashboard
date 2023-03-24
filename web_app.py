from database_model import *
from db_premade_content_for_testing import CcrpBase
from stock_projection_2D import StockProjection, ProjectionATP, ProjectionCTP

import pandas as pd
from typing import List
import os
import uuid
from h2o_wave import Q, main, app, ui, data


_id = 0
ppath = '/home/jensd/PycharmProjects/ctp_dashboard'

current_date = date.today()
server_engine = create_engine("sqlite+pysqlite:///server_db.sqlite", echo=False, future=True)
with Session(server_engine) as session:
    reset_db(server_engine)
    premake_db(session, CcrpBase)

# reset_db(engine)

class TodoItem:
    def __init__(self, text):
        global _id
        _id += 1
        self.id = f'todo_{_id}'
        self.text = text
        self.done = False


@app('/todo', mode='multicast')
async def serve(q: Q):
    # To_do card.
    # On startup all conditions are False and it starts at else: show_todos(q)
    if q.args.new_todo:
        new_todo(q)
    elif q.args.add_todo:
        add_todo(q)
    elif q.args.clear:
        clear_done_todos(q)
    else:
        show_todos(q)

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


to_do_box = '1 1 2 3'
plot_control_box = '3 1 2 3'
plot_box = '1 4 7 4'


def show_controls(q: Q):
    q.page['controls'] = ui.form_card(
        box=plot_control_box,
        items=[
            ui.text_xl("Lets make some plots"),
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


def show_todos(q: Q):
    # Get items for this user
    todos: List[TodoItem] = q.user.todos

    # Create a sample list if we don't have any
    if todos is None:
        q.user.todos = todos = [TodoItem('Do this'), TodoItem('Do that'), TodoItem('Do something else')]

    # Update completion states
    for todo in todos:
        if todo.id in q.args:
            todo.done = q.args[todo.id]

    # Make a checkbox for each TodoItem
    not_done = [ui.checkbox(name=todo.id, label=todo.text, trigger=True) for todo in todos if not todo.done]
    done = [ui.checkbox(name=todo.id, label=todo.text, value=True, trigger=True) for todo in todos if todo.done]

    # Display them
    q.page['to_do_card'] = ui.form_card(box=to_do_box, items=[
        ui.text_l('To Do (example card, not part of my app)'),
        ui.button(name='new_todo', label='New To Do...', primary=True),
        *not_done,
        *([ui.separator('Done')] if len(done) else []),
        *([ui.button(name='clear', label='Clear')] if len(done) else []),
        *done
    ])


def new_todo(q: Q):
    # Display an input form
    q.page['to_do_card'] = ui.form_card(box=to_do_box, items=[
        ui.text_l('New To Do'),
        ui.textbox(name='new_todo_text', label='What needs to be done?'),
        ui.buttons([
            ui.button(name='add_todo', label='Add', primary=True),
            ui.button(name='show_todos', label='Back')
        ])
    ])


def add_todo(q: Q):
    q.user.todos.insert(0, TodoItem(q.args.new_todo_text or 'Untitled'))
    # Then go back to our list
    show_todos(q)


def clear_done_todos(q: Q):
    for todo in q.user.todos:
        if todo.done:
            q.user.todos.remove(todo)

    show_todos(q)

