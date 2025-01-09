from flask import Flask, Response, request, jsonify
import yt_dlp
import os
import random
import string
import threading
import zipfile
import io
from werkzeug.wsgi import FileWrapper
from dotenv import load_dotenv
from data import task_progress, finished_tasks

load_dotenv()

# Grabs the infomation of the playlist
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

def task_runner(url, taskid):
    def progress_hook(d):
        if d['status'] == 'finished':
            task_progress[taskid]['finished'] += 1

    try:
        # YT-DLP options
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
                    'key': 'FFmpegMetadata',  # Embed metadata into audio
                    'add_metadata': True
                },
                {
                    'key': 'EmbedThumbnail',  # Embed thumbnail into MP3
                    'already_have_thumbnail': False
                }
            ],
            'writethumbnail': True,  # Download thumbnails
            'writeinfojson': False,  # Save metadata in JSON
            'outtmpl': os.path.join(f"downloads/{taskid}", '%(uploader)s - %(title)s.%(ext)s'),
            'playlist_items': '1-',  # Download all items in the playlist
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(e)
    finally:
        finished_tasks[taskid] = task_progress[taskid]
        finished_tasks[taskid]['done'] == True
        task_progress.pop(taskid)

def make_zipfile(taskid):
    data = io.BytesIO()

    files = os.listdir(f"downloads/{taskid}")

    with zipfile.ZipFile(data, mode="w") as z:
        for f in files:
            z.write(f"downloads/{taskid}/{f}")

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
    task_progress[taskid] = { 'url': playlist_info['url'], 'count': playlist_info['count'], 'finished': 0, 'title': playlist_info['title'], 'done': False }

    threading.Thread(target=task_runner, args=(playlist, taskid)).start()

    return jsonify({ 'status': 'success', 'message': taskid}), 200

@app.route('/status/<string:task>', methods=["GET"])
def get_task(task):
    if finished_tasks.get(task) != None:
        return jsonify({ "status": "success", "message": finished_tasks[task] }), 200
    elif task_progress.get(task) == None:
        return jsonify({ "status": "error", "message": f"No task was found with the task id of {task}" }), 400 

    return jsonify({ "status": "success", "message": task_progress[task] }), 200

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

    app.run(host='0.0.0.0', port=os.getenv("BACKEND_PORT"))