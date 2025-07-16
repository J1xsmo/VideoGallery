# VideoGallery platform 

This is a simple video hosting application built with Python and Flask. It allows users to upload video files, which are then stored and can be played back through a custom HTML5 video player. The application supports uploading multiple video files for a single video entry, allowing for different quality options (e.g., 1080p, 720p). <br>
*Note: Сode may still contain some bugs - report or suggest improvements if you find something!*
## Features

* **Video Upload:** Upload new videos with a title, description, and one or more video files.
  - Supported formats: MP4, MOV, AVI, MKV, WEBM
  - Note: HEVC/H.265 playback may not be supported in all browsers by default (e.g. Edge).  
    If you know solution to make it play at all browser by defualt please say it.

* **Multiple Qualities:** Associate multiple quality versions (e.g., different resolutions) with a single video.
* **Codec Detection:** Automatically detects video and audio codecs using `ffprobe`.
* **Custom Video Player:** A clean, custom-styled HTML5 player with play/pause, quality switching, and fullscreen controls.
* **Responsive Design:** User interface built with Tailwind CSS for a modern, mobile-friendly experience.
* **Database Integration:** Uses SQLite to store video metadata and file paths.

## Requirements

To run this project, you need to have the following installed:

* Python 3.x
* FFmpeg and FFprobe (must be accessible in your system's PATH)
* `pip` for installing Python packages

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/J1xsmo/VideoGallery/tree/master
    cd video-hosting-platform
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: A `requirements.txt` file is still being finalized. In the meantime, required packages include `Flask`, `sqlite3`, `werkzeug`, and `datetime`. You can create this file manually or install them one by one.*

3.  **Install FFmpeg and FFprobe:**
    Download and install FFmpeg from the official website. Ensure that the `ffmpeg` and `ffprobe` executables are added to your system's PATH.

4.  **Run the application:**
    ```bash
    python main.py
    ```

The server will start, and you can access the application at `http://127.0.0.1:5000`.

## Project Structure

* `main.py`: The main Flask application file. It handles all routes, database interactions, and video processing.
* `static/`: Contains static files like CSS and uploads.
    * `static/uploads/`: Directory where uploaded video files are stored.
* `templates/`: Contains HTML files for the web pages.
    * `base.html`: The base template used for all pages.
    * `index.html`: The home page that lists all uploaded videos.
    * `upload.html`: The page with the video upload form.
    * `play.html`: The video playback page with the custom player.
* `schema.sql`
* `style.css`
