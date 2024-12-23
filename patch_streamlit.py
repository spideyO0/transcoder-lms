# patch_streamlit.py

import os
import shutil
import sys

def patch_streamlit():
    # Locate the streamlit package path
    streamlit_path = os.path.dirname(__import__('streamlit').__file__)
    server_file_path = os.path.join(streamlit_path, 'web', 'server', 'server.py')
    custom_server_file_path = os.path.join(os.path.dirname(__file__), 'src', 'server.py')
    patch_marker_file = os.path.join(os.path.dirname(__file__), 'patch_applied.marker')

    # Check if the patch has already been applied
    if os.path.exists(patch_marker_file):
        print("Patch has already been applied. Skipping.")
        return

    # Check if the custom server file exists
    if os.path.exists(custom_server_file_path):
        # Replace the existing server.py with the custom server.py
        shutil.copyfile(custom_server_file_path, server_file_path)
        print(f"Replaced {server_file_path} with {custom_server_file_path}")

        # Create a marker file to indicate that the patch has been applied
        with open(patch_marker_file, 'w') as f:
            f.write("Patch applied")

        # Kill the Streamlit server
        print("Patch applied successfully. Killing the Streamlit server.")
        os._exit(0)
    else:
        print(f"Custom server file not found: {custom_server_file_path}")

if __name__ == "__main__":
    patch_streamlit()
