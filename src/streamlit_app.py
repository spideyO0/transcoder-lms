import streamlit as st
import os
import subprocess
from pathlib import Path
from streamlit.components.v1 import html
from flask import Flask, send_from_directory
from flask_cors import CORS
from threading import Thread
import urllib.parse
from waitress import serve
import ffmpeg
import logging
import platform
import requests
import socket

# Define folders for uploads and output
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to check if ffmpeg is installed
def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

# Function to install ffmpeg
def install_ffmpeg():
    os_info = platform.system().lower()
    if os_info == "linux":
        # Download and install ffmpeg for Linux from GitHub
        ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz"
        subprocess.run(["curl", "-L", ffmpeg_url, "-o", "ffmpeg.tar.xz"], check=True)
        subprocess.run(["tar", "-xvf", "ffmpeg.tar.xz"], check=True)
        ffmpeg_dir = next(d for d in os.listdir() if d.startswith("ffmpeg-"))
        ffmpeg_bin = os.path.join(ffmpeg_dir, "ffmpeg")
        os.environ["PATH"] += os.pathsep + os.path.abspath(ffmpeg_dir)
    elif os_info == "darwin":
        # Download and install ffmpeg for macOS
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
    elif os_info == "windows":
        # Download and install ffmpeg for Windows
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        subprocess.run(["curl", "-L", ffmpeg_url, "-o", "ffmpeg.zip"], check=True)
        subprocess.run(["tar", "-xvf", "ffmpeg.zip"], check=True)
        ffmpeg_bin = os.path.abspath("ffmpeg/bin")
        os.environ["PATH"] += os.pathsep + ffmpeg_bin
    else:
        raise OSError("Unsupported operating system")

