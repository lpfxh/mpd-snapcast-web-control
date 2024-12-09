from flask import Flask, request, send_file, jsonify, Response, render_template
from mpd import MPDClient, CommandError
from mutagen.id3 import ID3, APIC
from mutagen import MutagenError
import os
import json

app = Flask(__name__)

# MPD服务器连接信息
MPD_HOST = "localhost"
MPD_PORT = 6600

# 音乐目录（与MPD的 music_directory 一致）
MUSIC_DIRECTORY = "/var/lib/mpd/music"  # 请根据实际路径修改

# 默认封面图
DEFAULT_COVER = os.path.join(app.static_folder, "images", "123.jpg")

# 用户名密码（如不需要认证，可注释掉下面代码块）
USERNAME = "admin"
PASSWORD = "password"

# 定时播放信息文件
TIMERS_FILE = os.path.join(os.path.dirname(__file__), 'timers.json')

# 广播流信息文件
BROADCASTS_FILE = os.path.join(os.path.dirname(__file__), 'broadcasts.json')

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        'Authentication required.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

@app.before_request
def require_auth():
    # 如果不需要认证，请注释此函数
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

def get_client():
    client = MPDClient()
    client.timeout = 10
    client.idletimeout = None
    client.connect(MPD_HOST, MPD_PORT)
    return client

