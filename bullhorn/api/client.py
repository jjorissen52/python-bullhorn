import json

import requests

from bullhorn import settings
from bullhorn.cache import cache
from bullhorn.pipeline import execution_pipeline, pre, post, error
from bullhorn.api.exceptions import APIAuthError, APICallError

from bullhorn.api.auth import BullhornAuthClient


class BullhornClient(BullhornAuthClient):
    methods = {
        "GET": requests.get,
        "UPDATE": requests.post,
        "DELETE": requests.delete,
        "CREATE": requests.put
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @execution_pipeline(pre=[pre.keep_authenticated], post=[post.raise_error_keys])
    def fake_method(self):
        print(self.auth_details)

    @execution_pipeline(pre=[pre.keep_authenticated, pre.clean_api_call_input], cache=cache)
    def api_call(self, command=None, method=None, entity=None, entity_id=None, select_fields="*", **kwargs):
        """
        :param command: (str) command that bullhorn accepts (see bullhorn api reference material)
        :param method: (str) HTTP verbs telling the API how you want to interact with the data ("GET", "POST", "UPDATE", "DELETE)
        :param entity: (str) Bullhorn entity that you wish to interact with
        :param entity_id: (int, str) (sometimes optional) numeric id corresponding to the desired entity,
            required for all POST and UPDATE commands
        :param select_fields: (str, list) fields desired in response from API call
        :param query: (str) SQL style query string (only used when command="search" and command="query")
        :param body: (dict) dictionary of items to be posted during "UPDATE" or "POST"
            (when command="entity" or command="entityFiles")
        :param kwargs: (kwargs) additional parameters to be passed to the request URL (count=100)
        :return: hopefully a dict with the key "data" with a  list of the searched, queried, added, or updated data
        """
        url = f"{self.auth_details['rest_url']}{command}/{entity}{kwargs['entity_id_str']}"
        # print(url)
        params = {
            "BhRestToken": self.auth_details['bh_rest_token'],
        }
        if select_fields:
            params.update({"fields": select_fields})
        for key in kwargs.keys():
            params.update({key: kwargs[key]})
        body = kwargs.get('body', '')
        response = self.methods[method.upper()](url, json=body, params=params, timeout=self.global_timeout)
        return response

    @execution_pipeline(pre=[pre.clean_api_search_input], cache=cache)
    def search(self, entity=None, select_fields="*", query=None, start=None, count=None, sort=None):
        return self.api_call(command="search", entity=entity, method="GET", select_fields=select_fields, query=query,
                             start=start, count=count, sort=sort)

