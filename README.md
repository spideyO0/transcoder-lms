# ABR Transcoder

## Overview
The ABR Transcoder is a Streamlit application that allows users to transcode audio and video streams to different quality levels. Users can input a file path or a link to a media file, select the desired quality, and play the transcoded stream directly in the application.

## Project Structure
```
abr-transcoder
├── src
│   ├── streamlit_app.py          # Main entry point for the Streamlit application
│   └── flask_server.py   # Contains the Transcoder class for handling transcoding
│
├── requirements.txt     # Lists the dependencies required for the project
└── README.md            # Documentation for the project
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd abr-transcoder
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit application:
   ```
   streamlit run src/streamlit_app.py
   ```

## Usage
- Open the application in your web browser.
- Input a file path or a link to the media file you want to transcode.
- Select the desired quality from the available options.
- Click on the "Transcode" button to start the transcoding process.
- Once transcoding is complete, the transcoded stream will be available for playback.

## Dependencies
- Streamlit
- FFmpeg (or any other libraries required for transcoding)

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.