import time
import logging

from bullhorn.api.exceptions import APICallError


def keep_authenticated(params):
    """

    """
    request_start = time.time()
    self = params.get('self')
    auth_details = self.auth_details
    expiration_time = auth_details.get("expiration_time", 0) if auth_details else 0
    if self.leader and not auth_details:
        self.authenticate()
        auth_details = self.auth_details
    else:
        retries = 10
        while retries:
            if expiration_time - request_start <= 0:
                time.sleep(1)
                auth_details = self.auth_details
            if auth_details:
                break
            retries -= 1
    return params


def clean_api_call_input(params):
    problems = []
    valid_commands = ['search', 'query', 'entity', 'entityFiles']
    entity_id_required_commands = ['UPDATE', 'DELETE']
    valid_methods = ['GET', 'CREATE'] + entity_id_required_commands
    api_params = 'command method entity select_fields start sort count query entity_id_str body'.split(' ')
    command, method, entity = params.get('command', None), params.get('method', None), params.get('entity', None)
    select_fields, query, body = params.get('select_fields', None), params.get('query', None), params.get('body', '')
    entity_id = params.pop('entity_id', None)
    entity_id_str = f'/{entity_id}' if entity_id else ''

    if method and method.upper() in entity_id_required_commands and not entity_id:
        problems.append(f"entity_is is a required field for all {entity_id_required_commands} commands.")

    if command and command.lower() != 'query':
        for param in params.keys():
            if param not in api_params and param != 'self':
                logging.warning(f'{param} is not an acceptable api parameter. '
                                f'You may only filter by keyword arguments when using the query command.')

    if command and command.lower() == 'search':
        if 'query' not in params:
            problems.append("query is a required argument when using the search command.")

    if command and command.lower() == 'entity' and method.upper() != 'CREATE' and not entity_id:
        problems.append("entity_id is a required argument when attempting to access existing records.")

    if not command or not command.lower() in valid_commands:
        problems.append(f"{command} is not a valid command. Valid commands are {valid_commands}")
    if not method or not method.upper() in valid_methods:
        problems.append(f"{command} is not a valid method. Valid methods are {valid_methods}")
    if not entity:
        problems.append(f"{entity} is not a valid entity.")

    if not select_fields or not isinstance(select_fields, (str, list)):
        problems.append(f"{select_fields} is not a valid argument for select_fields. Must be a str or list")
    else:
        if isinstance(select_fields, list):
            select_fields = ','.join(select_fields)
        select_fields = select_fields.replace(' ', '')

    if problems:
        raise APICallError("\n".join(problems))

    params.update({"command": command.lower(), "method": method.upper()})
    params.update({"entity_id_str": entity_id_str})
    params.update({'select_fields': select_fields})

    return params
