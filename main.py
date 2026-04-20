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


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/upload")
def upload_and_compress(
    files: list[UploadFile] = File(...),
    quality: int = Form(50),
    mode: str = Form("compress"),
    format: str = Form("jpg")
):
    print("MODE:", mode)

    # ======================
    # 📄 IMAGE → PDF (FIXED)
    # ======================

import img2pdf

if mode == "pdf":
    safe_paths = []

    for file in files:
        upload_path = os.path.join(UPLOAD_DIR, file.filename)

        # Save original
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Open + convert to safe JPEG
        img = Image.open(upload_path).convert("RGB")

        safe_path = upload_path + "_safe.jpg"
        img.save(safe_path, "JPEG")

        safe_paths.append(safe_path)

    output_filename = "combined.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(safe_paths))
    except Exception as e:
        return {"error": str(e)}

    original_size = sum(os.path.getsize(p) for p in safe_paths)
    output_size = os.path.getsize(output_path)

    return {
        "compressed_filename": output_filename,
        "original_size_kb": round(original_size / 1024, 2),
        "output_size_kb": round(output_size / 1024, 2),
        "mode": mode
    }

    # ======================
    # SINGLE FILE MODES
    # ======================
    file = files[0]
    upload_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = Image.open(upload_path)
    filename_no_ext = os.path.splitext(file.filename)[0]

    # ======================
    # 🔄 CONVERT
    # ======================
    if mode == "convert":

        if format == "png":
            output_filename = filename_no_ext + ".png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            img.save(output_path, "PNG")

        else:
            output_filename = filename_no_ext + ".jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(output_path, "JPEG")

    # ======================
    # 🗜️ COMPRESS
    # ======================
    else:
        output_filename = filename_no_ext + ".jpg"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        quality = max(1, min(100, quality))
        img.save(output_path, "JPEG", optimize=True, quality=quality)

    original_size = os.path.getsize(upload_path)
    output_size = os.path.getsize(output_path)

    return {
        "compressed_filename": output_filename,
        "original_size_kb": round(original_size / 1024, 2),
        "output_size_kb": round(output_size / 1024, 2),
        "mode": mode
    }


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
