import requests
from requests.exceptions import HTTPError
import backoff
import logging
from decouple import config


def decorate_for_log(f):
    """ Basic logging decorator"""
    def wrap(*args, **kwargs):
        logging.info(f'{f.__name__} with {args}, {kwargs}')
        try:
            return_value = f(*args, **kwargs)
            logging.debug(f'{f.__name__} has return value = {return_value}')
        except Exception as e:
            logging.error(f'{f.__name__} has error {e}')
            raise
        logging.info(f'{f.__name__} finished')
        return return_value
    return wrap

class BauBuddy:
    """ Util class for https://api.baubuddy.de/ usage """
    def __init__(self, cache_labels=False):
        self._get_access_token()
        self._cache_labels = cache_labels
        if self._cache_labels:
            self._labels_cache = {}
    #Acceses Token      
    def _get_access_token(self):
        """ Token refresher"""
        headers = {
            'Authorization': "Basic QVBJX0V4cGxvcmVyOjEyMzQ1NmlzQUxhbWVQYXNz",
            'Content-Type': 'application/json',
        }

        json_data = {
            'username': '365',
            'password': '1'
        }
        url = 'https://api.baubuddy.de/index.php/login'
        response = requests.post(url, headers=headers, json=json_data)
        response_data = response.json()
        self._token = response_data["oauth"]["access_token"]

    @decorate_for_log
    @backoff.on_exception(backoff.expo, exception=HTTPError, max_time=60, max_tries=3)
    def download_active(self):
        #Acceses active vehicles
        """Downloads active vehicle list from
        https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active
        """
        headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json',
        }
        
        url='https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active'
        response = requests.get(url, headers=headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self._get_access_token()
            raise
        data = response.json()
        return data

    @backoff.on_exception(backoff.expo, exception=HTTPError, max_time=60, max_tries=3)
    def query_color_code(self, label_id):
        #Accses color codes
        """get color code from 
        https://api.baubuddy.de/dev/index.php/v1/labels/{label_id}
        using label id
        """
        headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json',
        }
        
        url=f'https://api.baubuddy.de/dev/index.php/v1/labels/{label_id}'
        response = requests.get(url, headers=headers)
        
        try:
            response.raise_for_status()
        except HTTPError as e:
            self._token = self._get_access_token()
            raise
        
        data = response.json()
        logging.debug(f'color data returns : {data}')
        colorCode= (data[0]['colorCode'] if data and 'colorCode' in data[0] else '')
        logging.debug(f'color returned : {colorCode}')
        return colorCode

    @decorate_for_log
    def get_color(self, label_id):
        """ Get color information from label_id """
        # if cache usage is active try to get from cache
        if self._cache_labels:
            if label_id in self._labels_cache:
                return self._labels_cache[label_id]
        
        color_code = self.query_color_code(label_id)
        self._labels_cache[label_id] = color_code
        return color_code