import streamlit as st
import os
import subprocess
import sys  # Add this import statement
from pathlib import Path
from streamlit.components.v1 import html
from flask import Flask, send_from_directory, request, jsonify, Response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from threading import Thread
import urllib.parse
from waitress import serve
import ffmpeg
import logging
import platform
import requests
import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httputil
from streamlit.web.server.server import Server
from streamlit.runtime import get_instance
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Run the patch script to modify Streamlit server.py
# def run_patch_script():
#     patch_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'patch_streamlit.py')
#     marker_file = os.path.join(os.path.dirname(__file__), 'patch_applied.marker')
#     if not os.path.exists(marker_file):
#         try:
#             subprocess.check_call([sys.executable, patch_script_path])
#             with open(marker_file, 'w') as f:
#                 f.write('Patch applied')
#             st.info("Patch applied successfully. Killing the Streamlit server.")
#             os._exit(0)
#         except subprocess.CalledProcessError as e:
#             st.error(f"Error occurred while running the patch script: {e}")
#             sys.exit(1)
#         except Exception as e:
#             st.error(f"Unexpected error: {e}")
#             sys.exit(1)
#     else:
#         st.info("Patch already applied. Skipping patching process.")

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
    try:
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
    except Exception as e:
        st.error(f"Error installing ffmpeg: {e}")
        sys.exit(1)

# Function to check if the Flask server is running
def check_flask_server():
    try:
        response = requests.get(get_flask_url())
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except Exception as e:
        st.error(f"Unexpected error checking Flask server: {e}")
        return False

# Function to start the Flask server if not running
def ensure_flask_server_running():
    try:
        if not check_flask_server():
            st.info("Starting Flask server...")
            flask_thread = Thread(target=run_flask)
            flask_thread.daemon = True
            flask_thread.start()
            st.session_state['flask_thread'] = flask_thread
            st.success("Flask server started successfully.")
        else:
            st.success("Flask server is already running.")
    except Exception as e:
        st.error(f"Unexpected error starting Flask server: {e}")

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
    except Exception as e:
        st.error(f"Unexpected error during transcoding: {e}")
        return None

# Function to get the base URL from Streamlit secrets
def get_base_url():
    try:
        return st.secrets.get("base_url", "http://localhost:8501")
    except Exception as e:
        st.error(f"Unexpected error getting base URL: {e}")
        return "http://localhost:8501"

# Function to get the Flask server URL from Streamlit secrets
def get_flask_url():
    try:
        return st.secrets.get("flask_url", "http://localhost:8502")
    except Exception as e:
        st.error(f"Unexpected error getting Flask URL: {e}")
        return "http://localhost:8502"

# Generate stream URL for a file
def generate_stream_url(file_path):
    try:
        base_url = get_base_url()
        encoded_path = urllib.parse.quote(file_path)
        return f"{base_url}/proxy/stream/{encoded_path}"
    except Exception as e:
        st.error(f"Unexpected error generating stream URL: {e}")
        return ""

# Serve HLS files using Flask app 
flask_app = Flask(__name__)
flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app)
CORS(flask_app)

@flask_app.route('/stream/<path:filename>')
def stream(filename):
    logging.info(f"Serving file: {filename}")
    try:
        return send_from_directory(OUTPUT_FOLDER, filename)
    except Exception as e:
        logging.error(f"Error serving file {filename}: {str(e)}")
        return Response("File not found.", status=404)

@flask_app.route('/transcode', methods=['POST'])
def transcode():
    try:
        file = request.files['file']
        input_source = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_source)
        
        base_name = os.path.splitext(file.filename)[0]
        master_playlist = transcode_to_hls(input_source, base_name)
        
        if master_playlist:
            return jsonify({"url": generate_stream_url(f"{base_name}_master.m3u8")})
        else:
            return jsonify({"error": "Transcoding failed"}), 500
    except Exception as e:
        logging.error(f"Error during transcoding: {str(e)}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@flask_app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    try:
        flask_url = get_flask_url()
        target_url = f"{flask_url}/{path}"
        
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args)
        elif request.method == 'POST':
            response = requests.post(target_url, data=request.form, files=request.files)
        elif request.method == 'PUT':
            response = requests.put(target_url, data=request.form)
        elif request.method == 'DELETE':
            response = requests.delete(target_url)
        else:
            return Response("Method not allowed", status=405)
        
        return Response(response.content, status=response.status_code, headers=dict(response.headers))
    except Exception as e:
        logging.error(f"Error during proxying: {str(e)}")
        return Response("Unexpected error occurred", status=500)

