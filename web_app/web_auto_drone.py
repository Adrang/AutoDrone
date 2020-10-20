"""
@title
@description
"""
import argparse
import os

import flask

from auto_drone import PROJECT_PATH
from web_app import routes


class WebAutoDrone:
    DEBUG = False

    APP_NAME = 'WebAutoDrone'
    HOST = '127.0.0.1'
    PORT = 8080

    def __init__(self):
        self.app = flask.Flask(
            import_name=self.APP_NAME,
            template_folder=os.path.join(PROJECT_PATH, 'web_app', 'templates'),
            static_folder=os.path.join(PROJECT_PATH, 'web_app', 'static'),
            root_path=os.path.join(PROJECT_PATH, 'web_app')
        )
        return

    def add_get_routes(self):
        self.app.add_url_rule(rule='/bkapp', endpoint='bkapp', view_func=routes.bkapp_page, methods=['get'])
        return

    def add_post_routes(self):
        return

    def start_app(self):
        self.app.run(host=self.HOST, port=self.PORT)
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))
