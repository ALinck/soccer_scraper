from time import sleep

import requests.exceptions as req_exc

def get(session, url):
    response = None
    i = 3
    while i > 0:
        try:
            with session.get(url) as response:
                return response.text
        except req_exc.ConnectionError:
            i -= 1
            sleep(2)
    if not i > 0:
        raise req_exc.ConnectionError(f'Too many attempts to url {url}')
    return response
