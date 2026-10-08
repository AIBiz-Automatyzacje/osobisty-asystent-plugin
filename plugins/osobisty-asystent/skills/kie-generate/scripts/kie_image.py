#!/usr/bin/env python3
"""
Kie.ai Image Generator - Nano Banana 2 / Nano Banana Pro

Usage:
    # Generate (text → image)
    python kie_image.py generate "prompt" output.png
    python kie_image.py generate "prompt" output.png --ratio 16:9 --resolution 2K
    python kie_image.py generate "prompt" output.png --task-file image-task.json --strict-format

    # Recover without a second createTask
    python kie_image.py recover <task_id> output.png
    python kie_image.py recover --task-file image-task.json

    # Edit (image + instruction → image)
    python kie_image.py edit "change background to sunset" output.png --image input.png

    # Compose (multiple images + instruction → image)
    python kie_image.py compose "combine these in collage style" output.png --image img1.png --image img2.png

    # Remove background
    python kie_image.py remove-bg input.png output.png

Examples:
    python kie_image.py generate "futuristic city at night, neon lights" city.png
    python kie_image.py edit "add orange glow effect" result.png --image photo.png --resolution 2K
    python kie_image.py compose "style transfer: apply style from first to second" out.png --image style.png --image content.png
    python kie_image.py remove-bg photo.png photo_nobg.png
"""

import argparse
import json
import os
import sys
import tempfile
import time

import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import find_workspace, load_env
WORKSPACE = find_workspace(script_path=__file__)
load_env(WORKSPACE)

# Kie.ai
KIE_API_KEY = os.environ.get("KIE_API_KEY")
BASE_URL = "https://api.kie.ai/api/v1"

# ImgBB (temporary public URL hosting for reference images)
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")
IMGBB_EXPIRATION = 3600  # 1h TTL, Kie.ai pobiera w sekundę
IMGBB_MAX_SIZE_MB = 32

ASPECT_RATIOS = ["1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9", "auto"]
MODELS = ["nano-banana-2", "nano-banana-pro", "gpt-image-2.5", "gpt-image-2.5-flare"]
GPT_MODELS = {"gpt-image-2.5": "sunburst", "gpt-image-2.5-flare": "flare"}
RESOLUTIONS = ["1K", "2K", "4K"]
FORMATS = ["png", "jpg"]

MAGIC_TO_EXTENSION = {
    "png": ".png",
    "jpeg": ".jpg",
    "webp": ".webp",
}

GPT_RATIOS = {"auto", "1:1", "5:4", "9:16", "21:9", "16:9", "4:3", "3:2", "4:5", "3:4", "2:3"}


def upload_to_imgbb(local_path: str) -> str:
    """Upload pliku do ImgBB, zwróć publiczny URL (TTL 1h). Retry 3x na 5xx/network errors."""
    if not IMGBB_API_KEY:
        raise Exception("IMGBB_API_KEY not configured in .env")

    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    if size_mb > IMGBB_MAX_SIZE_MB:
        raise Exception(f"File too large: {size_mb:.1f} MB (ImgBB limit: {IMGBB_MAX_SIZE_MB} MB)")

    filename = os.path.basename(local_path)
    print(f"  Uploading {filename} to ImgBB ({size_mb:.1f} MB)...")

    last_error = None
    for attempt in range(3):
        try:
            with open(local_path, "rb") as f:
                res = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={"key": IMGBB_API_KEY, "expiration": IMGBB_EXPIRATION},
                    files={"image": f},
                    timeout=60
                )
            if res.status_code == 200:
                url = res.json()["data"]["url"]
                print(f"  Uploaded: {url}")
                return url
            if res.status_code < 500:
                raise Exception(f"ImgBB upload failed {res.status_code}: {res.text}")
            last_error = f"{res.status_code}: {res.text}"
        except requests.RequestException as e:
            last_error = str(e)

        if attempt < 2:
            backoff = 2 ** attempt
            print(f"  Upload attempt {attempt + 1} failed ({last_error}), retrying in {backoff}s...")
            time.sleep(backoff)

    raise Exception(f"ImgBB upload failed after 3 attempts: {last_error}")


def resolve_model_id(model: str, has_images: bool) -> str:
    """User-facing 'gpt-image-2.5' (= Sunburst, jakość) / 'gpt-image-2.5-flare' (szybszy)
    rozgałęzia się na wewnętrzne ID Kie w zależności od trybu."""
    variant = GPT_MODELS.get(model)
    if variant:
        mode = "image-to-image" if has_images else "text-to-image"
        return f"gpt-image-2-5-{variant}-{mode}"
    return model


