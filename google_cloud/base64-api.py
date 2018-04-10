from PIL import Image
import datetime
import flask
from flask import request
import io
import base64
import requests
import re
import json
from nltk.tokenize import api
from nltk.chunk import conlltags2tree, tree2conlltags
from nltk import word_tokenize, pos_tag, ne_chunk

app = flask.Flask(__name__)

token = "AIzaSyBuq_FimnRZwTHrqWtK0JbEdyITH2w4W_s"


def detect_text(image_file, access_token=None):

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


def name_extractor(name, ewst):
    for i in name:
        if i in ewst:
            start = ewst.index(i)
            end = ewst.index("\n")
            names = ewst[start:end]
            return names


def website_extract(ewst):
    start = ewst.index("www.")
    if start:
        try:
            end = ewst.index("\n", start + 1)
            return ewst[start:end]
        except Exception:
            return ewst[start:]
    else:
        return ""


def mobile_extractor(list_text):
    mobile_index = []
    r = re.compile(
        r"([0]{1}[6]{1}[-\s]*([1-9]{1}[\s]*){8})|([0]{1}[1-9]{1}[0-9]{1}[0-9]{1}[-\s]*([1-9]{1}[\s]*){6})|([0]{1}[1-9]{1}[0-9]{1}[-\s]*([1-9]{1}[\s]*){7})|")
    a = re.compile(r"^07([\d]{3})[(\D\s)]?[\d]{3}[(\D\s)]?[\d]{3}$")
    b = re.compile(
        r"([0]{1}[6]{1}[-\s]*([1-9]{1}[\s]*){8})|([0]{1}[1-9]{1}[0-9]{1}[0-9]{1}[-\s]*([1-9]{1}[\s]*){6})|([0]{1}[1-9]{1}[0-9]{1}[-\s]*([1-9]{1}[\s]*){7})")
    c = re.compile(r"^((?:\+27|27)|0)(=72|82|73|83|74|84)(\d{7})$")
    d = re.compile(r"[\+]{0,1}(\d{10,13}|[\(][\+]{0,1}\d{2,}[\13)]*\d{5,13}|\d{2,6}[\-]{1}\d{2,13}[\-]*\d{3,13})")
    e = re.compile(r"(\+91(-)?|91(-)?|0(-)?)?(9)[0-9]{9}")
    f = re.compile(r"[\+]{0,1}(\d{10,13}|[\(][\+]{0,1}\d{2,}[\13)]*\d{5,13}|\d{2,6}[\-]{1}\d{2,13}[\-]*\d{3,13})")

    for i in list_text:
        x = str(i).replace("Cell: ", "").replace("Cell ", "").replace("M: ", "", ).replace("M ", "").replace(
            "Landline:", '').replace(" ", '').replace("Landline:", "")
        val = r.search(x).group() if r.search(x) else ''
        val1 = a.search(x).group() if a.search(x) else ''
        val2 = b.search(x).group() if b.search(x) else ''
        val3 = c.search(x).group() if c.search(x) else ''
        val4 = d.search(x).group() if d.search(x) else ''
        val5 = e.search(x).group() if e.search(x) else ''
        val6 = f.search(x).group() if f.search(x) else ''
        if val or val1 or val2 or val3 or val4 or val5 or val6:
            mobile_index.append(i)
    # mobile = ''
    for i in mobile_index:
        i = i.replace(" ", "")
        if i.startswith("+91") or i.startswith("Cell: ") or i.startswith("Cell ") or i.startswith("M: ") \
                or i.startswith("M ") or i.startswith("Landline:") or i.startswith("91") or i.startswith("Tel.:") \
                or i.startswith("Tel:"):
            return str(i)
            # break
        else:
            x = i.replace("Cell: ", "").replace("Cell ", "").replace("M: ", "", ).replace("M ", "").replace(
                "Landline:", '').replace(" ", '').replace("Tel.:", "").replace("Tel: ", "").replace("(", "").replace(
                ")", "")
            return str(x)


def extract_required_entities(text, access_token=None):
    ewst= text
    entities = extract_entities(text, access_token)
    list_text = text.split("\n")
    text = text.splitlines()

    # Mobile number find block
    mobile = mobile_extractor(list_text)

    #name and email
    ne_tree = ne_chunk(pos_tag(word_tokenize(' '.join(text))))
    iob_tagged = tree2conlltags(ne_tree)
    name = []
    extra = []
    for text, code, val in iob_tagged:
        if val == 'B-PERSON' or val == "I-PERSON":
            name.append(text)
        if val == 'O':
            extra.append(text)
    index = extra.index("@")
    email = list(filter(lambda x: re.search(r"[\w\.-]+@[\w\.-]+", x), text))
    if email:
        email = email[0]
        if "Email: " in email:
            email = re.split(r"Email: ", email)[1]
        elif "E " in email:
            email = re.split(r"E ", email)[1]
        elif "E-mail: " in email:
            email = re.split(r"E-mail: ", email)[1]
        elif "e-mail" in email:
            email = re.split(r"e-mail: ", email)[1]

    else:
        email = ''
    names = name_extractor(name, ewst)

    required_entities = {
        'ORGANIZATION': '',
        'PERSON': '',
        'LOCATION': '',
        "EMAIL": ''.join(extra[index - 1:index + 2]),
        "MOBILE": mobile.replace("Cell: ", "").replace("Cell ", "").\
            replace("M: ", "", ).replace("M ", "").\
            replace("Landline:", '').replace(" ", '').\
            replace("Tel.:","").replace("Tel: ","").\
            replace("(","").replace(")","").\
            replace("Tel:", "").replace("Mobile:","").\
            replace("/",",").replace("Cell:",""),
        "CARD_TEXT": ewst,
        "DESIGNATION": "",
        "NAME": names if names else ' '.join(name[:2]),
        "ADDRESS": '',
        "WEBSITE": website_extract(ewst)
    }

    for entity in entities['entities']:
        t = entity['type']
        if t in required_entities:
            required_entities[t] += entity['name']
    if required_entities["NAME"] in required_entities["PERSON"]:

        if len(required_entities["PERSON"].split(required_entities["NAME"])) > 1:
            designation = required_entities["PERSON"].split(required_entities["NAME"])[1]
            if len(designation.split()) > 1:
                designation = designation
            else:
                start = ewst.index(designation.strip())
                end = ewst.index("\n", start+1)
                designation = ewst[start:end]
        else:
            designation = required_entities["PERSON"].split(required_entities["NAME"])
    else:
        designation = ""
    required_entities["DESIGNATION"] = designation
    # desg = required_entities["DESIGNATION"]
    # if desg == " ":
    #     start = ewst.index("\n")
    #     end = ewst.index("\n",start+1)
    #
    #     required_entities["DESIGNATION"] = ewst[start+1:end].strip()
    if required_entities["ADDRESS"] == "":
        required_entities["ADDRESS"] = required_entities["ORGANIZATION"]
    else:
        required_entities["ADDRESS"] = required_entities["ADDRESS"]
    return required_entities


@app.route("/cloud-api", methods=["POST"])
def predict():
    if request.method == "POST":
        print("Read the form data!!!!")

        redata = json.loads(flask.request.data)

        image = redata['image']

        text = detect_text(str(image), access_token=token)
        if text == "":
            data = {"success": False}
        else:
            res = extract_required_entities(text=str(text), access_token=token)

            data = res
            # print(data)
    else:
        data = {"success": False}

    return flask.jsonify(data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8002)