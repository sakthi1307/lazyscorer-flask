import os
from flask import Flask, json, request, jsonify, send_file
from pymongo import MongoClient
import urllib.parse
import uuid
from transformers.pipelines import question_answering
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
from predic import cross_encoder, univesal_sentence_encoder, bi_encoder
from bson.objectid import ObjectId
from bson import json_util
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
import pypdfium2 as pdfium
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
import datetime
username =urllib.parse.quote_plus(os.environ.get('MONGO_USERNAME'))
password = urllib.parse.quote_plus(os.environ.get('MONGO_PASSWORD'))
MONGO_URL = urllib.parse.quote_plus(os.environ.get('MONGO_URL'))

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOADS_PATH = "user-uploads"
app.config['UPLOAD_FOLDER'] = UPLOADS_PATH

client = MongoClient('mongodb://%s:%s@%s' % (username, password,MONGO_URL))

db = client.lazyscorer

assignment_template = {
        "set_by":"Q123423423423", #Teacher ID
        "questions":[{"question":"any question","answer":"correct answer"}],
        "due_date":datetime.datetime(2015, 7, 8, 18, 17, 28, 324000),
        "created_at":datetime.datetime.utcnow(),
        "tags":["tag1","tag2","tag3"]
        }



post_id = db.mycol.insert_one(assignment_template).inserted_id


def token_required_newer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        print(token)
        if token:

            # Here, you would check if the token is valid and belongs to a user
            # For example, you could query your MongoDB 'lazyscorer' collection for a user with this token
            # If the token is valid, you can proceed with the decorated function
            current_user = db.users.find_one({'token':token.split(" ")[1]})
            return f(current_user,*args, **kwargs)
    return decorated_function

