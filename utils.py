import requests
import os


def process_single_image(url, path):
    response = requests.get(url)
    if response.status_code == 200:
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(path, 'wb') as f:
            f.write(response.content)