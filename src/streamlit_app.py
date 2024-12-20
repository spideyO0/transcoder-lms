import streamlit as st
import requests
import os
import urllib.parse
from streamlit.components.v1 import html

def main():
    st.title("Personal Media Server")

    # User input for file upload
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])

    if st.button("Upload and Transcode") and uploaded_file:
        input_source = os.path.join("./uploads", uploaded_file.name)
        
        # Save uploaded file
        with open(input_source, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Send file to Flask server for transcoding
        files = {'file': open(input_source, 'rb')}
        response = requests.post("http://localhost:5000/transcode", files=files)
        
        if response.status_code == 200:
            st.success("Transcoding started!")
            stream_url = response.text.strip()
            encoded_stream_url = urllib.parse.quote(stream_url, safe=':/')
            my_html = f"""
                <link href="https://vjs.zencdn.net/7.11.4/video-js.css" rel="stylesheet" />
                <script src="https://vjs.zencdn.net/7.11.4/video.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@2.0.9/dist/videojs-contrib-quality-levels.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/videojs-http-source-selector@1.1.6/dist/videojs-http-source-selector.min.js"></script>
                <video-js id="videoPlayer" class="vjs-default-skin" controls preload="auto" width="640" height="360">
                    <source src="{encoded_stream_url}" type="application/x-mpegURL">
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
            st.error("Transcoding failed. Please check the server logs.")

    st.header("Previously Uploaded Files")
    response = requests.get("http://localhost:5000/files")
    if response.status_code == 200:
        files = response.json()
        selected_file = st.selectbox("Select a file to play", files)
        if st.button("Play Selected File"):
            base_name = os.path.splitext(selected_file)[0]
            encoded_base_name = urllib.parse.quote(base_name)
            stream_url = f"http://localhost:5000/stream/{encoded_base_name}_master.m3u8"
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
        st.error("Failed to retrieve files. Please check the server logs.")

if __name__ == "__main__":
    main()