def detect_document(path):
    """Detects document features in an image."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    image_context = vision.ImageContext(language_hints=['en-t-i0-handwrit'])

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image,image_context=image_context)
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return(response.full_text_annotation.text.replace('\r', '').replace('\n', ''))


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    if request.form['user-type'] and request.form['user-type']!='student':
        userType = request.form['user-type']
        user_tags = []
    else:
        userType = 'student'
        user_tags = list(request.form['user-tags'].split(","))
    if email and password:
        # Hash the password using a secure hashing algorithm
        hashed_password = generate_password_hash(password)
        # Generate a unique token for the user
        token = str(uuid.uuid4())
        # Create a new user document in the 'lazyscorer' collection
        user = {'email': email, 'password': hashed_password, 'token': token, 'user_type': userType,'user_tags':user_tags}
        if db.users.find_one({'email':user['email']}):
            return jsonify({'error':"user already exists"})
        db.users.insert_one(user)
        return jsonify({'Success': "sucessfully registered"})
    else:
        return jsonify({'error': 'Missing email or password'}), 400


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if email and password:
        # Find the user in the 'lazyscorer' collection
        user = db.users.find_one({'email': email})
        # print(user['password'],password)
        if user and check_password_hash(user['password'],password):
            # If the password matches, return the user's token
            return jsonify({'token': user['token'],'user-type':user['user_type']})
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    else:
        return jsonify({'error': 'Missing email or password'}), 400


@app.route('/setassignment',methods=['POST'])
@token_required_newer
def set_assignment(current_user):
    # if current_user['type']=='Teacher':
        # return jsonify({'error':"accout not Professor"}),400
    setters_id = current_user['_id']
    try:
        print("assignments",json.loads(request.form['questions']))
        assignment = {
            'set_by':setters_id,
            'questions':json.loads(request.form['questions']),
            'date_created':datetime.datetime.utcnow(),
            'date_due':datetime.datetime.strptime(request.form['due_date'], "%Y-%m-%d"),
            'tags':list(request.form['tags'].split(',')),
            }
        if request.form['title']:
            assignment['title'] = request.form['title']    


        if request.form['description']:
            assignment['description'] = request.form['description']    
        test_id = db.assignments.insert_one(assignment).inserted_id
        print("testid",test_id)
        return jsonify({'success':"created an assignment",'test_id':str(test_id)}),200
    except Exception as e:
        return jsonify({'error':e}),400


@app.route('/setscore',methods=['POST'])
@token_required_newer
def get_score(current_user):

    try:
        assignment_id = request.form['assignment_id']
        assignment = db.submitted.find_one({'_id':ObjectId(assignment_id)})
        print("assignment",assignment)
        test = db.assignments.find_one({'_id':assignment['test_id']})
        score = []
        answers = [i['answer'] for i in test['questions']]
        submitted_answers = assignment['answers']
        for idx,i in enumerate(answers):
            score1 = cross_encoder(i,submitted_answers[idx])*40
            score2 = univesal_sentence_encoder(i,submitted_answers[idx])*30
            score3 = bi_encoder(i,submitted_answers[idx])*30
            score.append(score1+score2+score3)
            print("score",score[-1])
        db.submitted.update_one({'_id':ObjectId(assignment_id)},{"$set":{"scores":json.loads(json_util.dumps(score))}})
        return jsonify({"sucess":"scored the test ","scores":score}),200
    except Exception as e:
        return jsonify({'error':"cannot score %s"%e,'expection':e}),400

@app.route('/getassigned',methods=['GET'])
@token_required_newer
def get_assigned(current_user):
    try:
        assignments = db.assignments.find({'set_by':ObjectId(current_user['_id'])})
        return jsonify({"asignments":json.loads(json_util.dumps(assignments))}),200
    except Exception as e:
        return jsonify({"error:%s" % e}), 400

@app.route('/submitassignment',methods=['POST'])
@token_required_newer
def submit_assignment(current_user):
    try:
        print("hello world")
        submited_on = datetime.datetime.utcnow()
        submitted_by = current_user["_id"]
        test_id = ObjectId(request.form['test-id'])

        isduplicate = list(db.submitted.find({'submitted_by':current_user['_id'],'test_id':test_id}))
        print(isduplicate)
        if len(isduplicate)!=0:
            return jsonify({'error':'dupplicate assignment'}),400
        # images_link = json.loads(request.form['images-link'])
        answers = []
        print(test_id)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({"error":"no file selected"})
        # filename = secure_filename(file.filename)
        # print(filename)

        isExist = os.path.exists(app.config['UPLOAD_FOLDER'])
        if not isExist:
            # Createa new directory because it does not exist
            os.makedirs(app.config['UPLOAD_FOLDER']+"/pdf/")

        filename = str(test_id)+str(current_user['_id'])+".pdf"
        filename_abs = os.path.join(basedir,app.config['UPLOAD_FOLDER']+"/pdf/", filename)
        file.save(filename_abs)    
        pdf = pdfium.PdfDocument(filename_abs)
        n_pages = len(pdf)  # get the number of pages in the document
        print("no_pages",n_pages)
        page_indices = [i for i in range(n_pages)]  # all pages
        renderer = pdf.render(pdfium.PdfBitmap.to_pil,page_indices = page_indices,scale = 300/72)
        photos_dir =app.config['UPLOAD_FOLDER']+'/'+ str(test_id)+"/"+str(submitted_by)
        os.makedirs(photos_dir)
        for i, image in zip(page_indices, renderer):
            image.save(photos_dir+"/out_%0*d.png" % (2,i))
            answers.append(detect_document(photos_dir+"/out_%0*d.png" % (2,i)))
        # print(images_link,answers,"this is the list")

        assignment = {
                'submitted_on':submited_on,
                "submitted_by":submitted_by,
                'test_id':test_id,
                'pdf_link':filename,
                'answers':answers
                }
        assignment_id = db.submitted.insert_one(assignment).inserted_id
        return jsonify({"success":"assignment submitted with id %s"% assignment_id,'assignment_id': str(assignment_id)}),200
    except Exception as e:
        return jsonify({"error":str(e)})

@app.route('/getassignments',methods=['GET'])
@token_required_newer
def get_assignments(current_user):
    try:
        user_tags = current_user['user_tags']
        tests_match = list(db.assignments.find({'tags':{'$in':user_tags}}))
        tests_submited = list(db.submitted.find({'submitted_by':current_user['_id']}))
        test_submitted_ids = set()
        test_matching = []
        for i in tests_submited:
            test_submitted_ids.add(ObjectId(i['test_id']))

        for i in tests_match:     
            if i['_id'] not in test_submitted_ids:
                test_matching.append(i)
    
        for i in test_matching:
            for k in i['questions']:
                k.pop('answer')
        return jsonify({"assignments":json.loads(json_util.dumps(test_matching[::-1])),"submitted":json.loads(json_util.dumps(tests_submited[::-1]))}),200
    except Exception as e:
        return jsonify({"error":str(e)}),400


@app.route('/submitted',methods=['POST'])
@token_required_newer
def get_submitted(current_user):
    try:
        assignment_id = request.form['assignment_id']
        assignment = db.submitted.find_one({'_id':ObjectId(assignment_id)})
        test = db.assignments.find_one({'_id':assignment['test_id']})
        return jsonify({"assignment":json.loads(json_util.dumps(test)),"submitted":json.loads(json_util.dumps(assignment))}),200
    except Exception as e:
        return jsonify({"error":str(e)}),400



@app.route('/assignment',methods=['POST'])
@token_required_newer
def get_assignment(current_user):
    try:
        assignment_id = request.form['assignment_id']
        test = db.assignments.find_one({'_id':ObjectId(assignment_id)})
        if current_user['user_type'] and current_user['user_type']=="student":
            for k in test['questions']:
                k.pop('answer')
        return jsonify({"assignment":json.loads(json_util.dumps(test))}),200
    except Exception as e:
        return jsonify({"error":str(e)}),400


@app.route('/assignment_overview',methods=['POST'])
@token_required_newer
def get_submissions(current_user):
    try:
        assignment_id = request.form['assignment_id']
        submitted = db.submitted.find({'test_id':ObjectId(assignment_id)})
        return jsonify({"submitted":json.loads(json_util.dumps(submitted))}),200
    except Exception as e:
        return jsonify({"error":str(e)}),400


@app.route('/downloadpdf/<pdf_uri>',methods=['GET'])
def get_submitted_pdf(pdf_uri):
    try:
        filename =secure_filename(pdf_uri)
        filename_abs = os.path.join(basedir,app.config['UPLOAD_FOLDER'],'/pdf/', filename)
        file = send_file(filename_abs,as_attachment=True)
        print(filename)
        return file
    except Exception as e:
        print(str(e))
        return jsonify({'error':str(e)}),400
