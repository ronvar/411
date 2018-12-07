import spotipy
from spotipy import util
import requests
import flask
from flask import Flask, render_template, Response, request, redirect, url_for, session,flash
import random
from flask_pymongo import PyMongo
from pymongo import MongoClient   #docs: http://api.mongodb.com/python/current/index.html
import config
import json
import sys



client_id = config.client_id
client_secret = config.client_secret
redirect_uri = config.redirect_uri

scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

session = {}
db = {}

#connect to mongo server 
print('...connecting to mongo server')
client = MongoClient()
db = client.database
songs = db.songs
users = db.users

app = Flask(__name__)
app.secret_key = b'w49tgunw4*&G#Er3jifg'




if len(sys.argv) > 1:
    username = sys.argv[1]
    mood = float(sys.argv[2])
else: 
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)

if token:
    def authenticate():
        print('...now connecting to spotify')
        sp = spotipy.Spotify(auth=token)
        return sp

    def getpersonalizedartists(sp):
        print('...now getting your personalized artists')
        top_artists_name = []
        top_artists_uri = []
        ranges = ['short_term','medium_term','long_term']
        for r in ranges:
            top_artists_all_data = sp.current_user_top_artists(limit=60, time_range = r)
            top_artists_data = top_artists_all_data['items']
            for artist_data in top_artists_data:
                if artist_data["name"] not in top_artists_name:
                    top_artists_name.append(artist_data['name'])
                    top_artists_uri.append(artist_data['uri'])
        followed_artists_all_data = sp.current_user_followed_artists(limit= 60)
        followed_artists_data = (followed_artists_all_data['artists'])
        for artist_data in followed_artists_data['artists']:
            if artist_data["name"] not in top_artists_name:
                top_artists_name.append(artist_data['name'])
                top_artists_uri.append(artist_data['uri'])
        return top_artists_uri

    def aggregate_top_tracks(sp, top_artists_uri):
        print('...now getting personalized tracks')
        top_tracks_uri = []
        for artist in top_artists_uri:
            top_tracks_all_data = sp.artist_top_tracls(artist)
            top_tracks_data = top_tracks_all_data['tracks']
            for track_data in top_tracks_data:
                top_tracks_uri.append(track_data['uri'])
        return top_tracks_uri

    def select_tracks(sp, top_tracks_uri):
        print('...now selecting tracks based on mood')
        selected_tracks_uri = []
        random.shuffle(top_tracks_uri)
        for tracks in list(group(top_tracks_uri, 60)):
            tracks_all_data = sp.audio_features(tracks)
            for track_data in tracks_all_data:
                try:
                    if mood < 0.10: #feeling really bad
                        if (0 <= track_data["valence"] <= (mood + 0.15) and track_data["danceability"] <= (mood * 8) and track_data["energy"] <= (mood * 10)):
                            selected_tracks_uri.append(track_data["uri"])
                    elif 0.10 <= mood < 0.25:
                        if ((mood - 0.075) <= track_data["valence"] <= (mood + 0.075) and track_data["danceability"] <= (mood * 4) and track_data["energy"] <= (mood * 5)):
                            selected_tracks_uri.append(track_data["uri"])
                    elif 0.25 <= mood < 0.5:
                        if ((mood - 0.05) <= track_data["valence"] <= (mood + 0.05) and track_data["danceability"] <= (mood * 1.75) and track_data["energy"] <= (mood * 1.75)):
                            selected_tracks_uri.append(track_data["uri"])
                    elif 0.5 <= mood < 0.75:
                        if ((mood - 0.075) <= track_data["valence"] <= (mood + 0.075) and track_data["danceability"] >= (mood / 2.5) and track_data["energy"] >= (mood / 2)):
                            selected_tracks_uri.append(track_data["uri"])
                    elif 0.75 <= mood < 0.9:
                        if ((mood - 0.075) <= track_data["valence"] <= (mood + 0.075) and track_data["danceability"] >= (mood / 2) and track_data["energy"] >= (mood / 1.75)):
                            selected_tracks_uri.append(track_data["uri"])
                    elif mood >= 0.9:
                        if ((mood - 0.15) <= track_data["valence"] <= 1 and track_data["danceability"] >= (mood / 1.75) and track_data["energy"] >= (mood / 1.5)):                            selected_tracks_uri.append(track_data["uri"])
                except TypeError as te:
                        continue
        return selected_tracks_uri

    def create_playlist(sp, selected_tracks_uri):
        print('... now creating your playlist')
        user_all_data = sp.current_user()
        user_id = user_all_data["id"]
        playlist_all_data = sp.user_playlist_create(user_id, "Big Mood: " + mood)
        playlist_id = playlist_all_data["id"]
        random.shuffle(selected_tracks_uri)
        sp.user_playlist_add_tracks(user_id, playlist_id, selected_tracks_uri[0:30])



@app.route('/')
def main():
    return render_template('index.html')