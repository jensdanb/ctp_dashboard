from typing import List
from h2o_wave import Q, main, app, ui

_id = 0
ppath = '/home/jensd/PycharmProjects/ctp_dashboard'

class TodoItem:
    def __init__(self, text):
        global _id
        _id += 1
        self.id = f'todo_{_id}'
        self.text = text
        self.done = False


@app('/todo', mode='multicast')
async def serve(q: Q):
    # ToDo card
    if q.args.new_todo:
        new_todo(q)
    elif q.args.add_todo:
        add_todo(q)
    elif q.args.clear:
        clear_done_todos(q)
    else:
        show_todos(q)

    await q.page.save()


to_do_box = '1 1 3 5'

def show_todos(q: Q):
    # Get items for this user
    todos: List[TodoItem] = q.user.todos

    # Create a sample list if we don't have any
    if todos is None:
        q.user.todos = todos = [TodoItem('Do this'), TodoItem('Do that'), TodoItem('Do something else')]

    for todo in todos:
        if todo.id in q.args:
            todo.done = q.args[todo.id]

    # Make a checkbox for each TodoItem
    not_done = [ui.checkbox(name=todo.id, label=todo.text, trigger=True) for todo in todos if not todo.done]
    done = [ui.checkbox(name=todo.id, label=todo.text, value=True, trigger=True) for todo in todos if todo.done]

    # Display them
    q.page['form'] = ui.form_card(box=to_do_box, items=[
        ui.text_l('To Do'),
        ui.button(name='new_todo', label='New To Do...', primary=True),
        *not_done,
        *([ui.separator('Done')] if len(done) else []),
        *([ui.button(name='clear', label='Clear')] if len(done) else []),
        *done
    ])


def new_todo(q: Q):
    # Display an input form
    q.page['form'] = ui.form_card(box=to_do_box, items=[
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

