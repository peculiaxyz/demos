from flask import Flask

app = Flask(__name__)


@app.route("/", methods=['POST'])
def incoming_message_callback():
    return 'This is a demo whatsapp bot api'

@app.route("/status", methods=['POST'])
def delivery_status_callback():
    return 'Delivery status for message, sent to = TBC'


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
