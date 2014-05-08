# -*- coding: utf8 -*-
import os
import os.path

import flask

import zeeguu
import zeeguu.gym.views
import zeeguu.api.views


class CrossDomainApp(flask.Flask):
    """Allows cross-domain requests for all error pages"""
    def handle_user_exception(self, e):
        rv = super(CrossDomainApp, self).handle_user_exception(e)
        rv = self.make_response(rv)
        rv.headers['Access-Control-Allow-Origin'] = "*"
        return rv

    # create the instance folder and return the path
    def instance_path(self):
        path = os.path.join(self.instance_path, "gen")
        try:
            os.makedirs(path)
        except:
            if not os.path.isdir(path):
                raise
        return path

# *** Starting the App *** #
app = CrossDomainApp(__name__, instance_relative_config=True)

app.config.from_object("zeeguu.default_config")
app.config.from_pyfile("config.cfg", silent=True) #config.cfg is in the instance folder

instance = flask.Blueprint("instance", __name__, static_folder=app.instance_path)

app.register_blueprint(instance)
app.register_blueprint(zeeguu.gym.views.gym)
app.register_blueprint(zeeguu.api.views.api)

