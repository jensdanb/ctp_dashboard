from h2o_wave import site, Q, ui


""" DO NOT CHANGE header_zone WITHOUT ALSO CHANGING IT IN OTHER PAGES """
def layout(q: Q):
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            breakpoint='xs',
            zones=[
                ui.zone('header_zone'),
                ui.zone('message_zone'),
            ]
        )
    ])


async def home_page(q:Q):
    q.page['welcome'] = ui.form_card('message_zone', items=[
        ui.text_l(f'Welcome to the home page.'),
        ui.text(f"Please navigate to Data Page or Plotting Page by using the navigation header. ")
    ])