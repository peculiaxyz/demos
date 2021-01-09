from flask import Flask

app = Flask(__name__)


@app.route("/", method='POST')
def index():
    return 'This is a demo whatsapp bot api'

@app.route("/status", method='POST')
def index():
    return 'Delivery status for message, sent to = TBC'


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