def load_broadcasts():
    if os.path.exists(BROADCASTS_FILE):
        with open(BROADCASTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_broadcasts(broadcasts):
    with open(BROADCASTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(broadcasts, f, ensure_ascii=False, indent=2)

@app.route("/")
def index_page():
    return render_template("index.html")

### 播放控制API ###
@app.route("/api/play", methods=["POST"])
def play():
    client = get_client()
    try:
        file = request.form.get("file")
        pos = request.form.get("pos")
        if file:
            # 如果指定文件，则清空列表并播放该文件
            client.clear()
            client.add(file)
            client.play()
        elif pos is not None:
            # 如果给出pos则直接跳到pos播放
            pos = int(pos)
            client.play(pos)
        else:
            client.play()
        return jsonify({"result": "Playing"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/pause", methods=["POST"])
def pause():
    client = get_client()
    try:
        client.pause(1)
        return jsonify({"result": "Paused"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/stop", methods=["POST"])
def stop():
    client = get_client()
    try:
        client.stop()
        return jsonify({"result": "Stopped"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/prev", methods=["POST"])
def prev_track():
    client = get_client()
    try:
        client.previous()
        return jsonify({"result": "Previous track"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/next", methods=["POST"])
def next_track():
    client = get_client()
    try:
        client.next()
        return jsonify({"result": "Next track"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 音量控制 ###
@app.route("/api/volume", methods=["POST"])
def volume():
    client = get_client()
    try:
        level = int(request.form.get("volume", 50))
        if 0 <= level <= 100:
            client.setvol(level)
            return jsonify({"result": f"Volume set to {level}"})
        else:
            return jsonify({"error": "Volume must be between 0 and 100"}), 400
    except (ValueError, CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 循环/随机 ###
@app.route("/api/repeat", methods=["POST"])
def set_repeat():
    client = get_client()
    try:
        mode = request.form.get("mode", "off").lower()
        state = 1 if mode == "on" else 0
        client.repeat(state)
        return jsonify({"result": f"Repeat mode {mode.upper()}"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/random", methods=["POST"])
def set_random():
    client = get_client()
    try:
        mode = request.form.get("mode", "off").lower()
        state = 1 if mode == "on" else 0
        client.random(state)
        return jsonify({"result": f"Random mode {mode.upper()}"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 播放列表 ###
@app.route("/api/playlist", methods=["GET"])
def get_playlist():
    client = get_client()
    try:
        playlist = client.playlistinfo()
        return jsonify(playlist)
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/playlist/add", methods=["POST"])
def add_to_playlist():
    client = get_client()
    try:
        file = request.form.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        client.add(file)
        return jsonify({"result": f"Added {file}"})
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@app.route("/api/playlist/delete", methods=["POST"])
def remove_from_playlist():
    client = get_client()
    try:
        pos = request.form.get("pos")
        if pos is None:
            return jsonify({"error": "No pos provided"}), 400
        pos = int(pos)
        client.delete(pos)
        return jsonify({"result": f"Deleted track at pos {pos}"})
    except (ValueError, CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 音乐库 ###
@app.route("/api/library", methods=["GET"])
def library():
    client = get_client()
    try:
        items = client.listallinfo()
        return jsonify(items)
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 上传音乐文件(支持中文文件名) ###
@app.route("/api/library/upload", methods=["POST"])
def upload_file():
    file = request.files.get('file')
    if file:
        # 不使用secure_filename，直接用原始文件名
        filename = file.filename
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400
        filepath = os.path.join(MUSIC_DIRECTORY, filename)
        try:
            file.save(filepath)
        except Exception as e:
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
        # 更新MPD数据库
        client = get_client()
        try:
            client.update()
        except (CommandError, Exception) as e:
            return jsonify({"error": f"Failed to update MPD database: {str(e)}"}), 500
        finally:
            client.close()
        return jsonify({"result": "ok"})
    return jsonify({"error": "no file uploaded"}), 400

### 删除音乐文件 ###
@app.route("/api/library/delete", methods=["POST"])
def delete_file():
    filename = request.form.get('filename')
    if not filename:
        return jsonify({"error": "no filename provided"}), 400
    filepath = os.path.join(MUSIC_DIRECTORY, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500
        # 更新MPD数据库
        client = get_client()
        try:
            client.update()
        except (CommandError, Exception) as e:
            return jsonify({"error": f"Failed to update MPD database: {str(e)}"}), 500
        finally:
            client.close()
        return jsonify({"result": "ok"})
    else:
        return jsonify({"error": "file not found"}), 400

### 实时播放状态 ###
@app.route("/api/status", methods=["GET"])
def get_status():
    client = get_client()
    try:
        current_song = client.currentsong()
        status = client.status()
        if not current_song:
            current_song = {}
        return jsonify({
            "current_song": current_song,
            "status": status
        })
    except (CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 封面图 ###
@app.route("/api/albumart", methods=["GET"])
def album_art():
    client = get_client()
    try:
        current_song = client.currentsong()
        if current_song and 'file' in current_song:
            song_file = current_song['file']
            mp3_path = os.path.join(MUSIC_DIRECTORY, song_file)
            if os.path.isfile(mp3_path):
                try:
                    audio = ID3(mp3_path)
                    for tag in audio.values():
                        if isinstance(tag, APIC):
                            image_data = tag.data
                            mime = tag.mime if hasattr(tag, 'mime') else "image/jpeg"
                            return Response(image_data, mimetype=mime)
                except (MutagenError, Exception):
                    pass
        return send_file(DEFAULT_COVER, mimetype="image/jpeg")
    except (CommandError, Exception) as e:
        return send_file(DEFAULT_COVER, mimetype="image/jpeg")
    finally:
        client.close()

### 跳转进度 ###
@app.route("/api/seek", methods=["POST"])
def seek():
    client = get_client()
    try:
        sec = int(request.form.get("time", 0))
        client.seekcur(sec)
        return jsonify({"result": "seeked"})
    except (ValueError, CommandError, Exception) as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

### 定时播放信息管理 ###
@app.route("/api/timers/save", methods=["POST"])
def save_timers():
    timers = request.json.get('timers')
    if not timers:
        return jsonify({"error": "No timers provided"}), 400
    try:
        with open(TIMERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(timers, f, ensure_ascii=False)
        return jsonify({"result": "Timers saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/timers/get", methods=["GET"])
def get_timers():
    try:
        if not os.path.exists(TIMERS_FILE):
            return jsonify({"timers": []})
        with open(TIMERS_FILE, 'r', encoding='utf-8') as f:
            timers = json.load(f)
        return jsonify({"timers": timers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/timers/delete", methods=["POST"])
def delete_timers():
    try:
        if os.path.exists(TIMERS_FILE):
            os.remove(TIMERS_FILE)
        return jsonify({"result": "Timers deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

### 广播流管理 ###
@app.route("/api/broadcasts", methods=["GET"])
def get_broadcasts():
    try:
        broadcasts = load_broadcasts()
        return jsonify(broadcasts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/broadcasts/add", methods=["POST"])
def add_broadcast():
    name = request.form.get("name")
    url = request.form.get("url")
    if not name or not url:
        return jsonify({"error": "Name and URL required"}), 400
    broadcasts = load_broadcasts()
    for b in broadcasts:
        if b['url'] == url:
            return jsonify({"error": "Broadcast URL already exists"}), 400
    broadcasts.append({"name": name, "url": url})
    try:
        save_broadcasts(broadcasts)
        return jsonify({"result": "Broadcast added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/broadcasts/delete", methods=["POST"])
def delete_broadcast():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    broadcasts = load_broadcasts()
    new_list = [b for b in broadcasts if b['url'] != url]
    if len(new_list) == len(broadcasts):
        return jsonify({"error": "Broadcast not found"}), 404
    try:
        save_broadcasts(new_list)
        return jsonify({"result": "Broadcast deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not os.path.exists(DEFAULT_COVER):
        raise FileNotFoundError(f"Default cover image not found at {DEFAULT_COVER}")
    app.run(host="0.0.0.0", port=5000, debug=True)