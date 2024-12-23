# patch_streamlit.py

import os
import shutil

def patch_streamlit():
    # Locate the streamlit package path
    streamlit_path = os.path.dirname(__import__('streamlit').__file__)
    server_file_path = os.path.join(streamlit_path, 'web', 'server', 'server.py')
    custom_server_file_path = os.path.join(os.path.dirname(__file__), 'src', 'server.py')

    # Check if the custom server file exists
    if os.path.exists(custom_server_file_path):
        # Replace the existing server.py with the custom server.py
        shutil.copyfile(custom_server_file_path, server_file_path)
        print(f"Replaced {server_file_path} with {custom_server_file_path}")
    else:
        print(f"Custom server file not found: {custom_server_file_path}")

if __name__ == "__main__":
    patch_streamlit()
