import json
from flask import request
from zeeguu import db, flask

from zeeguu.api import api
from zeeguu.api.json_result import json_result
from zeeguu.api.route_wrappers import cross_domain, with_session
from zeeguu.model.smartwatch.watch_interaction_event import WatchInteractionEvent
from zeeguu.model.smartwatch.watch_event_type import WatchEventType


@api.route("/upload_smartwatch_events", methods=["POST"])
@cross_domain
@with_session
def upload_smartwatch_events():
    """
    This expects a post parameter named

        events

    which is a json array of dictionaries of the form:

        dict (
                bookmark_id: 1,
                time: 'YYYY-MM-DDTHH:MM:SS',
                event: "Glance"
            }

    :return: OK or FAIL
    """

    events = json.loads(request.form['events'])
    for event in events:
        event_type = WatchEventType.find_by_name(event["event"])
        if not event_type:
            event_type = WatchEventType(event["event"])
            db.session.add(event_type)
            db.session.commit()

        new_event = WatchInteractionEvent(
            event_type,
            event["bookmark_id"],
            event["time"])
        db.session.add(new_event)
    db.session.commit()

    return "OK"

@api.route("/get_smartwatch_events", methods=["GET"])
@cross_domain
@with_session
def get_smartwatch_events():
    """
    Returns an array of entries which are dicts:
        dict (
                bookmark_id: 1,
                time: 'YYYY-MM-DDTHH:MM:SS',
                event: "Glance"
            }

    :return: OK or FAIL
    """
    event_objects = WatchInteractionEvent.events_for_user(flask.g.user)
    sorted_events = sorted(event_objects, key=lambda event: event.time)
    events = [x.data_as_dictionary() for x in sorted_events]

    return json_result(events)