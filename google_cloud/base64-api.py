from PIL import Image
import datetime
import flask
from flask import request
import io
import base64
import requests
import re
import json

app = flask.Flask(__name__)

token = "AIzaSyBuq_FimnRZwTHrqWtK0JbEdyITH2w4W_s"


def detect_text(image_file, access_token=None):

    # with open(image_file, 'rb') as image:
    #     base64_image = base64.b64encode(image.read()).decode()
    url = 'https://vision.googleapis.com/v1/images:annotate?key={}'.format(access_token)
    header = {'Content-Type': 'application/json'}
    body = {
        'requests': [{
            'image': {
                'content': image_file,
            },
            'features': [{
                'type': 'TEXT_DETECTION',
                'maxResults': 1,
            }]

        }]
    }
    try:
        response = requests.post(url, headers=header, json=body).json()
        text = response['responses'][0]['textAnnotations'][0]['description'] if len(response['responses'][0]) > 0 else ''
    except Exception:
        text = ''
    return text


def extract_entities(text, access_token=None):

    url = 'https://language.googleapis.com/v1beta1/documents:analyzeEntities?key={}'.format(access_token)
    header = {'Content-Type': 'application/json'}
    body = {
        "document": {
            "type": "PLAIN_TEXT",
            "language": "EN",
            "content": text
        },
        "encodingType": "UTF8"
    }
    response = requests.post(url, headers=header, json=body).json()
    return response


def extract_required_entities(text, access_token=None):
    entities = extract_entities(text, access_token)
    text = str(text).splitlines()
    # import pdb;pdb.set_trace()
    # email = re.search(r"[\w\.-]+@[\w\.-]+", t)
    email = list(filter(lambda x: re.search(r"[\w\.-]+@[\w\.-]+", x), text))
    mobile = list(filter(lambda x: re.search(r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})", x), text))
    if email:
        email = email[0]
        if "Email: " in email:
            email = re.split(r"Email: ", email)[1]
        elif "E " in email:
            email = re.split(r"E ", email)[1]
        elif "E-mail: " in email:
            email = re.split(r"E-mail: ", email)[1]

    else:
        email = ''
    # mobile = list(filter(lambda x: re.search(r"Cell: ", x), mobile))
    # if mobile:
    #     mobile = re.split(r"Cell: ", mobile[0])[1]
    # else:
    #     mobile = mobile
    mobile = mobile[0] if len(mobile)> 0 else ''
    required_entities = {'ORGANIZATION': '', 'PERSON': '', 'LOCATION': '',
                         "EMAIL": email, "MOBILE": mobile, "CARD_TEXT": text,
                         "DESIGNATION": text[1], "NAME": text[0],
                         "ADDRESS": text[2]
                         }

    for entity in entities['entities']:
        t = entity['type']
        if t in required_entities:
            required_entities[t] += entity['name']

    return required_entities


@app.route("/cloud-api", methods=["POST"])
def predict():
    if request.method == "POST":
        print("Read the form data!!!!")
        # import pdb;pdb.set_trace()
        redata = json.loads(flask.request.data)

        image = redata['image']
        # image = request.files["image"].read()
        # image_name = request.files["image"].filename
        # images = Image.open(io.BytesIO(image))
        # if ".png" in image_name:
        #     name = "images/image_{}.png".format(datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S"))
        #
        # else:
        #     name = "images/image_{}.jpeg".format(datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S"))

        # images.save(name)
        text = detect_text(str(image), access_token=token)
        if text == "":
            data = {"success": False}
        else:
            res = extract_required_entities(text=str(text), access_token=token)

            data = res
            print(data)
    else:
        data = {"success": False}

    return flask.jsonify(data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001)
