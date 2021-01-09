import flask
import _dialog_engines as eng
from twilio.twiml.messaging_response import MessagingResponse
import logging

app = flask.Flask(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _build_twilio_response(message:str, media_url:str=None):
    response = MessagingResponse()
    msg = response.message()
    msg.body(message)
    if media_url not in (None, ''):
        msg.media(media_url)
    return str(response)

def _sanitize_sender_info(sender:str):
    if 'whatsapp' in sender:
        sender = sender.replace('whatsapp', '')
    if 'sms' in sender:
        sender = sender.replace('whatsapp', '')
    return sender

@app.route("/", methods=['POST'])
def incoming_message_callback():
    incoming_msg = flask.request.values.get('Body')
    sender = flask.request.values.get('From')
    sender = _sanitize_sender_info(sender)
    logger.info(f'Incoming message from twilio: {incoming_msg}')

    input = eng.DialogEngineInput()
    input.input_message = incoming_msg
    input.sender = sender
    engine = eng.TensoFlowDialogEngine(request_data=input)
    botresponse = engine.execute()

    response = _build_twilio_response(botresponse)
    return response

@app.route("/status", methods=['POST'])
def delivery_status_callback():
    return _build_twilio_response('Delivery status callback ready')


if __name__ == '__main__':
    app.run()
