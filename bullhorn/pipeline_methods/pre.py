import ast
import time
import logging

from bullhorn.api.exceptions import APICallError

REST_API_PARAMS = "command method entity select_fields start sort count query entity_id_str body where".split(" ")
VALID_COMMANDS = ['search', 'query', 'entity', 'entityFiles']
ENTITY_ID_REQUIRED_METHODS = ['UPDATE', 'DELETE']
VALID_METHODS = ['GET', 'POST'] + ENTITY_ID_REQUIRED_METHODS


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
    command, method, entity = params.get('command', None), params.get('method', None), params.get('entity', None)
    select_fields, query, body = params.get('select_fields', None), params.get('query', None), params.get('body', '')
    entity_id = params.pop('entity_id', None)
    entity_id_str = f'/{entity_id}' if entity_id else ''

    if method and method.upper() in ENTITY_ID_REQUIRED_METHODS and not entity_id:
        problems.append(f"entity_id is a required field for all {ENTITY_ID_REQUIRED_METHODS} methods.")

    if command and command.lower() != 'query':
        for param in params.keys():
            if param not in REST_API_PARAMS and param != 'self':
                logging.warning(f'{param} is not an acceptable api parameter. '
                                f'You may only filter by keyword arguments when using the query command.')

    elif command:
        if 'where' not in params:
            problems.append('where is a required argument for the query command. It cannot be none.')

    if command and command.lower() == 'search':
        if 'query' not in params:
            problems.append("query is a required argument when using the search command.")

    if command and command.lower() == 'entity' and method.upper() != 'CREATE' and not entity_id:
        problems.append("entity_id is a required argument when attempting to access existing records.")

    if not command or not command.lower() in VALID_COMMANDS:
        problems.append(f"{command} is not a valid command. Valid commands are {VALID_COMMANDS}")
    if not method or not method.upper() in VALID_METHODS:
        problems.append(f"{command} is not a valid method. Valid methods are {VALID_METHODS}")
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


def clean_api_search_input(params):
    required_params = "entity query select_fields".split(" ")
    if not all(required in params for required in required_params):
        raise APICallError("search command requires entity, query, and select_fields are required arguments.")
    return params


def translate_kwargs_to_query(params):
    mapping = {'gt': '{}>{}', 'gte': '{}>={}', 'lt': '{}<{}', 'lte': '{}<={}', 'to': '{}:[{} TO {}]', 'eq': '{}:{}',
               'ne': 'NOT {}:{}'}
    supported_comparisons = ['gt', 'gte', 'lt', 'lte', 'to', 'eq', 'ne']
    implicit_and = []
    for param in params:
        if param not in REST_API_PARAMS:
            field, comparison = param, 'eq'
            if len(param.split('__')) == 2 and param.split('__')[-1] in supported_comparisons:
                param, comparison = param.split('__')[0], param.split('__')[-1]
            if comparison not in ['ne', 'to']:
                implicit_and.append(mapping[comparison].format(field, params.get(param)))
            elif comparison == 'to':
                to_list = ast.literal_eval(params.get(param))
                if not isinstance(to_list, list):
                    raise APICallError(f'{param} should be a list of two elements, cannot be {params.get(param)}. '
                                       f'Ex: {param}=[1, 2]')
                # implicit_and.append()
    raise NotImplementedError('interrupted')
