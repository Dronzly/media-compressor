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
    quality: int = Form(50),
    mode: str = Form("compress"),
    format: str = Form("jpg")
):
    upload_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save original file
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = Image.open(upload_path)
    print("MODE RECEIVED:", mode)
    print("FORMAT RECEIVED:", format)

    filename_no_ext = os.path.splitext(file.filename)[0]

    # ======================
    # 🔄 CONVERT MODE
    # ======================
    if mode == "convert":

        if format == "png":
            output_filename = filename_no_ext + ".png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            img.save(output_path, "PNG")

        elif format == "jpg":
            output_filename = filename_no_ext + ".jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG")


    # ======================
    # 🗜️ COMPRESS MODE
    # ======================
    else:
        output_filename = filename_no_ext + ".jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        quality = max(1, min(100, quality))

        img.save(output_path, "JPEG", optimize=True, quality=quality)

    # File sizes
    original_size = os.path.getsize(upload_path)
    compressed_size = os.path.getsize(output_path)

    return {

        "original_filename": file.filename,
        "compressed_filename": output_filename,
        "original_size_kb": round(original_size / 1024, 2),
        "compressed_size_kb": round(compressed_size / 1024, 2),
        "mode": mode
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

