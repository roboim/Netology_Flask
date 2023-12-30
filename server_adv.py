import pydantic

from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from models import Advertisement, Session
from schema import CreateAdvertisement

app = Flask('app')


def validate(schema_class, json_data):
    try:
        return schema_class(**json_data).dict(exclude_unset=True)
    except pydantic.ValidationError as er:
        error = er.errors()[0]
        error.pop('ctx', None)
        raise HttpError(400, error)


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_request(response):
    request.session.close()
    return response


def get_adv_by_id(advertisement_id: int):
    advertisement = request.session.get(Advertisement, advertisement_id)
    if not advertisement:
        raise HttpError(404, f'Advertisement {advertisement_id} is not found')
    return advertisement


def add_adv(advertisement: Advertisement):
    try:
        request.session.add(advertisement)
        request.session.commit()
    except IntegrityError:
        raise HttpError(400, "advertisement already exists")


class HttpError(Exception):
    def __init__(self, status_code: int, message: str | dict | list):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def error_handler(error: HttpError):
    response = jsonify({'status': 'error', 'message': error.message})
    response.status_code = error.status_code
    return response


class AdvRest(MethodView):

    def post(self):
        json_data = validate(CreateAdvertisement, request.json)
        advertisement = Advertisement(**json_data)
        add_adv(advertisement)
        return jsonify(advertisement.dict)

    def get(self, advertisement_id):
        advertisement = get_adv_by_id(advertisement_id)
        return jsonify(advertisement.dict)

    def delete(self, advertisement_id):
        advertisement = get_adv_by_id(advertisement_id)
        request.session.delete(advertisement)
        request.session.commit()
        return jsonify({'title': advertisement.title, 'status': 'deleted'})


adv_view = AdvRest.as_view('adv')
app.add_url_rule('/adv/', view_func=adv_view, methods=['POST'])
app.add_url_rule('/adv/<int:advertisement_id>/', view_func=adv_view, methods=['GET', 'DELETE'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