def build_task_payload(prompt: str, image_urls: list, ratio: str, resolution: str, output_format: str, model: str) -> dict:
    """Zbuduj payload — GPT Image 2.5 ma inny schema niż Nano Banana."""
    if model in GPT_MODELS:
        if ratio not in GPT_RATIOS:
            raise Exception(f"GPT Image 2.5 nie wspiera proporcji '{ratio}'. Dozwolone: {sorted(GPT_RATIOS)}")
        actual_model = resolve_model_id(model, bool(image_urls))
        input_payload = {"prompt": prompt, "aspect_ratio": ratio, "resolution": resolution}
        if image_urls:
            input_payload["input_urls"] = image_urls
        return {"model": actual_model, "input": input_payload}

    return {
        "model": model,
        "input": {
            "prompt": prompt,
            "image_input": image_urls,
            "aspect_ratio": ratio,
            "resolution": resolution,
            "output_format": output_format
        }
    }


def write_task_file(path: str, payload: dict):
    """Zapisz stan odzysku atomowo i prywatnie (o ile system wspiera chmod)."""
    if not path:
        return
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent), text=True)
    try:
        try:
            os.fchmod(fd, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def read_task_file(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not data.get("task_id") or not data.get("output"):
        raise Exception(f"Task file bez task_id/output: {path}")
    return data


def create_task(prompt: str, image_urls: list, ratio: str, resolution: str, output_format: str, model: str = "nano-banana-2") -> str:
    """Utwórz task generacji, zwróć taskId."""
    payload = build_task_payload(prompt, image_urls, ratio, resolution, output_format, model)

    response = requests.post(
        f"{BASE_URL}/jobs/createTask",
        headers={"Authorization": f"Bearer {KIE_API_KEY}"},
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    if not data.get("data"):
        raise Exception(f"API error {data.get('code')}: {data.get('msg')}")
    if "taskId" not in data["data"]:
        raise Exception(f"Unexpected response: {data}")

    return data["data"]["taskId"]


def poll_task(task_id: str, max_attempts: int = 120) -> dict:
    """Polluj status aż zakończony, zwróć wynik."""
    for attempt in range(max_attempts):
        time.sleep(5)

        response = requests.get(
            f"{BASE_URL}/jobs/recordInfo",
            headers={"Authorization": f"Bearer {KIE_API_KEY}"},
            params={"taskId": task_id},
            timeout=60,
        )

        if response.status_code != 200:
            raise Exception(f"Poll error {response.status_code}: {response.text}")

        data = response.json()["data"]
        state = data.get("state", "unknown")

        if state == "success":
            result_json = data.get("resultJson", "{}")
            return json.loads(result_json)
        elif state == "fail":
            raise Exception(f"Generation failed: {data.get('failMsg', 'Unknown error')}")

        print(f"[{attempt + 1}/{max_attempts}] Generating... (status: {state})")

    raise Exception(f"Timeout after {max_attempts * 5} seconds")


def detect_image_format(content: bytes) -> str:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def download_image(url: str, output_path: str, strict_format: bool = False) -> str:
    """Pobierz atomowo; rozszerzenie zawsze ma zgadzać się z magic bytes."""
    response = requests.get(url, timeout=300)

    if response.status_code != 200:
        raise Exception(f"Download error {response.status_code}")

    actual_format = detect_image_format(response.content)
    if actual_format == "unknown":
        raise Exception("Downloaded file is not PNG, JPEG or WebP")
    requested = Path(output_path).suffix.lower()
    requested_format = "jpeg" if requested in (".jpg", ".jpeg") else requested.lstrip(".")
    actual_path = Path(output_path)
    if requested_format != actual_format:
        if strict_format:
            raise Exception(
                f"Format mismatch: requested {requested_format or 'no extension'}, got {actual_format}. "
                "No file was saved."
            )
        actual_path = actual_path.with_suffix(MAGIC_TO_EXTENSION[actual_format])
        print(f"  Format mismatch: requested {requested_format or 'none'}, got {actual_format}; saving as {actual_path}")

    actual_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{actual_path.name}.", dir=str(actual_path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(response.content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, actual_path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return str(actual_path)


def create_remove_bg_task(image_url: str) -> str:
    """Utwórz task usuwania tła, zwróć taskId."""
    response = requests.post(
        f"{BASE_URL}/jobs/createTask",
        headers={"Authorization": f"Bearer {KIE_API_KEY}"},
        json={
            "model": "recraft/remove-background",
            "input": {
                "image": image_url
            }
        }
    )

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    if "data" not in data or "taskId" not in data["data"]:
        raise Exception(f"Unexpected response: {data}")

    return data["data"]["taskId"]


def run_generation(prompt: str, output: str, image_urls: list, ratio: str, resolution: str,
                   fmt: str, model: str = "nano-banana-2", task_file: str = None,
                   strict_format: bool = False):
    """Wspólna logika dla wszystkich trybów."""
    print(f"Creating task...")
    print(f"  Model: {resolve_model_id(model, bool(image_urls))}")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print(f"  Ratio: {ratio}, Resolution: {resolution}, Format: {fmt}")
    if image_urls:
        print(f"  Reference images: {len(image_urls)}")

    task_id = create_task(prompt, image_urls, ratio, resolution, fmt, model)
    print(f"  Task ID: {task_id}")
    task_state = {
        "schema": 1,
        "kind": "image",
        "task_id": task_id,
        "output": str(Path(output).resolve()),
        "model": resolve_model_id(model, bool(image_urls)),
        "ratio": ratio,
        "requested_format": fmt,
        "strict_format": strict_format,
        "state": "created",
        "created_at": int(time.time()),
    }
    write_task_file(task_file, task_state)
    if task_file:
        print(f"  Recovery state: {task_file}")

    print(f"Polling for result...")
    result = poll_task(task_id)

    if "resultUrls" not in result or not result["resultUrls"]:
        raise Exception(f"No result URLs in response: {result}")

    image_url = result["resultUrls"][0]
    print(f"Downloading image...")
    actual_output = download_image(image_url, output, strict_format)
    task_state.update({"state": "downloaded", "actual_output": str(Path(actual_output).resolve())})
    write_task_file(task_file, task_state)

    print(f"Image saved to: {actual_output}")


def recover_image(task_id: str, output: str, task_file: str = None, strict_format: bool = False):
    """Odzyskaj istniejący task; nigdy nie wywołuje createTask."""
    state = None
    if task_file:
        state = read_task_file(task_file)
        task_id = task_id or state["task_id"]
        output = output or state["output"]
        strict_format = strict_format or bool(state.get("strict_format"))
    if not task_id or not output:
        raise Exception("recover wymaga task_id i output albo kompletnego --task-file")
    print(f"Recovering image task {task_id}...")
    result = poll_task(task_id)
    urls = result.get("resultUrls")
    if not urls:
        raise Exception(f"No result URLs in response: {result}")
    actual_output = download_image(urls[0], output, strict_format)
    if task_file:
        state.update({"state": "downloaded", "actual_output": str(Path(actual_output).resolve())})
        write_task_file(task_file, state)
    print(f"Image saved to: {actual_output}")


def main():
    if not KIE_API_KEY:
        print("Error: KIE_API_KEY environment variable not set")
        sys.exit(1)
    parser = argparse.ArgumentParser(description="Kie.ai Image Generator")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # generate subcommand
    gen = subparsers.add_parser("generate", help="Generate image from text prompt")
    gen.add_argument("prompt", help="Text prompt for image generation")
    gen.add_argument("output", help="Output file path (e.g., output.png)")
    gen.add_argument("--model", default="gpt-image-2.5", choices=MODELS, help="Model (default: gpt-image-2.5 = Sunburst; gpt-image-2.5-flare = szybszy wariant)")
    gen.add_argument("--ratio", default="1:1", choices=ASPECT_RATIOS, help="Aspect ratio (default: 1:1)")
    gen.add_argument("--resolution", default="1K", choices=RESOLUTIONS, help="Resolution (default: 1K)")
    gen.add_argument("--format", default="png", choices=FORMATS, help="Output format (default: png)")
    gen.add_argument("--task-file", help="Atomic recovery-state JSON written before polling")
    gen.add_argument("--strict-format", action="store_true", help="Fail instead of changing extension on magic-byte mismatch")

    # edit subcommand
    edit = subparsers.add_parser("edit", help="Edit image with instruction")
    edit.add_argument("instruction", help="Edit instruction (e.g., 'change background to sunset')")
    edit.add_argument("output", help="Output file path")
    edit.add_argument("--image", required=True, help="Input image to edit")
    edit.add_argument("--model", default="gpt-image-2.5", choices=MODELS, help="Model (default: gpt-image-2.5 = Sunburst; gpt-image-2.5-flare = szybszy wariant)")
    edit.add_argument("--ratio", default="auto", choices=ASPECT_RATIOS, help="Aspect ratio (default: auto)")
    edit.add_argument("--resolution", default="1K", choices=RESOLUTIONS, help="Resolution (default: 1K)")
    edit.add_argument("--format", default="png", choices=FORMATS, help="Output format (default: png)")
    edit.add_argument("--task-file", help="Atomic recovery-state JSON written before polling")
    edit.add_argument("--strict-format", action="store_true", help="Fail instead of changing extension on magic-byte mismatch")

    # compose subcommand
    comp = subparsers.add_parser("compose", help="Compose multiple images")
    comp.add_argument("instruction", help="Composition instruction")
    comp.add_argument("output", help="Output file path")
    comp.add_argument("--image", action="append", required=True, dest="images", help="Input images (use multiple times)")
    comp.add_argument("--model", default="gpt-image-2.5", choices=MODELS, help="Model (default: gpt-image-2.5 = Sunburst; gpt-image-2.5-flare = szybszy wariant)")
    comp.add_argument("--ratio", default="1:1", choices=ASPECT_RATIOS, help="Aspect ratio (default: 1:1)")
    comp.add_argument("--resolution", default="1K", choices=RESOLUTIONS, help="Resolution (default: 1K)")
    comp.add_argument("--format", default="png", choices=FORMATS, help="Output format (default: png)")
    comp.add_argument("--task-file", help="Atomic recovery-state JSON written before polling")
    comp.add_argument("--strict-format", action="store_true", help="Fail instead of changing extension on magic-byte mismatch")

    # remove-bg subcommand
    rmbg = subparsers.add_parser("remove-bg", help="Remove background from image")
    rmbg.add_argument("input", help="Input image path")
    rmbg.add_argument("output", help="Output file path (PNG with transparent background)")
    rmbg.add_argument("--task-file", help="Atomic recovery-state JSON written before polling")
    rmbg.add_argument("--strict-format", action="store_true", help="Fail on non-PNG response")

    # recover existing task — no createTask and therefore no second charge
    rec = subparsers.add_parser("recover", help="Recover image result after interrupted polling")
    rec.add_argument("task_id", nargs="?", help="Task ID (optional with --task-file)")
    rec.add_argument("output", nargs="?", help="Output path (optional with --task-file)")
    rec.add_argument("--task-file", help="Recovery-state JSON from generate/edit/compose/remove-bg")
    rec.add_argument("--strict-format", action="store_true", help="Fail on magic-byte/extension mismatch")

    args = parser.parse_args()

    if args.mode == "recover":
        recover_image(args.task_id, args.output, args.task_file, args.strict_format)
        return

    if args.mode in ("edit", "compose", "remove-bg") and not IMGBB_API_KEY:
        raise Exception("IMGBB_API_KEY not configured in .env (required only for edit/compose/remove-bg)")

    if args.mode == "remove-bg":
        if not os.path.exists(args.input):
            raise Exception(f"Image not found: {args.input}")

        print(f"Removing background from: {args.input}")
        image_url = upload_to_imgbb(args.input)

        print(f"Creating remove-bg task...")
        task_id = create_remove_bg_task(image_url)
        print(f"  Task ID: {task_id}")
        task_state = {
            "schema": 1, "kind": "image", "mode": "remove-bg",
            "task_id": task_id, "output": str(Path(args.output).resolve()),
            "strict_format": args.strict_format, "state": "created",
            "created_at": int(time.time()),
        }
        write_task_file(args.task_file, task_state)

        print(f"Polling for result...")
        result = poll_task(task_id)

        if "resultUrls" not in result or not result["resultUrls"]:
            raise Exception(f"No result URLs in response: {result}")

        print(f"Downloading image...")
        actual_output = download_image(result["resultUrls"][0], args.output, args.strict_format)
        task_state.update({"state": "downloaded", "actual_output": str(Path(actual_output).resolve())})
        write_task_file(args.task_file, task_state)
        print(f"Done! Saved to: {actual_output}")
        return

    # Upload images to ImgBB if needed
    image_urls = []

    if args.mode == "edit":
        if not os.path.exists(args.image):
            raise Exception(f"Image not found: {args.image}")
        image_urls.append(upload_to_imgbb(args.image))
        prompt = args.instruction

    elif args.mode == "compose":
        for img_path in args.images:
            if not os.path.exists(img_path):
                raise Exception(f"Image not found: {img_path}")
            image_urls.append(upload_to_imgbb(img_path))
        prompt = args.instruction

    else:  # generate
        prompt = args.prompt

    run_generation(
        prompt, args.output, image_urls, args.ratio, args.resolution,
        args.format, args.model, args.task_file, args.strict_format
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
