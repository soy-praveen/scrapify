from flask import Flask, render_template, request, send_file, jsonify, url_for
import instaloader
import os
import glob
import shutil
import threading
import time


app = Flask(__name__)
app.config["DEBUG"] = True  # Enable debug mode

# Initialize Instaloader
loader = instaloader.Instaloader()

# Function to delete a file after a delay
def delete_file_after_delay(file_path, delay):
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted {file_path} after {delay} seconds.")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/download', methods=['POST'])
def download():
    try:
        # Ensure the 'url' parameter is received
        url = request.json.get('url')
        if not url:
            return jsonify({"error": "URL parameter is missing"}), 400

        # Extract shortcode from URL
        shortcode = url.split('/')[-2]
        
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
        except Exception as e:
            return jsonify({"error": f"Failed to fetch post: {e}"}), 500

        # Create downloads folder if it doesn't exist
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        # Clear any existing files in the downloads folder
        for filename in os.listdir("downloads"):
            file_path = os.path.join("downloads", filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        # Download video
        loader.download_post(post, target="downloads")

        # Find the downloaded video file
        video_files = glob.glob("downloads/*.mp4")
        if not video_files:
            return jsonify({"error": "Video file not found. Please check the link."}), 404

        video_path = video_files[0]  # Assuming only one video file is downloaded
        video_filename = os.path.basename(video_path)

        # Schedule file deletion after 5 minutes
        threading.Thread(target=delete_file_after_delay, args=(video_path, 300)).start()

        # Provide a URL to download the file
        download_url = url_for('serve_video', filename=video_filename, _external=True)
        return jsonify({"download_url": download_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<filename>')
def serve_video(filename):
    # Serve the file as a downloadable attachment
    return send_file(f'downloads/{filename}', as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
