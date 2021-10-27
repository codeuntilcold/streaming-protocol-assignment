import sys
from tkinter import Tk

from werkzeug.utils import redirect
from Client import Client

# import threading
# from VideoStream import VideoStream
# import time
from flask import Flask, render_template, request, Response, url_for

app = Flask(__name__)

# video = VideoStream('movie.Mjpeg')

PREFIX = 'cache-'
POSTFIX = '.jpg'
state = ''

def generate_frames():
    i = 0
    while True:
        try:
            # time.sleep(0.05)
            # image = video.nextFrame()
            image = open(PREFIX + str(client.sessionId) + POSTFIX, 'r')
            if image:
                print('Got ', i)
                i += 1
            # print(image)
            # return image
            frame = bytes(image)
            yield(b'--frame\r\n'
                b'Content-Type: image/jpg\r\n\r\n' + frame + b'\r\n')
        except IOError:
            print(IOError)
    # client.updateMovie()



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream/play')
def stream():
    # if state == 'play':
    return Response(client.listenRtp(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # else:
    #     cachename = PREFIX + str(client.sessionId) + POSTFIX
    #     image = open(cachename, 'r')
    #     return (b'Content-type: image/jpg\r\n\r\n' + bytes(image))


@app.route('/stream/control')
def stream_control():
    global state
    state = request.args.get('state')

    if state == 'setup':
        client.setupMovie()
    elif state == 'play':
        client.playMovie()
    elif state == 'pause':
        client.pauseMovie()
    elif state == 'teardown':
        client.exitClient()

    return index()

if __name__ == '__main__':

    try:
	    serverAddr = sys.argv[1]
	    serverPort = sys.argv[2]  # where the server is listening on
	    rtpPort = sys.argv[3]     # where the RTP packets are received
	    fileName = sys.argv[4]
    except:
        print("[Usage: App.py Server_name Server_port RTP_port Video_file]\n")

    root = Tk()
    client = Client(root, serverAddr, serverPort, rtpPort, fileName)

    app.run(debug=True)
    # root.mainloop()
