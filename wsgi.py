import flask
from twilio.twiml.messaging_response import MessagingResponse
import logging

app = flask.Flask(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _build_twilio_response(message:str, media_url:str=None):
    response = MessagingResponse()
    message = response.message()
    message.body(message)
    return str(response)

@app.route("/", methods=['POST'])
def incoming_message_callback():
    incoming_msg = flask.request.values.get('Body')  # TODO: ask user to try again here
    logger.info(f'Incoming message from twilio: {incoming_msg}')
    response = _build_twilio_response('This is a demo whatsapp bot api')
    return response

@app.route("/status", methods=['POST'])
def delivery_status_callback():
    return _build_twilio_response('Delivery status callback ready')


if __name__ == '__main__':
    app.run()
