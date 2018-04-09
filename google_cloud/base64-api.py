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
    print("text")
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
    ewst= text
    entities = extract_entities(text, access_token)
    list_text = text.split("\n")
    text = text.splitlines()
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
        x = i.replace("Landline:", "")
        x = str(i).replace("Cell: ", "").replace("Cell ", "").replace("M: ", "", ).replace("M ", "").replace(
            "Landline:", '').replace(" ", '')
        val = r.search(x).group() if r.search(x) else ''
        val1 = a.search(x).group() if a.search(x) else ''
        val2 = b.search(x).group() if b.search(x) else ''
        val3 = c.search(x).group() if c.search(x) else ''
        val4 = d.search(x).group() if d.search(x) else ''
        val5 = e.search(x).group() if e.search(x) else ''
        val6 = f.search(x).group() if f.search(x) else ''
        if val or val1 or val2 or val3 or val4 or val5 or val6:
            mobile_index.append(i)

    mobile = ''
    for i in mobile_index:
        print(i)
        if i.startswith("+91") or i.startswith("Cell: ") or i.startswith("Cell ") or i.startswith("M: ") \
                or i.startswith("M ") or i.startswith("Landline:") or i.startswith("91") or i.startswith("Tel.:")\
                or i.startswith("Tel:"):
            mobile = str(i)
        else:
            x = i.replace("Cell: ", "").replace("Cell ", "").replace("M: ", "", ).replace("M ", "").replace(
                "Landline:", '').replace(" ", '').replace("Tel.:","").replace("Tel: ","").replace("(","").replace(")","")
            mobile = str(x)

    ne_tree = ne_chunk(pos_tag(word_tokenize(' '.join(text))))
    iob_tagged = tree2conlltags(ne_tree)
    name = []
    extra = []
    # mobile_list = []
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
    # if type(mobile_index) == int:
    #     mobile_index = mobile_index
    # elif type(mobile_index) == str:
    #     if mobile_index.startswith("+91"):
    #         mobile_index = mobile_index



    required_entities = {'ORGANIZATION': '', 'PERSON': '', 'LOCATION': '',
                         "EMAIL": ''.join(extra[index - 1:index + 2]),
                         "MOBILE": mobile.replace("Cell: ", "").replace("Cell ", "").replace("M: ", "", ).replace("M ", "").replace(
                "Landline:", '').replace(" ", '').replace("Tel.:","").replace("Tel: ","").replace("(","").replace(")",""),
                             #mobile_index.replace("Cell: ", "").replace("Cell: ", "").replace("M: ", "", ).replace("M ", "").replace(
                              #  "Landline:", '').replace(" ", ''),
                         "CARD_TEXT": ewst,
                         "DESIGNATION": "",
                         "NAME": ' '.join(name[:2]),
                         "ADDRESS": ''
                         }

    for entity in entities['entities']:
        t = entity['type']
        if t in required_entities:
            required_entities[t] += entity['name']
    org_len = len(required_entities["ORGANIZATION"])
    if org_len > 20:
        required_entities["ORGANIZATION"] = required_entities["ORGANIZATION"][:37]
    else:
        required_entities["ORGANIZATION"] = required_entities["ORGANIZATION"][:20]
    required_entities['ADDRESS'] = required_entities["LOCATION"]
    if required_entities["NAME"] not in required_entities["PERSON"]:
        required_entities["NAME"] = required_entities["PERSON"]

    if required_entities["NAME"] in required_entities["PERSON"]:

        if len(required_entities["PERSON"].split(required_entities["NAME"])) > 1:
            designation = ' '.join(required_entities["PERSON"].split(required_entities["NAME"]))
        else:
            required_entities["PERSON"].split(required_entities["NAME"])
        # required_entities["PERSON"] =
    else:
        designation = ""
    required_entities["DESIGNATION"] = designation

    return required_entities


@app.route("/cloud-api", methods=["POST"])
def predict():
    if request.method == "POST":
        print("Read the form data!!!!")

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
    app.run(host='0.0.0.0', port=8002)





# Tree('S', [Tree('PERSON', [('Himanshu', 'NNP')]), Tree('PERSON', [('Gogia', 'NNP')]), ('Sr.', 'NNP'), ('Business', 'NNP'), ('Analyst', 'NNP'), ('A-12/3', 'NNP'), (',', ','), ('Phase', 'NNP'), ('1', 'CD'), (',', ','), Tree('PERSON', [('Naraina', 'NNP'), ('Industrial', 'NNP'), ('Area', 'NNP'), ('New', 'NNP')]), ('Delhi', 'NNP'), ('110028', 'CD'), Tree('ORGANIZATION', [('INDIA', 'NNP')]), ('|', 'NNP'), ('+91', 'VBD'), ('11', 'CD'), ('49194903', 'CD'), ('E', 'NNP'), ('himanshu.gogia', 'NN'), ('@', 'NNP'), ('sirez.com', 'NN'), ('M', 'NNP'), ('+91', 'VBD'), ('95555', 'CD'), ('29419', 'CD'), ('W', 'NNP'), ('www.sirez.com', 'NN')])



