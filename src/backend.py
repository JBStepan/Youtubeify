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
import data

load_dotenv()
DB = data.get_db("backend")

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

def task_runner(url, taskid, download_path=""):
    def progress_hook(d):
        if d['status'] == 'finished':
            DB['tasks'].update_one(
                { "id": taskid }, 
                { '$inc': { "finished": 1 }}
            )

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
            'outtmpl': os.path.join(f"downloads/{taskid}", '%(uploader)s - %(title)s.%(ext)s'),
            'playlist_items': '1-',  
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(e)
    finally:
        DB['finished_tasks'].insert_one(DB['tasks'].find_one({ "id": taskid }))
        DB['finished_tasks'].update_one({ "id": taskid }, { "$set": { "done": True, "download_url": f"http://127.0.0.1:6969/download/{taskid}.zip" } })
        DB['tasks'].delete_one({ "id": taskid })

def make_zipfile(taskid):
    data = io.BytesIO()

    files = os.listdir(f"downloads/{taskid}")

    with zipfile.ZipFile(data, mode="w") as z:
        for f in files:
            z.write(f"downloads/{taskid}/{f}", f)

    data.seek(0)
    
    return data

## Backend server communcation
app = Flask(__name__)

@app.route('/add_download', methods=["POST"])
def add_task():
    data = request.get_json()
    playlist = data.get('url')

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
        "done": False 
    })

    threading.Thread(target=task_runner, args=(playlist, taskid)).start()

    return jsonify({ 'status': 'success', 'message': taskid}), 200

@app.route('/status/<string:task>', methods=["GET"])
def get_task(task):

    count_fin = DB['finished_tasks'].count_documents({ "id": task })
    count_act = DB['tasks'].count_documents({ "id": task })

    if count_fin != 0:
        doc = DB['finished_tasks'].find_one({ "id": task})
        return jsonify({ "status": "success", "message": doc }), 200
    elif count_act == 0:
        return jsonify({ "status": "error", "message": f"No task was found with the task id of {task}" }), 400 

    doc = DB['tasks'].find_one({ "id": task})

    return jsonify({ "status": "success", "message": doc }), 200

@app.route("/status", methods=["GET"])
def get_all_tasks():
    pass

@app.route("/download/<string:task>.zip", methods=["GET"])
def download(task):
    zipfile = make_zipfile(task)

    if not zipfile:
        return jsonify({ "status": "error", "message": f"Invalid zip file" }), 400
    
    file_wrapper = FileWrapper(zipfile)

    return Response(
        file_wrapper,
        mimetype="application/zip",
        direct_passthrough=True,
        headers={'Content-Disposition': f'attachment; filename="{task}.zip"'}
    )

def run_backend():
    os.makedirs("downloads", exist_ok=True)

    app.run(host='0.0.0.0', port=6969)