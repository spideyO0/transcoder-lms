import os
import logging
import subprocess

class Transcoder:
    def __init__(self):
        pass

    def transcode(self, input_source):
        output_dir = "./output"
        base_name = os.path.splitext(os.path.basename(input_source))[0]
        master_playlist = os.path.join(output_dir, f"{base_name}_master.m3u8")
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Transcoding logic using ffmpeg to generate HLS for multiple qualities
            qualities = {
                "Low": "24",
                "Medium": "18",
                "High": "12"
            }
            ffmpeg_commands = []
            for quality, crf in qualities.items():
                output_file = os.path.join(output_dir, f"{base_name}_{quality}.m3u8")
                ffmpeg_command = [
                    "ffmpeg",
                    "-i", input_source,
                    "-c:v", "libx264",
                    "-crf", crf,
                    "-preset", "fast",
                    "-g", "48",
                    "-hls_time", "4",
                    "-hls_playlist_type", "event",
                    "-hls_flags", "delete_segments",
                    "-hls_segment_filename", os.path.join(output_dir, f"{base_name}_{quality}_%03d.ts"),
                    output_file
                ]
                ffmpeg_commands.append(ffmpeg_command)
            
            # Run ffmpeg commands in parallel
            processes = [subprocess.Popen(cmd) for cmd in ffmpeg_commands]
            for p in processes:
                p.wait()
            
            # Create master playlist
            with open(master_playlist, 'w') as f:
                f.write("#EXTM3U\n")
                for quality in qualities.keys():
                    f.write(f"#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360\n")
                    f.write(f"{base_name}_{quality}.m3u8\n")
            
            return master_playlist
        except subprocess.CalledProcessError as e:
            logging.error(f"Transcoding failed: {e}")
            return None

    def validate_input(self, input_path):
        # Implement input validation logic here
        return True if input_path else False

    def get_supported_formats(self):
        # Return a list of supported formats
        return ['mp4', 'mkv', 'webm']