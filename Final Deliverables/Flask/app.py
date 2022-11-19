from flask import Flask, render_template, Response, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from tensorflow import keras
import os as os
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from flask import Flask, render_template, Response, request
import cv2
import datetime, time


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
UPLOADS_PATH = r'C:\demo\Sprint 4\Flask\Upload images'
model = load_model("model.h5") #loading the model for testing


global capture,rec_frame, grey, switch, neg, face, rec, out 
capture=0
grey=0
neg=0
face=0
switch=1
rec=0

#make shots directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass
#initatiate flask app  
app = Flask(__name__, )
camera = cv2.VideoCapture(1)




app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Harish@2002'
app.config['MYSQL_DB'] = 'signup'

mysql = MySQL(app)


@app.route('/')
def index():
        return render_template('index.html')
@app.route('/Dashboard', methods =['GET', 'POST'])
def dashboard():
        if request.method == 'POST':
                if request.files['myfile'].filename != '':
                        myfile = request.files['myfile']
                        myfile.save(os.path.join(UPLOADS_PATH, secure_filename(myfile.filename)))
                        path = "C:\\demo\\Sprint 4\\Flask\\Upload images\\"+ myfile.filename
                        #loading of the image
                        img = image.load_img(path,color_mode='grayscale',target_size= (64,64))
                        x = image.img_to_array(img)#image to array
                        x = np.expand_dims(x,axis = 0)
                        predict_x=model.predict(x) 
                        classes_x=np.argmax(predict_x,axis=1)
                        classes_x
                        index=['0','1','2','3','4','5']
                        result=str(index[classes_x[0]])
                        return render_template('Dashboard.html',result="The sign is " + result)
@app.route('/sign_up', methods =['GET', 'POST'])
def signup():
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'name' in request.form and'gender' in request.form and'age' in request.form and'DOB' in request.form  and 'email' in request.form and 'password' in request.form :
                username = request.form['username']
                name = request.form['name']
                gender = request.form['gender']
                age = request.form['age']
                DOB = request.form['DOB']
                email = request.form['email']
                password = request.form['password']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM detail WHERE username = % s', (username, ))
                account = cursor.fetchone()
                if account:
                        msg = 'Account already exists !'
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                        msg = 'Invalid email address !'
                elif not re.match(r'[A-Za-z0-9]+', username):
                        msg = 'Username must contain only characters and numbers !'
                elif not username or not name or not gender or not age or not DOB or not email or not password :
                        msg = 'Please fill out the form !'
                else:
                        cursor.execute('INSERT INTO detail VALUES (NULL, % s, %s, %s, %s, %s, % s, % s)', (username, name, gender, age, DOB, email, password, ))
                        mysql.connection.commit()
                        msg = 'You have successfully registered !'
        elif request.method == 'POST':
                msg = 'Please fill out the form !'
        return render_template('sign_up.html', msg = msg)
@app.route('/sign_in', methods =['GET', 'POST'])
def signin ():
        msg = ''
        if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
                email = request.form['email']
                password = request.form['password']
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute('SELECT name FROM detail WHERE email = % s AND password = % s', (email, password, ))
                name = cur.fetchone()
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM detail WHERE email = % s AND password = % s', (email, password, ))
                account = cursor.fetchone()
                if account:
                        session['loggedin'] = True
                        msg = 'Logged in successfully !'
                        return render_template('Dashboard.html', name = "😁😁 Welcome " + name['name'] +" 😁😁")
                else:
                        msg = 'Incorrect email / password !'
        return render_template('sign_in.html', msg = msg)


@app.route('/logout')
def logout():
        session.pop('loggedin', None)
        return redirect(url_for('index'))
@app.route('/introduction')
def introduction():
        return render_template('introduction.html')
@app.route('/about')
def about():
        return render_template('about.html')

def gen_frames():  # generate frame by frame from camera
    global out, capture,rec_frame
    while True:
        success, frame = camera.read()
        
        if success:
            if(face):                
                frame= detect_face(frame)
            if(grey):
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if(neg):
                frame=cv2.bitwise_not(frame)    
            if(capture):
                capture=0
                print("starting webcam...")
                cv2.namedWindow("preview")
                now = datetime.datetime.now()
                p = os.path.sep.join(['shots', "shot.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
            
            if(rec):
                rec_frame=frame
                frame= cv2.putText(cv2.flip(frame,1),"Recording...", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),4)
                frame=cv2.flip(frame,1)
            
                
            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
                
        else:
            pass

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/webcam',methods=['POST','GET'])
def webcam():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1
        elif  request.form.get('grey') == 'Grey':
            global grey
            grey=not grey
        elif request.form.get('predict') == 'Predict':
            path=r'C:\demo\Sprint 4\Flask\shots\shot.png'
            #loading of the image
            img = image.load_img(path,color_mode='grayscale',target_size= (64,64))
            x = image.img_to_array(img)#image to array
            x = np.expand_dims(x,axis = 0)
            predict_x=model.predict(x) 
            classes_x=np.argmax(predict_x,axis=1)
            classes_x
            index=['0','1','2','3','4','5']
            result=str(index[classes_x[0]])
            return render_template('webcam.html',result="The sign is " + result)
        elif  request.form.get('stop') == 'Stop/Start':
            
            if(switch==0):
                switch=1
                camera.release()
                cv2.destroyAllWindows()
                
            else:
                camera = cv2.VideoCapture(0)
                switch=0                  
    elif request.method=='GET':
        return render_template('webcam.html')
    return render_template('webcam.html')

if __name__ == '__main__':
    app.run()
