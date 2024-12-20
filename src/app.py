import streamlit as st
from transcoder import Transcoder
import os
import logging

# Configure logging
# logging.basicConfig(level=logging.DEBUG)

def main():
    st.title("ABR Transcoder")
    
    # User input for file upload
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])
    
    if st.button("Transcode") and uploaded_file:
        input_source = os.path.join("./uploads", uploaded_file.name)
        
        # Save uploaded file
        with open(input_source, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        transcoder = Transcoder()
        try:
            output_file = transcoder.transcode(input_source)
            logging.debug(f"Output file: {output_file}")
            if output_file:
                st.success("Transcoding started!")
                st.markdown(f"""
                    <video id="videoPlayer" class="video-js vjs-default-skin" controls preload="auto" width="640" height="264">
                        <source src="{output_file}" type="application/x-mpegURL">
                    </video>
                    <link href="https://vjs.zencdn.net/7.11.4/video-js.css" rel="stylesheet">
                    <script src="https://vjs.zencdn.net/7.11.4/video.js"></script>
                    <script>
                        var player = videojs('videoPlayer');
                        player.play();
                    </script>
                """, unsafe_allow_html=True)
            else:
                st.error("Transcoding failed. Please check the input.")
        except Exception as e:
            logging.error(f"Error during transcoding: {e}")
            st.error("An error occurred during transcoding. Please check the logs.")
    else:
        st.error("Please upload a valid video file.")

if __name__ == "__main__":
    main()