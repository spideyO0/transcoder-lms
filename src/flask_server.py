# from flask import Flask, request, send_from_directory, jsonify
# from flask_cors import CORS
# import os
# import subprocess
# import logging

# app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes

# UPLOAD_FOLDER = './uploads'
# OUTPUT_FOLDER = './output'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# logging.basicConfig(level=logging.DEBUG)

# @app.route('/transcode', methods=['POST'])
# def transcode():
#     file = request.files['file']
#     input_source = os.path.join(UPLOAD_FOLDER, file.filename)
#     file.save(input_source)
    
#     base_name = os.path.splitext(file.filename)[0]
#     master_playlist = os.path.join(OUTPUT_FOLDER, f"{base_name}_master.m3u8")
    
#     try:
#         # Transcoding logic using ffmpeg to generate HLS for multiple qualities
#         qualities = {
#             "240p": {"resolution": "426x240", "bitrate": "300k"},
#             "360p": {"resolution": "640x360", "bitrate": "500k"},
#             "480p": {"resolution": "854x480", "bitrate": "700k"},
#             "720p": {"resolution": "1280x720", "bitrate": "1500k"},
#             "1080p": {"resolution": "1920x1080", "bitrate": "3000k"}
#         }
#         ffmpeg_commands = []
#         for quality, params in qualities.items():
#             output_file = os.path.join(OUTPUT_FOLDER, f"{base_name}_{quality}.m3u8")
#             ffmpeg_command = [
#                 "ffmpeg",
#                 "-i", input_source,
#                 "-vf", f"scale={params['resolution']}",
#                 "-c:v", "libx264",
#                 "-b:v", params["bitrate"],
#                 "-preset", "veryfast",
#                 "-g", "48",
#                 "-hls_time", "4",
#                 "-hls_playlist_type", "event",
#                 "-hls_flags", "delete_segments",
#                 "-hls_segment_filename", os.path.join(OUTPUT_FOLDER, f"{base_name}_{quality}_%03d.ts"),
#                 output_file
#             ]
#             ffmpeg_commands.append(ffmpeg_command)
        
#         # Run ffmpeg commands in parallel
#         processes = [subprocess.Popen(cmd) for cmd in ffmpeg_commands]
#         for p in processes:
#             p.wait()
        
#         # Create master playlist
#         with open(master_playlist, 'w') as f:
#             f.write("#EXTM3U\n")
#             for quality, params in qualities.items():
#                 f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={params['bitrate']},RESOLUTION={params['resolution']}\n")
#                 f.write(f"{base_name}_{quality}.m3u8\n")
        
#         return f"http://localhost:5000/stream/{base_name}_master.m3u8"
#     except subprocess.CalledProcessError as e:
#         logging.error(f"Transcoding failed: {e}")
#         return jsonify({"error": "Transcoding failed"}), 500

# @app.route('/stream/<path:filename>')
# def stream(filename):
#     return send_from_directory(OUTPUT_FOLDER, filename)

# @app.route('/files', methods=['GET'])
# def list_files():
#     files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
#     return jsonify(files)

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000)