# Function to transcode video to HLS with multiple qualities
def transcode_to_hls(input_source, base_name):
    if not check_ffmpeg_installed():
        st.info("ffmpeg is not installed. Installing ffmpeg...")
        install_ffmpeg()
        st.success("ffmpeg installed successfully.")

    qualities = {
        "240p": {"resolution": "426x240", "bitrate": "300k"},
        "360p": {"resolution": "640x360", "bitrate": "500k"},
        "480p": {"resolution": "854x480", "bitrate": "700k"},
        "720p": {"resolution": "1280x720", "bitrate": "1500k"},
        "1080p": {"resolution": "1920x1080", "bitrate": "3000k"},
    }
    master_playlist = os.path.join(OUTPUT_FOLDER, f"{base_name}_master.m3u8")

    try:
        for quality, params in qualities.items():
            output_file = os.path.join(OUTPUT_FOLDER, f"{base_name}_{quality}.m3u8")
            process = (
                ffmpeg
                .input(input_source)
                .output(
                    output_file,
                    vf=f"scale={params['resolution']}",
                    vcodec="libx264",
                    b=params["bitrate"],
                    preset="veryfast",
                    g=48,
                    hls_time=4,
                    hls_playlist_type="event",
                    hls_flags="delete_segments",
                    hls_segment_filename=os.path.join(OUTPUT_FOLDER, f"{base_name}_{quality}_%03d.ts")
                )
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise ffmpeg.Error('ffmpeg', stdout, stderr)

        # Create master playlist
        with open(master_playlist, 'w') as f:
            f.write("#EXTM3U\n")
            for quality, params in qualities.items():
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={params['bitrate']},RESOLUTION={params['resolution']}\n")
                f.write(f"{base_name}_{quality}.m3u8\n")

        return master_playlist

    except ffmpeg.Error as e:
        st.error(f"An error occurred during transcoding: {e.stderr.decode() if e.stderr else str(e)}")
        return None

# Function to get the local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = 'localhost'
    finally:
        s.close()
    return ip

# Generate stream URL for a file
def generate_stream_url(file_path):
    local_ip = get_local_ip()
    base_url = f"http://{local_ip}:8502"
    encoded_path = urllib.parse.quote(file_path)
    return f"{base_url}/stream/{encoded_path}"

# Serve HLS files
@st.cache_data
def serve_file(file_path):
    with open(file_path, 'rb') as f:
        return f.read()

# Flask app to serve HLS files
flask_app = Flask(__name__)
CORS(flask_app)  # Enable CORS for all routes

@flask_app.route('/stream/<path:filename>')
def stream(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

def run_flask():
    try:
        serve(flask_app, host='0.0.0.0', port=8502)
    except OSError as e:
        if "Address already in use" in str(e):
            logging.info("Port 8502 is already in use. Using the existing server.")
        else:
            raise

# Streamlit app
def main():
    st.title("Streamlit Media Server")

    # Start Flask app in a separate thread
    if 'flask_thread' not in st.session_state:
        flask_thread = Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        st.session_state['flask_thread'] = flask_thread

    # Button to show the operating system
    if st.button("Show Operating System"):
        os_info = platform.system() + " " + platform.release()
        st.info(f"Operating System: {os_info}")

    # Upload video file
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])
    
    if uploaded_file:
        input_source = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        with open(input_source, "wb") as f:
            f.write(uploaded_file.getbuffer())

        base_name = os.path.splitext(uploaded_file.name)[0]
        st.info(f"Uploaded file: {uploaded_file.name}")

        # Transcode video
        if st.button("Start Transcoding"):
            try:
                st.info("Transcoding in progress...")
                master_playlist = transcode_to_hls(input_source, base_name)
                if master_playlist:
                    st.success("Transcoding completed!")

                    # Generate and display streamable URL
                    master_playlist_url = generate_stream_url(f"{base_name}_master.m3u8")
                    st.write(f"Stream URL: [Stream Video]({master_playlist_url})")
                    st.markdown(f"Use this URL to play the video in any HLS-compatible player:\n\n`{master_playlist_url}`")

                    # Embed Video.js player
                    my_html = f"""
                        <link href="https://vjs.zencdn.net/7.11.4/video-js.css" rel="stylesheet" />
                        <script src="https://vjs.zencdn.net/7.11.4/video.min.js"></script>
                        <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@2.0.9/dist/videojs-contrib-quality-levels.min.js"></script>
                        <script src="https://cdn.jsdelivr.net/npm/videojs-http-source-selector@1.1.6/dist/videojs-http-source-selector.min.js"></script>
                        <video-js id="videoPlayer" class="vjs-default-skin" controls preload="auto" width="640" height="360">
                            <source src="{master_playlist_url}" type="application/x-mpegURL">
                        </video-js>
                        <script>
                            var player = videojs('videoPlayer');
                            player.qualityLevels();
                            player.httpSourceSelector();
                            player.play();
                        </script>
                    """
                    html(my_html)
            except ffmpeg.Error as e:
                error_message = e.stderr.decode() if e.stderr else str(e)
                st.error(f"Transcoding failed: {error_message}")

    # Display list of previously transcoded files
    st.header("Previously Transcoded Files")
    transcoded_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith("_master.m3u8")]
    if transcoded_files:
        selected_file = st.selectbox("Select a file to play", transcoded_files)
        if st.button("Play Selected File"):
            selected_file_path = os.path.join(OUTPUT_FOLDER, selected_file)
            stream_url = generate_stream_url(selected_file)

            st.write(f"Stream URL: [Stream Video]({stream_url})")
            st.markdown(f"Use this URL to play the video in any HLS-compatible player:\n\n`{stream_url}`")

            my_html = f"""
                <link href="https://vjs.zencdn.net/7.11.4/video-js.css" rel="stylesheet" />
                <script src="https://vjs.zencdn.net/7.11.4/video.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@2.0.9/dist/videojs-contrib-quality-levels.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/videojs-http-source-selector@1.1.6/dist/videojs-http-source-selector.min.js"></script>
                <video-js id="videoPlayer" class="vjs-default-skin" controls preload="auto" width="640" height="360">
                    <source src="{stream_url}" type="application/x-mpegURL">
                </video-js>
                <script>
                    var player = videojs('videoPlayer');
                    player.qualityLevels();
                    player.httpSourceSelector();
                    player.play();
                </script>
            """
            html(my_html)
    else:
        st.info("No transcoded files available.")

if __name__ == "__main__":
    main()
