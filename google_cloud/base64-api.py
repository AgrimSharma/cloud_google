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

    # print(text)
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
        # if (code == 'CD' or code == "NN" or code == "JJ") and val == 'O':
        #     mobile_list.append(text)
    # print(mobile_list)
    # import pdb;pdb.set_trace()

    mobile_index = 0
    for i in list_text:
        if "+91" in i:
            mobile_index = i
            break
    print(mobile_index)
    if mobile_index.startswith("+91"):
        mobile_index = mobile_index
    else:
        mobile_split = mobile_index.replace("Cell: ","").replace("Cell: ", "").replace("M: ","",).replace("M ","").split()

        try:
            if int(mobile_split):
                pass
            else:
                mob = mobile_split.index("+91")
                mobile_index = ' '.join(mobile_split[mob:mob + 3])
        except Exception:
            # mob = mobile_split.index("91")
            # mobile_index = ''.join(mobile_split[mob:mob + 3])
        # else:
            mobile_index = mobile_index

    # print(' '.join(name[:2]))
    # print(' '.join(extra[:3]))
    index = extra.index("@")
    # print(''.join(extra[index - 1:index + 2]))
    # print(mobile_list[mobile_index: mobile_index + 2])

    # import pdb;pdb.set_trace()
    # email = re.search(r"[\w\.-]+@[\w\.-]+", t)
    email = list(filter(lambda x: re.search(r"[\w\.-]+@[\w\.-]+", x), text))
    mobile = list(filter(lambda x: re.search(r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})", str(x).replace("-", " ")), text))
    # print(mobile)
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
    if mobile:
        mobile = mobile[0]
        if "Cell: " in mobile:
            mobile = re.split(r"Cell: ", mobile)[1]
        elif "M: " in mobile:
            mobile = re.split(r"M: ", mobile)[1]
        elif "M " in mobile:
            mobile = re.split(r"M ", mobile)[1]
        if "Cell: " in mobile:
            mobile = re.split(r"Cell: ", mobile)[1]
        else:
            mobile = mobile
    else:
        mobile = mobile
    # mobile = mobile[0] if len(mobile)> 0 else ''
    required_entities = {'ORGANIZATION': '', 'PERSON': '', 'LOCATION': '',
                         "EMAIL": ''.join(extra[index - 1:index + 2]),
                         "MOBILE": mobile_index.replace("Cell: ","").replace("Cell: ", "").replace("M: ","",).replace("M ",""),
                         "CARD_TEXT": ewst,
                         "DESIGNATION": '',#text[1],
                        "NAME": ' '.join(name[:2]),
                         "ADDRESS": ''#text[2]
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
    app.run(host='0.0.0.0', port=8002)





# Tree('S', [Tree('PERSON', [('Himanshu', 'NNP')]), Tree('PERSON', [('Gogia', 'NNP')]), ('Sr.', 'NNP'), ('Business', 'NNP'), ('Analyst', 'NNP'), ('A-12/3', 'NNP'), (',', ','), ('Phase', 'NNP'), ('1', 'CD'), (',', ','), Tree('PERSON', [('Naraina', 'NNP'), ('Industrial', 'NNP'), ('Area', 'NNP'), ('New', 'NNP')]), ('Delhi', 'NNP'), ('110028', 'CD'), Tree('ORGANIZATION', [('INDIA', 'NNP')]), ('|', 'NNP'), ('+91', 'VBD'), ('11', 'CD'), ('49194903', 'CD'), ('E', 'NNP'), ('himanshu.gogia', 'NN'), ('@', 'NNP'), ('sirez.com', 'NN'), ('M', 'NNP'), ('+91', 'VBD'), ('95555', 'CD'), ('29419', 'CD'), ('W', 'NNP'), ('www.sirez.com', 'NN')])



