from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
import shutil
import os
from PIL import Image

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Home route (serves HTML)
@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html") as f:
        return f.read()


# Upload + Compress
@app.post("/upload")
def upload_and_compress(
    file: UploadFile = File(...),
    quality: int = Form(50)
):
    upload_path = os.path.join(UPLOAD_DIR, file.filename)

    # Force output as JPG
    filename_no_ext = os.path.splitext(file.filename)[0]
    output_filename = filename_no_ext + ".jpg"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Save original file
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Open image
    img = Image.open(upload_path)

    # Convert if needed
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Clamp quality (safety)
    quality = max(1, min(100, quality))

    # Compress and save
    img.save(output_path, "JPEG", optimize=True, quality=quality)

    # Get sizes
    original_size = os.path.getsize(upload_path)
    compressed_size = os.path.getsize(output_path)

    return {
        "original_filename": file.filename,
        "compressed_filename": output_filename,
        "original_size_kb": round(original_size / 1024, 2),
        "compressed_size_kb": round(compressed_size / 1024, 2),
        "quality_used": quality
    }


# Download route
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=filename
        )

    return {"error": "File not found"}
