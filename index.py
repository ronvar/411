import cv2
import time
import json
import numpy as np
import base64
import requests
from flask import Flask, render_template
from pymongo import MongoClient


app = Flask(__name__)

# @app.route("/")
# def main():
# 	header = {
# 		"content-type":"application/json"
# 	}

# 	cap = cv2.VideoCapture(0)
# 	ret, frame = cap.read()
# 	payload = {
# 		"frame_b64": frame.tolist(),
# 		"name": "Minh"
# 	}

# 	client = MongoClient()

# 	db = client.pymongo_test

# 	while(True):
# 		# Capture frame-by-frame
# 		ret, frame = cap.read()

# 		# Our operations on the frame come here
# 		cv2.imwrite("./buf.jpeg", frame)
# 		with open("buf.jpeg", "rb") as f:
# 			payload["frame_b64"] = base64.b64encode(f.read())

# 		# requests.post(url=url, headers=header, data=json.dumps(payload))
# 		with open("decoded.jpeg", "wb+") as g:
# 			g.write(base64.b64decode(payload["frame_b64"]))
# 		dbs = db.tinder4BU
# 		dbs.insert_one(payload)
# 		# Display the resulting frame
# 		# decoded = cv2.imread("decoded.jpeg")
# 		# cv2.imshow('frame',frame)
# 		# cv2.imshow('decoded',decoded)
# 		if cv2.waitKey(1) & 0xFF == ord('q'):
# 			break
# 		time.sleep(0.1)
# 		break
# 	# When everything done, release the capturing device
# 	cap.release()
# 	cv2.destroyAllWindows()
# 	return

if __name__ == "__main__":
	app.run()

@app.route("/")
def index():
	return render_template("index.html")