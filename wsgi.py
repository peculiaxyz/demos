from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return 'This is a demo whatsapp bot api'


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
