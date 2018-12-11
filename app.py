import os
import spotipy
from spotipy import util
import requests
import flask
import base64
from flask import Flask, render_template, Response, request, redirect, url_for, session,flash
import random
from flask_pymongo import PyMongo
from pymongo import MongoClient   #docs: http://api.mongodb.com/python/current/index.html
import config
import json
import sys
from werkzeug.utils import secure_filename
from PIL import Image
import cognitive_face as CF 
from camera import VideoCamera
video_camera = None
global_frame = None

#file upload requirements
UPLOAD_FOLDER = './imageuploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

#-- AZURE REQUIREMENTS --#
# azureheaders = {
#     'Content-Type': 'application/json',
#     'Ocp-Apim-Subscription-Key': config.AzureAPIKey,
# }
# azure_qs = { 
#     'returnFaceAttributes': 'emotion' 
# }
# azure_body = {
#     'url': 'https://pbs.twimg.com/profile_images/1034484319866302472/O8nhACsb_400x400.jpg'
# }
azure_api = 'https://westus.api.cognitive.microsoft.com/face/v1.0/detect'

#-- SPOTIPY REQUIREMENTS --#
client_id = config.client_id
client_secret = config.client_secret
redirect_uri = config.redirect_uri

scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

session = {}
db = {}
sp = {}
#connect to mongo server 
print('...connecting to mongo server')
client = MongoClient()
db = client.database
songs = db.songs
users = db.users
username = ''
mood = 0.0
loggedin = False
image = None
token = config.token


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'w49tgunw4*&G#Er3jifg'


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    global username, scope, client_id, client_secret, redirect_uri, token
    username = request.form['username']
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    #token = request.args['code']
    def authenticate(): #authenticate user using spotify
        global sp, token
        print('...now connecting to spotify')
        print('token: ', token)
        sp = spotipy.Spotify(auth=token)
        print('\n\n\n\n\n\n authenticated \n\n\n\n\n')
        print(sp)
    authenticate()
    return login(username)


@app.route('/callback')
def callback():
    global token, username
    token = request.args['code']
    def authenticate(): #authenticate user using spotify
        global sp, token
        print('...now connecting to spotify')
        print('token: ', token)
        sp = spotipy.Spotify(auth=token)
        print(sp)
    authenticate()
    return login(username)

#main index page
@app.route('/')
def gotomain():
    return render_template('index.html')

@app.route('/gotologin')
def gotologin():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/gotohistory')
def gotohistory():
    return render_template('history.html')
#login using spotify oauth
@app.route('/login', methods = ['POST'])
def login(username):
    global token
    print('...now inside login')
    print('...authenticated')
    print(sp)
    #grab username to create/lookup account
    if db.users.find_one({'username':username}):
        print('user exists! getting history')
        user = db.users.find_one({'username': username})
        session['username'] = user['username']
        loggedin = True
        return render_template('dashboard.html', name = user['username'], loggedIn = True)
    else:
        details = {'username': username} 
        db.users.insert_one(details)
        loggedin = True
        print('...successfully created user')
        return render_template('dashboard.html', name=username, loggedIn = True)
    print('')

@app.route('/history', methods=['GET'])
def history():
    if (loggedin and db.users.find_one({'username': username})):
        history = db.history.find_one({'username': username}) #should return all songs
        return render_template('history.html', name = username, loggedIn = True, history = history)
    return render_template('history.html', error = True, error_message = "User it not logged in")

@app.route('/getemotions', methods=['GET'])
def getemotions():
    print('... getting emotions from image')
    KEY = config.AzureAPIKey  # Replace with a valid Subscription Key here.
    CF.Key.set(KEY)
    print('...set key')
    BASE_URL = 'https://eastus.api.cognitive.microsoft.com/face/v1.0/'  # Replace with your regional Base URL
    CF.BaseUrl.set(BASE_URL)
    print('...set the url')
    img = './static/buf.jpeg'
    print('...opened image')
    result = CF.face.detect(img, attributes='emotion')
    print('...got some results')
    #print(result)
    moods = result[0]['faceAttributes']['emotion']
    print('...printing moods')
    print(moods)
    db.moods.insert_one(moods)
    moodsy = 0.0
    overpowered_emotion = ''
    iteration_count = 0
    for key in moods:
        if iteration_count == 8: # Cognitive face api is broken 
            break
        print(key)
        if moods[key] > moodsy:
            moodsy = moods[key]
            overpowered_emotion = key
        
        iteration_count += 1
    print('overpowered_emotion: ', overpowered_emotion)
    return createplaylist(overpowered_emotion)

