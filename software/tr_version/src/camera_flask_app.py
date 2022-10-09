from flask import Flask, render_template, Response, request
import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread
from v4_tiny import *


global capture,rec_frame, grey, switch, neg, face, rec, out, dect
capture=0
grey=0
neg=0
face=0
switch=1
rec=0
dect=0

# direction位移台控制   x，y坐标
global up_dir, left_dir, right_dir, down_dir
global x, y
up_dir=0
left_dir=0
right_dir=0
down_dir=0

x=0
y=0

# light 照明控制    brightness辉度，最低为0(不亮)
global testlb, add_lb, sub_lb
add_lb=0
sub_lb=0

testlb=0

#make shots directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

#Load pretrained face detection model    
net = cv2.dnn.readNetFromCaffe('D:\\microscope_lab\\based_version\\src\\saved_model\\deploy.prototxt.txt', 'D:\\microscope_lab\\based_version\\src\\saved_model\\res10_300x300_ssd_iter_140000.caffemodel')

#instatiate flask app  
app = Flask(__name__, template_folder='./templates')


camera = cv2.VideoCapture(0)

def record(out):
    global rec_frame
    while(rec):
        time.sleep(0.05)
        out.write(rec_frame)
 

def gen_frames():  # generate frame by frame from camera
    global out, capture,rec_frame
    while True:
        success, frame = camera.read() 
        cv2.imshow("title", frame);
        if success:
            if(grey):
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if(neg):
                frame=cv2.bitwise_not(frame)    
            if(dect):
                frame=cv2.flip(v4_inference(frame), 1)
            if(capture):
                capture=0
                now = datetime.datetime.now()
                p = os.path.sep.join(['shots', "shot_{}.png".format(str(now).replace(":",''))])
                if(dect):
                    cv2.imwrite(p, cv2.flip(frame, 1))
                else:
                    cv2.imwrite(p, frame)
            
            if(rec):
                if(dect):
                    rec_frame=cv2.flip(frame, 1)
                else:
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


@app.route('/')
def index():
    return render_template('index.html')
    
    
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1
        elif  request.form.get('grey') == 'Grey':
            global grey
            grey=not grey
        elif  request.form.get('neg') == 'Negative':
            global neg
            neg=not neg
        elif request.form.get('dect') == 'Detect':
            global dect
            dect=not dect
        elif  request.form.get('stop') == 'Stop/Start':
            
            if(switch==1):
                switch=0
                camera.release()
                cv2.destroyAllWindows()
                
            else:
                camera = cv2.VideoCapture(0)
                switch=1
        elif  request.form.get('rec') == 'Start/Stop Recording':
            global rec, out
            rec= not rec
            if(rec):
                now=datetime.datetime.now() 
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter('vid_{}.avi'.format(str(now).replace(":",'')), fourcc, 20.0, (640, 480))
                #Start new thread for recording the video
                thread = Thread(target = record, args=[out,])
                thread.start()
            # elif(rec==False):
            #     out.release()
        # 位移台控制部分
        elif(request.form.get('up_dir') == '👆' or request.form.get('down_dir') == '👇' or request.form.get('left_dir') == '👈' or request.form.get('right_dir') == '👉'):
            global x, y, testlb
            if(request.form.get('up_dir') == '👆'):
                y = y + 1
            elif(request.form.get('down_dir') == '👇'):
                y = y - 1
            elif(request.form.get('left_dir') == '👈'):
                x = x -1
            elif(request.form.get('right_dir') == '👉'):
                x = x + 1
            print('({},{},{})\n'.format(x, y, testlb))
        # 照明控制部分
        elif(request.form.get('add_lb') == 'Bright' or request.form.get('sub_lb') == 'Dark'):
            if(request.form.get('add_lb') == 'Bright'):
                testlb = testlb + 1
            elif(request.form.get('sub_lb') == 'Dark' and testlb > 0):
                testlb = testlb - 1
            print('({},{},{})\n'.format(x, y, testlb))
        
    elif request.method=='GET':
        return render_template('index.html')
    return render_template('index.html')


if __name__ == '__main__':
     app.run(host = '0.0.0.0')
    
camera.release()
cv2.destroyAllWindows()     