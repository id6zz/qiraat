from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import subprocess
import acoustid

app = Flask(__name__)
CORS(app)

# Set the directory containing .bin fingerprint files
FINGERPRINT_DIR = "fingerprints"
FP_CALC_PATH = "./fpcalc"  # This must be uploaded and marked as executable

# Converts input audio to a proper WAV format
def convert_to_wav(input_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path, "-ar", "44100", "-ac", "1", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Converts Chromaprint bytes to usable list of ints
def decode_fp(fp_bytes):
    try:
        fp_str = fp_bytes.decode("utf-8")
        return acoustid.decode_fingerprint(fp_str)
    except Exception as e:
        print("Decode error:", e)
        return []

# Uses fpcalc to generate a fingerprint
def fingerprint_audio(path):
    os.environ["CHROMAPRINT_FP_CALC"] = FP_CALC_PATH
    return acoustid.fingerprint_file(path)

# Loads a saved fingerprint .bin and decodes it
def load_fingerprint(file_path):
    with open(file_path, "rb") as f:
        raw = f.read()
    return decode_fp(raw)

# Basic Hamming distance for similarity scoring
def compute_similarity(fp1, fp2):
    min_len = min(len(fp1), len(fp2))
    if min_len == 0:
        return float("inf")
    return sum(a != b for a, b in zip(fp1[:min_len], fp2[:min_len]))

# Home page (serves the frontend)
@app.route("/")
def home():
    return render_template("index.html")

# Endpoint to receive audio + return best match
@app.route("/reverse_search", methods=["POST"])
def reverse_search():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded = request.files["file"]
    raw_path = "temp_input.webm"
    wav_path = "temp_input.wav"
    uploaded.save(raw_path)

    try:
        # Convert and fingerprint input audio
        convert_to_wav(raw_path, wav_path)
        fp_raw, _ = fingerprint_audio(wav_path)
        user_fp = decode_fp(fp_raw)

        best_match = None
        best_score = float("inf")

        # Compare against each saved .bin
        for fname in os.listdir(FINGERPRINT_DIR):
            if fname.endswith(".bin"):
                path = os.path.join(FINGERPRINT_DIR, fname)
                db_fp = load_fingerprint(path)
                score = compute_similarity(user_fp, db_fp)

                if score < best_score:
                    best_score = score
                    best_match = fname

        return jsonify({
            "best_match": best_match or "No match found",
            "distance": best_score
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for f in [raw_path, wav_path]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