@flask_app.route('/check_flask_access')
def check_flask_access():
    try:
        return send_from_directory('.', 'check_flask_access.html')
    except Exception as e:
        logging.error(f"Error serving check_flask_access.html: {str(e)}")
        return Response("File not found.", status=404)

def run_flask():
    try:
        serve(flask_app, host='127.0.0.1', port=8502)
    except OSError as e:
        if "Address already in use" in str(e):
            logging.info("Port 8502 is already in use. Using the existing server.")
        else:
            raise
    except Exception as e:
        logging.error(f"Unexpected error while running Flask server: {str(e)}")
        sys.exit(1)

# Function to check if the stream URL is accessible
def check_stream_url(stream_url):
    try:
        response = requests.get(stream_url, stream=True)
        if response.status_code == 200:
            st.success("Stream URL is accessible.")
        else:
            st.error(f"Stream URL is not accessible. Status code: {response.status_code}")
    except requests.ConnectionError:
        st.error("Failed to connect to the stream URL. Please check the Flask server and proxy configuration.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

# Tornado reverse proxy handler is now handled in server.py, so remove it from here

def configure_tornado():
    try:
        runtime = get_instance()
        app = runtime._get_tornado_app()
        if app:
            # No need to add handlers here as it's already done in server.py
            pass
        else:
            raise RuntimeError("Could not get the Streamlit server instance.")
    except Exception as e:
        st.error(f"Unexpected error during Tornado configuration: {e}")
        sys.exit(1)

def main():
    try:
        # Run the patch script to modify Streamlit server.py
        # run_patch_script()

        st.title("Streamlit Media Server")

        # Start Flask app in a separate thread
        if 'flask_thread' not in st.session_state:
            ensure_flask_server_running()

        # No need to configure Tornado reverse proxy here

        # Reverse proxy for Flask server requests (for streaming)
        
        query_params = st.query_params
        
        if "stream" in query_params:
            stream_path = query_params["stream"][0]
            
            # Forward request to Flask server and get response.
            
            logging.info(f"Proxying request to Flask server for stream: {stream_path}")
            
            flask_url = get_flask_url()
            response = requests.get(f"{flask_url}/stream/{stream_path}", stream=True)
            
            if response.status_code == 200:
                st.write("Streaming video...")
                st.video(response.url)
            else:
                st.error(f"Failed to fetch stream: {response.status_code} - {response.text}")
                logging.error(f"Error fetching stream: {response.status_code} - {response.text}")

        # Upload video file 
        uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])
        
        if uploaded_file:
            try:
                input_source = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
                
                with open(input_source, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                base_name = os.path.splitext(uploaded_file.name)[0]
                
                st.info(f"Uploaded file: {uploaded_file.name}")

                # Transcode video 
                if st.button("Start Transcoding"):
                    try:
                        st.info("Transcoding in progress...")
                        
                        flask_url = get_flask_url()
                        response = requests.post(f"{flask_url}/transcode", files={"file": open(input_source, "rb")})
                        
                        if response.status_code == 200:
                            data = response.json()
                            master_playlist_url = data["url"]
                            
                            st.success("Transcoding completed!")

                            # Generate and display streamable URL 
                            st.write(f"Stream URL: [Stream Video]({master_playlist_url})")
                            st.markdown(f"Use this URL to play the video in any HLS-compatible player:\n\n`{master_playlist_url}`")

                            # Check if the stream URL is accessible
                            check_stream_url(master_playlist_url)

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
                        else:
                            st.error("Transcoding failed.")
                    except Exception as e:
                        st.error(f"Transcoding failed: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error uploading file: {e}")

        # Display list of previously transcoded files 
        st.header("Previously Transcoded Files")
        
        try:
            transcoded_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith("_master.m3u8")]
            
            if transcoded_files:
                selected_file = st.selectbox("Select a file to play", transcoded_files)
                
                if st.button("Play Selected File"):
                    selected_file_path = os.path.join(OUTPUT_FOLDER, selected_file)
                    stream_url = generate_stream_url(selected_file)

                    st.write(f"Stream URL: [Stream Video]({stream_url})")
                    st.markdown(f"Use this URL to play the video in any HLS-compatible player:\n\n`{stream_url}`")

                    # Check if the stream URL is accessible
                    check_stream_url(stream_url)

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
        except Exception as e:
            st.error(f"Unexpected error displaying transcoded files: {e}")

    except Exception as e:
        st.error(f"Unexpected error in main: {e}")

if __name__ == "__main__":
    main()

