from time import sleep

def get(session, url):
    response = None
    i = 3
    while i > 0:
        try:
            with session.get(url) as response:
                return response.text
        except ConnectionError:
            i -= 1
            sleep(2)
    if not i > 0:
        raise ConnectionError(f'Too many attempts to url {url}')
    return response
