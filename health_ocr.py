import os
import shutil
import subprocess
import tempfile
import csv
import io

from PIL import Image, ImageOps
import win32con
import win32gui
import win32ui


def find_tesseract():
    executable = shutil.which("tesseract")
    if executable:
        return executable

    for program_files in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if program_files:
            candidate = os.path.join(program_files, "Tesseract-OCR", "tesseract.exe")
            if os.path.isfile(candidate):
                return candidate

    raise FileNotFoundError(
        "Tesseract OCR was not found. Install Tesseract OCR or add it to PATH."
    )


def read_health_percent(region):
    left, top, right, bottom = region
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0:
        raise ValueError("The selected health region has invalid dimensions.")

    screen_handle = win32gui.GetDC(0)
    screen_dc = win32ui.CreateDCFromHandle(screen_handle)
    memory_dc = screen_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    old_bitmap = None

    try:
        bitmap.CreateCompatibleBitmap(screen_dc, width, height)
        old_bitmap = memory_dc.SelectObject(bitmap)
        memory_dc.BitBlt((0, 0), (width, height), screen_dc, (left, top), win32con.SRCCOPY)

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, "health.bmp")
            bitmap.SaveBitmapFile(memory_dc, image_path)
            with Image.open(image_path) as image:
                return recognize_health_percent(image)
    finally:
        if old_bitmap is not None:
            memory_dc.SelectObject(old_bitmap)
        win32gui.DeleteObject(bitmap.GetHandle())
        memory_dc.DeleteDC()
        screen_dc.DeleteDC()
        win32gui.ReleaseDC(0, screen_handle)


def recognize_health_percent(image):
    with tempfile.TemporaryDirectory() as temp_dir:
        scaled = image.convert("RGB").resize(
            (image.width * 2, image.height * 2),
            Image.Resampling.LANCZOS
        )
        gray = ImageOps.grayscale(scaled)
        variants = (
            image.convert("RGB"),
            gray.convert("RGB"),
            gray.point(lambda pixel: 255 if pixel >= 180 else 0).convert("RGB"),
        )
        composite = Image.new(
            "RGB",
            (max(variant.width for variant in variants),
             sum(variant.height for variant in variants) + 8 * (len(variants) - 1)),
            "white",
        )
        top = 0
        for variant in variants:
            composite.paste(variant, (0, top))
            top += variant.height + 8

        image_path = os.path.join(temp_dir, "health_variants.png")
        composite.save(image_path)
        executable = find_tesseract()
        try:
            result = subprocess.run(
                [
                    executable,
                    image_path,
                    "stdout",
                    "--psm",
                    "6",
                    "-c",
                    "tessedit_char_whitelist=0123456789%",
                    "tsv",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            detail = error.stderr.strip() or str(error)
            raise RuntimeError(f"Tesseract OCR failed: {detail}") from error
        readings = parse_tesseract_results(result.stdout)

    if not readings:
        return None
    scores = {}
    for percent, confidence in readings:
        if percent not in scores:
            scores[percent] = [1, confidence, confidence]
        else:
            scores[percent][0] += 1
            scores[percent][1] = max(scores[percent][1], confidence)
            scores[percent][2] += confidence
    return max(
        scores,
        key=lambda percent: (
            scores[percent][1],
            scores[percent][0],
            scores[percent][2],
        ),
    )


def parse_health_percent(text):
    digits = "".join(character for character in text if character.isdigit())
    if not digits:
        return None

    percent = int(digits)
    return percent if 0 <= percent <= 100 else None


def parse_tesseract_results(tsv_output):
    lines = {}
    for row in csv.DictReader(io.StringIO(tsv_output), delimiter="\t"):
        text = row.get("text", "").strip()
        if not text:
            continue
        line_key = (row["block_num"], row["par_num"], row["line_num"])
        confidence = float(row["conf"])
        lines.setdefault(line_key, []).append((int(row["word_num"]), text, confidence))

    readings = []
    for words in lines.values():
        words.sort()
        percent = parse_health_percent("".join(word[1] for word in words))
        if percent is not None:
            confidence = sum(word[2] for word in words) / len(words)
            readings.append((percent, confidence))
    return readings


def phase_for_percent(percent):
    if not 0 <= percent <= 100:
        raise ValueError("Health percentage must be between 0 and 100.")
    if percent >= 90:
        return 1, 270
    if percent >= 75:
        return 2, 90
    if percent >= 45:
        return 3, 180
    if percent >= 30:
        return 4, 90
    return 5, 270