def createplaylist(overpowered_emotion):
    if overpowered_emotion == 'happiness':
        mood = 1.0
    elif overpowered_emotion == 'surprise':
        mood = 0.7
    elif overpowered_emotion == 'neutral':
        mood = 0.5
    elif overpowered_emotion == 'contempt':
        mood = 0.4
    elif overpowered_emotion == 'fear':
        mood = 0.3
    elif overpowered_emotion == 'sadness':
        mood = 0.2
    elif overpowered_emotion == 'disgust':
        mood = 0.1
    sample = True
    if (sample):
        #get personalized artists for playlist
        print('...now getting your personalized artists')
        top_artists_name = []
        top_artists_uri = []
        ranges = ['short_term','medium_term','long_term']
        print('...now printing sp\n\n\n\n\n\n')
        print(sp)
        for r in ranges:
            top_artists_all_data = sp.current_user_top_artists(limit=20, time_range = r)
            top_artists_data = top_artists_all_data['items']
            for artist_data in top_artists_data:
                if artist_data["name"] not in top_artists_name:
                    top_artists_name.append(artist_data['name'])
                    top_artists_uri.append(artist_data['uri'])
        followed_artists_all_data = sp.current_user_followed_artists(limit=20)
        followed_artists_data = (followed_artists_all_data['artists'])
        for artist_data in followed_artists_data['items']:
            if artist_data["name"] not in top_artists_name:
                top_artists_name.append(artist_data['name'])
                top_artists_uri.append(artist_data['uri'])

        #look at top tracks from artists
        print('...now getting personalized tracks')
        top_tracks_uri = []
        top_tracks_names = []
        top_tracks_artists = []
        top_tracks_albums = []
        for artist in top_artists_uri:
            top_tracks_all_data = sp.artist_top_tracks(artist)
            top_tracks_data = top_tracks_all_data['tracks']
            for track_data in top_tracks_data:
                # print('\n\n')
                # print(track_data)
                # print('\n\n')
                top_tracks_uri.append(track_data['uri'])
                top_tracks_names.append(track_data['album']["href"])
                top_tracks_artists.append(track_data["name"])
                top_tracks_albums.append(track_data['album']['name'])

        #select songs based on mood returned
        print('...now selecting tracks based on mood')
        selected_tracks_uri = []
        selected_tracks_names = []
        selected_tracks_artist = []
        selected_tracks_albums = []
        random.shuffle(top_tracks_uri)
        for i in range(len(top_tracks_uri)):
            tracks_all_data = sp.audio_features(top_tracks_uri[i])
            for track_data in tracks_all_data:
                # print('\n\n')
                # print(track_data)
                # print('\n\n')
                try:
                    if mood < 0.10: #feeling really bad
                        if (0 <= track_data["valence"] <= (mood + 0.15) and track_data["danceability"] <= (mood * 8) and track_data["energy"] <= (mood * 10)):
                            selected_tracks_uri.append(top_tracks_uri[i])
                            selected_tracks_names.append(top_tracks_names[i])
                            selected_tracks_artist.append(top_tracks_artists[i])
                            selected_tracks_albums.append(top_tracks_albums[i])
                    elif 0.10 <= mood < 0.25:
                        if ((mood - 0.075) <= track_data["valence"] <= (mood + 0.075) and track_data["danceability"] <= (mood * 4) and track_data["energy"] <= (mood * 5)):
                            selected_tracks_uri.append(top_tracks_uri[i])
                            selected_tracks_names.append(top_tracks_names[i])
                            selected_tracks_artist.append(top_tracks_artists[i])
                            selected_tracks_albums.append(top_tracks_albums[i])
                    elif 0.25 <= mood < 0.5:
                        if ((mood - 0.05) <= track_data["valence"] <= (mood + 0.05) and track_data["danceability"] <= (mood * 1.75) and track_data["energy"] <= (mood * 1.75)):
                            selected_tracks_uri.append(top_tracks_uri[i])
                            selected_tracks_names.append(top_tracks_names[i])
                            selected_tracks_artist.append(top_tracks_artists[i])
                            selected_tracks_albums.append(top_tracks_albums[i])
                    elif 0.5 <= mood < 0.75:
                        if ((mood - 0.075) <= track_data["valence"] <= (mood + 0.075) and track_data["danceability"] >= (mood / 2.5) and track_data["energy"] >= (mood / 2)):
                            selected_tracks_uri.append(top_tracks_uri[i])
                            selected_tracks_names.append(top_tracks_names[i])
                            selected_tracks_artist.append(top_tracks_artists[i])
                            selected_tracks_albums.append(top_tracks_albums[i])
                    elif 0.75 <= mood < 0.9:
                        if ((mood - 0.075) <= track_data["valence"] <= (mood + 0.075) and track_data["danceability"] >= (mood / 2) and track_data["energy"] >= (mood / 1.75)):
                            selected_tracks_uri.append(top_tracks_uri[i])
                            selected_tracks_names.append(top_tracks_names[i])
                            selected_tracks_artist.append(top_tracks_artists[i])
                            selected_tracks_albums.append(top_tracks_albums[i])
                    elif mood >= 0.9:
                        if ((mood - 0.15) <= track_data["valence"] <= 1 and track_data["danceability"] >= (mood / 1.75) and track_data["energy"] >= (mood / 1.5)):
                            selected_tracks_uri.append(top_tracks_uri[i])
                            selected_tracks_names.append(top_tracks_names[i])
                            selected_tracks_artist.append(top_tracks_artists[i])
                            selected_tracks_albums.append(top_tracks_albums[i])
                except TypeError as te:
                        continue
        #create the actual playlist
        print('... now creating your playlist')
        user_all_data = sp.current_user()
        user_id = user_all_data["id"]
        playlist_all_data = sp.user_playlist_create(user_id, "Big Mood: " + overpowered_emotion)
        print('\n\n...printing playlist data...\n\n')
        playlist_id = playlist_all_data["id"]
        print('...printing playlist id')
        print(playlist_all_data)
        random.shuffle(selected_tracks_uri)
        sp.user_playlist_add_tracks(user_id, playlist_id, selected_tracks_uri[0:30]) #playlist can be seen in spotify app
        uri = playlist_all_data['owner']['uri']
        #return render_template('dashboard.html', name = username, loggedIn = True, palylisturis = selected_tracks_uri, artists = selected_tracks_artist, names = selected_tracks_names)
        return render_template('myplaylist.html', uri=uri)
    else:
        print('...theres been an error authenticating the user')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # # check if the post request has the file part
        # if 'file' not in request.files:
        #     flash('No file part')
        #     return redirect('getplaylist.html')
        file = request.files['image']
        # # if user does not select file, browser also
        # # submit a empty part without filename
        # if file.filename == '':
        #     flash('No selected file')
        #     return redirect('getplaylist.html')
        if file and allowed_file(file.filename):
            faceimage = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], faceimage))
            image = Image.open('static/buf.jpeg')
            return redirect(url_for('/getemotions',
                                    filename=faceimage, image=image))
    return 

@app.route('/logout')
def logout():
    loggedin = False
    mood = 0
    return render_template('index.html')


@app.route('/record_status', methods=['POST'])
def snap():
    global video_camera 
    if video_camera == None:
        video_camera = VideoCamera()

    json = request.get_json()

    status = json['status']
    print("taking picture...")
    video_camera.start_record()
    video_camera = None
    return jsonify(result="started")

def video_stream():
    global video_camera 
    global global_frame

    if video_camera == None:
        video_camera = VideoCamera()
        
    while True:
        frame = video_camera.get_frame()

        if frame != None:
            global_frame = frame
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n\r\n')

@app.route('/video_viewer')
def video_viewer():
    return Response(video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=1)