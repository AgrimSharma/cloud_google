import flask
from flask import request
from base64 import b64encode
import requests
import json
from flask import render_template

import urllib

app = flask.Flask(__name__)

token = "AIzaSyBuq_FimnRZwTHrqWtK0JbEdyITH2w4W_s"


def label_detection(image_file, access_token=None):

    url = 'https://vision.googleapis.com/v1/images:annotate?key={}'.format(access_token)
    header = {'Content-Type': 'application/json'}
    body = {
        'requests': [{
            'image': {
                'content': image_file,
            },
            'features': [{
                'type': 'LABEL_DETECTION',
                'maxResults': 50,
            }]

        }]
    }
    response = requests.post(url, headers=header, json=body).json()
    text = response['responses'][0]
    return text


def web_detection(image_file, access_token=None):

    url = 'https://vision.googleapis.com/v1/images:annotate?key={}'.format(access_token)
    header = {'Content-Type': 'application/json'}
    body = {
        'requests': [{
            'image': {
                'content': image_file,
            },
            'features': [{
                'type': 'WEB_DETECTION',
                'maxResults': 1,
            }]

        }]
    }
    response = requests.post(url, headers=header, json=body).json()
    text = response['responses'][0]
    return text


@app.route("/compare-api", methods=["POST"])
def predict():
    if request.method == "POST":
        print("Read the form data!!!!")
        import pdb;pdb.set_trace()
        try:
            URL = flask.request.form["image"]

            image = b64encode(urllib.request.urlopen(URL).read()).decode()
            label = label_detection(image, access_token=token)
            all_labels = [dict(description=x['description'].upper(), percentage=round(x['score']*100, 2)) for x in label['labelAnnotations']]
            return render_template('index1.html', name=all_labels, message="Success")
        except Exception:
            return render_template('index1.html', message="Try again with different image. We are unable to process it.")

    else:
        data = {"success": False}

    return flask.jsonify(data)


@app.route("/base64-api", methods=["POST"])
def base64():
    if request.method == "POST":
        print("Read the form data!!!!")

        redata = json.loads(flask.request.data)

        image = redata['image']

        label = label_detection(image, token)
        all_labels = [dict(description=x['description'].upper(), percentage=round(x['score']*100, 2)) for x in label['labelAnnotations']]
        data = all_labels
    else:
        data = {"success": False}

    return flask.jsonify(data)


@app.route("/")
def index():

    return render_template('index.html', title='Home')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8002)