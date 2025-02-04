import yt_dlp
import os
import random
import string
import threading
import zipfile
import io
from flask import Flask, Response, request, jsonify
from werkzeug.wsgi import FileWrapper
from dotenv import load_dotenv
from data import get_db
from datetime import datetime
from bson import json_util
from json import loads
from werkzeug.middleware.proxy_fix import ProxyFix


load_dotenv()
DB = get_db("backend")

def get_playlist_info(playlist_url):

    opts = {
        'quiet': True,
            'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    return {
        'title': info.get('title', 'Unknown'),
        'uploader': info.get('uploader', 'Unknown'),
        'count': len(info.get('entries', [])),
        'url': playlist_url
    }

def task_runner(url, taskid, download_path="", no_folder=False, no_url=False, base_url=""):
    def progress_hook(d):
        if d['status'] == 'finished':
            DB['tasks'].update_one(
                { "id": taskid }, 
                { '$inc': { "finished": 1 }}
            )

    path = ""
    if download_path == "" and no_folder == False:
        path = os.path.join(f"/downloads/{taskid}", '%(uploader)s - %(title)s.%(ext)s')
    elif no_folder == True:
        path = os.path.join(f"/downloads/", '%(uploader)s - %(title)s.%(ext)s')
    elif download_path:
        if no_folder == False:
            path = os.path.join(f"{download_path}/{taskid}", '%(uploader)s - %(title)s.%(ext)s')
        else:
            path = os.path.join(f"{download_path}", '%(uploader)s - %(title)s.%(ext)s')

    try:
        ydl_opts = {
            'progress_hooks': [progress_hook],
            "quiet": True,
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '256',
                },
                {
                    'key': 'FFmpegMetadata',  
                    'add_metadata': True
                },
                {
                    'key': 'EmbedThumbnail',  
                    'already_have_thumbnail': False
                }
            ],
            'writethumbnail': True,  
            'writeinfojson': False,  
            'outtmpl': path,
            'playlist_items': '1-',  
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(e)
    finally:
        DB['finished_tasks'].insert_one(DB['tasks'].find_one({ "id": taskid }))
        if no_url == True:
            DB['finished_tasks'].update_one(
            { "id": taskid }, 
            { "$set": 
                { "done": True, 
                  "done_at": datetime.now()
                } 
            })
        else:
            DB['finished_tasks'].update_one(
            { "id": taskid }, 
            { "$set": 
                { "done": True, 
                  "download_url": f"{base_url}/download/{taskid}.zip",
                  "done_at": datetime.now()
                } 
            })
        DB['tasks'].delete_one({ "id": taskid })

def make_zipfile(taskid, download_path = "downloads"):
    data = io.BytesIO()

    files = os.listdir(f"/{download_path}/{taskid}")

    with zipfile.ZipFile(data, mode="w") as z:
        for f in files:
            z.write(f"/{download_path}/{taskid}/{f}", f)

    data.seek(0)
    
    return data

## Backend server communcation
app = Flask(__name__)

if os.getenv("BEHIND_PROXY", "false").lower() == "true":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

@app.route('/add_download', methods=["POST"])
def add_task():
    data = request.get_json()

    playlist = data.get("url")
    download_path = data.get("download_path", "")
    no_folder = data.get("no_folder", False)
    no_url = data.get("no_url", False)

    base_url = request.host_url

    if playlist == None:
        return jsonify({ "status": "error", "message": "No URL was provided" }), 400

    taskid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    playlist_info = get_playlist_info(playlist)
    DB["tasks"].insert_one({ 
        "id": taskid, 
        "url": playlist_info['url'], 
        "count": playlist_info['count'], 
        "finished": 0, 
        "title": playlist_info['title'], 
        "uploader": playlist_info['uploader'], 
        "done": False,
        "created_at": datetime.now()
    })

    threading.Thread(target=task_runner, args=(playlist, 
                                               taskid, 
                                               download_path, 
                                               no_folder, 
                                               no_url, 
                                               base_url), name=taskid).start()

    return jsonify({ 'status': 'success', 'message': taskid}), 200

@app.route('/status/<string:task>', methods=["GET"])
def get_task(task):

    count_fin = DB['finished_tasks'].count_documents({ "id": task })
    count_act = DB['tasks'].count_documents({ "id": task })

    if count_fin != 0:
        doc = DB['finished_tasks'].find({ "id": task }, { "_id": 0 })
        return jsonify({ "status": "success", "message": loads(json_util.dumps(doc))}), 200
    elif count_act == 0:
        return jsonify({ "status": "error", "message": f"No task was found with the task id of {task}" }), 400 

    doc = DB['tasks'].find({ "id": task}, { "_id": 0 })

    return jsonify({ "status": "success", "message": loads(json_util.dumps(doc)) }), 200

@app.route("/status", methods=["GET"])
def get_all_tasks():
    docs = list(DB["tasks"].find({}, { "_id": 0}))

    print(docs)

    if docs.__len__() == 0:
        return jsonify({ "status": "error", "message": "There are no tasks in the queue"}), 400
    
    return jsonify({ "status": "success", "message": loads(json_util.dumps(docs)) })


@app.route("/download/<string:task>.zip", methods=["GET"])
def download(task):
    zipfile = make_zipfile(task)

    if not zipfile:
        return jsonify({ "status": "error", "message": "Invalid zip file" }), 400
    
    file_wrapper = FileWrapper(zipfile)

    return Response(
        file_wrapper,
        mimetype="application/zip",
        direct_passthrough=True,
        headers={'Content-Disposition': f'attachment; filename="{task}.zip"'}
    )
