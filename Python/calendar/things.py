import appscript as aps

things=aps.app('Things')

# Locate the Logbook list
for list_ in things.lists():
    if list_.name() == 'Logbook':
        break
# Recover the TODOs from the Logbook, that is the completed items
for todo in list_.to_dos():
    print todo.name(), type(todo.completion_date())
