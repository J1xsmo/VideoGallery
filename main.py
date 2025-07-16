import os
import sqlite3
import subprocess
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024 # 16gb

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'hevc'}

DATABASE = 'database.db'

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_codec_info(file_path):
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'json',
            file_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        probe_output = json.loads(result.stdout)
        video_codec = probe_output['streams'][0]['codec_name'] if 'streams' in probe_output and probe_output[
            'streams'] else 'unknown'

        command_audio = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'json',
            file_path
        ]
        result_audio = subprocess.run(command_audio, capture_output=True, text=True, check=True)
        probe_output_audio = json.loads(result_audio.stdout)
        audio_codec = probe_output_audio['streams'][0]['codec_name'] if 'streams' in probe_output_audio and \
                                                                        probe_output_audio['streams'] else 'unknown'

        return video_codec, audio_codec
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Getting information about codec error: {e}")
        return 'unknown', 'unknown'


def transcode_video(input_path, output_path, vcodec, acodec):
    try:
        subprocess.run([
            'ffmpeg',
            '-i', input_path,
            '-c:v', vcodec,
            '-c:a', acodec,
            output_path
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Transcode video error: {e}")
        return False

@app.route('/')
def index():
    db = get_db()
    videos = db.execute('''
        SELECT v.id, v.title, v.description, v.upload_date,
               GROUP_CONCAT(vf.quality_label || ':' || vf.file_path || ':' || vf.codec) AS qualities
        FROM videos v
        LEFT JOIN video_files vf ON v.id = vf.video_id
        GROUP BY v.id
        ORDER BY v.upload_date DESC
    ''').fetchall()

    video_list = []
    for video in videos:
        video_dict = dict(video)
        quality_map = []
        if video_dict['qualities']:
            for q_entry in video_dict['qualities'].split(','):
                parts = q_entry.split(':', 2)
                if len(parts) == 3:
                    label, path, codec = parts
                    quality_map.append({'label': label, 'path': path, 'codec': codec})
        video_dict['qualities'] = quality_map
        video_list.append(video_dict)

    return render_template('index.html', videos=video_list)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        if 'files' not in request.files:
            return redirect(request.url)

        files = request.files.getlist('files')
        quality_labels = request.form.getlist('quality_label[]')

        if not files or all(f.filename == '' for f in files):
            return redirect(request.url)

        db = get_db()
        cursor = db.execute(
            'INSERT INTO videos (title, description, upload_date) VALUES (?, ?, ?)',
            (title, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        video_id = cursor.lastrowid
        db.commit()

        for i, file in enumerate(files):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{video_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                video_codec, audio_codec = get_codec_info(file_path)

                quality_label = quality_labels[i] if i < len(quality_labels) and quality_labels[i] else 'Original'

                db.execute(
                    'INSERT INTO video_files (video_id, quality_label, file_path, codec) VALUES (?, ?, ?, ?)',
                    (video_id, quality_label, unique_filename, f'video: {video_codec}, audio: {audio_codec}')
                )
                db.commit()

        return redirect(url_for('index'))
    return render_template('upload.html')


@app.route('/play/<int:video_id>')
def play_video(video_id):
    db = get_db()
    video = db.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    if video is None:
        return "Video not found", 404

    video_files = db.execute(
        'SELECT quality_label, file_path, codec FROM video_files WHERE video_id = ? ORDER BY quality_label DESC',
        (video_id,)
    ).fetchall()

    qualities = []
    for vf in video_files:
        qualities.append(dict(vf))

    default_file_path = qualities[0]['file_path'] if qualities else None

    default_codec = qualities[0]['codec'] if qualities else 'unknown'

    return render_template('play.html', video=video, qualities=qualities, default_file_path=default_file_path,
                           default_codec=default_codec)


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)