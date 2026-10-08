#!/usr/bin/env python3
"""
Kie.ai Video Generator - Kling 3.0 / Seedance 2.0 / Seedance 2.5 / MiniMax H3

Ten sam flow co kie_image.py: createTask -> polling recordInfo -> download.
Różnica: rendery wideo są WOLNE (znany case obrazów: 13 min; wideo bywa dłuższe),
więc polling ma budżet 40 min. Z `--task-file` taskId jest zapisany
atomowo NATYCHMIAST po createTask i przed pollingiem; stdout też go pokazuje.
Po przerwaniu wynik odzyskasz komendą `recover` bez płacenia drugi raz.

Upload lokalnych obrazów idzie przez natywny endpoint plików kie.ai (redpandaai.co),
nie ImgBB — nie trzeba osobnego klucza, plik żyje 24h i jest widoczny dla API.

Trzy silniki, jeden interfejs — do porównywania wyników na tym samym promptcie:

    --model kling       kling-3.0/video            (default; tryby std/pro/4K, natywny dźwięk)
    --model seedance    bytedance/seedance-2       (rozdzielczości do 4k, do 9 obrazów referencyjnych)
    --model seedance25  bytedance/seedance-2-5     (do 30 s, 480p/720p, dźwięk, aspect adaptive)
    --model minimax     minimax-h3/image-to-video  (768P/2K, 15 s, brak aspect_ratio przy i2v)

Usage:
    # Text -> video
    python kie_video.py generate "a cat walking through neon city" out.mp4
    python kie_video.py generate "prompt" out.mp4 --model seedance --duration 5 --resolution 1080p

    # Image -> video (first frame + opcjonalny end frame)
    python kie_video.py image-to-video "camera slowly zooms in" out.mp4 --first frame.png --aspect-ratio 16:9
    python kie_video.py image-to-video "seamless idle loop" out.mp4 --first egg.png --end egg.png --duration 5 --aspect-ratio 1:1

    # Ten sam prompt na trzech silnikach (porównanie)
    for M in kling seedance minimax; do
      python kie_video.py image-to-video "pixel-art idle bounce, seamless loop" \\
        out_$M.mp4 --model $M --first sprite.png --end sprite.png --duration 5 &
    done; wait

    # Odzysk wyniku po task_id (gdy polling się urwał)
    python kie_video.py recover <task_id> out.mp4

Examples:
    # Seamless loop pixel-art (główny use case): ten sam PNG jako first i end frame
    python kie_video.py image-to-video "pixel-art egg character idle bounce, seamless loop" \\
        egg_loop.mp4 --first egg.png --end egg.png --duration 5 --aspect-ratio 1:1 --mode std
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import find_workspace, load_env
WORKSPACE = find_workspace(script_path=__file__)
load_env(WORKSPACE)

# Kie.ai
KIE_API_KEY = os.environ.get("KIE_API_KEY")
BASE_URL = "https://api.kie.ai/api/v1"

# Natywny upload plików kie.ai (multipart), zwraca publiczny URL, TTL 24h
FILE_UPLOAD_URL = "https://kieai.redpandaai.co/api/file-stream-upload"

# Polling — wideo renderuje się wolno. 10s * 240 = 40 min budżetu.
POLL_INTERVAL = 10
POLL_MAX_ATTEMPTS = 240

MODES = ["std", "pro", "4K"]           # tylko Kling
RESOLUTIONS = ["480p", "720p", "1080p", "4k", "768P", "2K"]   # Seedance / MiniMax


# --- Rejestr silników ------------------------------------------------------
#
# Każdy model dostaje builder payloadu, bo API kie.ai NIE ujednolica inputów:
# Kling bierze klatki jako listę `image_urls`, pozostałe dwa jako osobne pola
# `first_frame_url` / `last_frame_url`. Różnią się też typem `duration`
# (Kling: string, reszta: int) i zestawem dozwolonych rozdzielczości.


def _kling_payload(p) -> dict:
    """kling-3.0/video — klatki jako image_urls[0]=first, [1]=end."""
    inp = {
        "prompt": p["prompt"],
        "duration": str(p["duration"]),
        "aspect_ratio": p["aspect_ratio"] or "1:1",
        "mode": p["mode"] or "std",
        "sound": p["sound"],
        "multi_shots": False,
    }
    if p["image_urls"]:
        inp["image_urls"] = p["image_urls"]
    return {"model": "kling-3.0/video", "input": inp}


def _seedance_payload(p) -> dict:
    """bytedance/seedance-2 — osobne pola na klatki, dźwięk domyślnie WYŁĄCZONY.

    API ma generate_audio=true w domyślnych, co przy animacji sprite'a jest
    niepotrzebnym kosztem — włączasz świadomie flagą --sound.
    """
    inp = {
        "prompt": p["prompt"],
        "duration": int(p["duration"]),
        "resolution": p["resolution"] or "720p",
        "aspect_ratio": p["aspect_ratio"] or "1:1",
        "generate_audio": p["sound"],
    }
    if len(p["image_urls"]) > 0:
        inp["first_frame_url"] = p["image_urls"][0]
    if len(p["image_urls"]) > 1:
        inp["last_frame_url"] = p["image_urls"][1]
    return {"model": "bytedance/seedance-2", "input": inp}


def _seedance25_payload(p) -> dict:
    """bytedance/seedance-2-5 — ten sam kształt inputu co seedance-2, inne limity.

    Różnice vs 2.0: duration do 30 s, rozdzielczości tylko 480p/720p (4K jeszcze
    nie wystawione w API), aspect_ratio ma wartość domyślną `adaptive` (kadr
    z klatki wejściowej). Dźwięk jak w 2.0 — domyślnie wyłączony, flaga --sound.
    """
    inp = {
        "prompt": p["prompt"],
        "duration": int(p["duration"]),
        "resolution": p["resolution"] or "720p",
        "aspect_ratio": p["aspect_ratio"] or "adaptive",
        "generate_audio": p["sound"],
    }
    if len(p["image_urls"]) > 0:
        inp["first_frame_url"] = p["image_urls"][0]
    if len(p["image_urls"]) > 1:
        inp["last_frame_url"] = p["image_urls"][1]
    return {"model": "bytedance/seedance-2-5", "input": inp}


def _minimax_payload(p) -> dict:
    """minimax-h3 — osobny model ID dla i2v i t2v; i2v nie przyjmuje aspect_ratio."""
    if p["image_urls"]:
        inp = {
            "prompt": p["prompt"],
            "duration": int(p["duration"]),
            "resolution": p["resolution"] or "2K",
            "first_frame_url": p["image_urls"][0],
        }
        if len(p["image_urls"]) > 1:
            inp["last_frame_url"] = p["image_urls"][1]
        return {"model": "minimax-h3/image-to-video", "input": inp}

    return {"model": "minimax-h3/text-to-video", "input": {
        "prompt": p["prompt"],
        "duration": int(p["duration"]),
        "resolution": p["resolution"] or "2K",
        "aspect_ratio": p["aspect_ratio"] or "16:9",
    }}


ENGINES = {
    "kling": {
        "label": "Kling 3.0",
        "build": _kling_payload,
        "aspect_ratios": ["16:9", "9:16", "1:1"],
        "resolutions": [],                       # steruje się --mode, nie --resolution
        "duration_range": (3, 15),
        "supports_end_frame": True,
        "supports_sound": True,
        "max_image_mb": 10,
    },
    "seedance": {
        "label": "Seedance 2.0 (Bytedance)",
        "build": _seedance_payload,
        "aspect_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16", "21:9", "adaptive"],
        "resolutions": ["480p", "720p", "1080p", "4k"],
        "duration_range": (4, 15),
        "supports_end_frame": True,
        "supports_sound": True,
        "max_image_mb": 10,
    },
    "seedance25": {
        "label": "Seedance 2.5 (Bytedance)",
        "build": _seedance25_payload,
        "aspect_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16", "21:9", "adaptive"],
        "resolutions": ["480p", "720p"],
        "duration_range": (4, 30),
        "supports_end_frame": True,
        "supports_sound": True,
        "max_image_mb": 30,
    },
    "minimax": {
        "label": "MiniMax H3 (Hailuo 03)",
        "build": _minimax_payload,
        "aspect_ratios": ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],   # tylko text-to-video
        "resolutions": ["768P", "2K"],
        "duration_range": (4, 15),
        "supports_end_frame": True,
        "supports_sound": False,
        "max_image_mb": 30,
    },
}


def validate_engine_args(engine_key: str, duration, resolution, aspect_ratio, mode, sound, has_images: bool):
    """Odrzuć kombinacje, których dany silnik nie obsłuży — zanim zapłacisz za task."""
    e = ENGINES[engine_key]
    lo, hi = e["duration_range"]
    if not (lo <= int(duration) <= hi):
        raise Exception(f"{e['label']}: duration musi być w zakresie {lo}-{hi} s (podano {duration})")
    if resolution:
        if not e["resolutions"]:
            raise Exception(f"{e['label']} nie przyjmuje --resolution — użyj --mode ({'/'.join(MODES)})")
        if resolution not in e["resolutions"]:
            raise Exception(f"{e['label']}: --resolution musi być jedną z {e['resolutions']}")
    if mode and engine_key != "kling":
        raise Exception(f"{e['label']} nie przyjmuje --mode — użyj --resolution ({'/'.join(e['resolutions'])})")
    if sound and not e["supports_sound"]:
        raise Exception(f"{e['label']} nie generuje dźwięku — pomiń --sound")
    if has_images and engine_key != "minimax" and not aspect_ratio:
        raise Exception(f"{e['label']} image-to-video wymaga jawnego --aspect-ratio; nie zgaduję 1:1")
    if aspect_ratio:
        if engine_key == "minimax" and has_images:
            raise Exception("MiniMax H3 image-to-video nie przyjmuje aspect_ratio — kadr bierze się z klatki")
        if aspect_ratio not in e["aspect_ratios"]:
            raise Exception(f"{e['label']}: --aspect-ratio musi być jedną z {e['aspect_ratios']}")

# Magic bytes do wykrycia realnego formatu (niezależnie od rozszerzenia)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def detect_image_format(local_path: str) -> str:
    """Zwróć realny format po magic bytes: 'png', 'jpeg', 'webp' albo 'unknown'."""
    with open(local_path, "rb") as f:
        head = f.read(12)
    if head.startswith(PNG_MAGIC):
        return "png"
    if head.startswith(JPEG_MAGIC):
        return "jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def prepare_image(local_path: str, max_mb: int = 10) -> str:
    """Zwaliduj klatkę wejściową i zwróć ścieżkę gotową do uploadu.

    Limity są per silnik (Kling/Seedance 10 MB, MiniMax 30 MB). Realny przypadek
    z projektu: plik z rozszerzeniem .png, który wewnątrz jest WebP (RIFF) — API by go
    odrzuciło. Przerywamy przed płatnym taskiem; konwersja musi być jawna i lokalna.
    """
    if not os.path.exists(local_path):
        raise Exception(f"Image not found: {local_path}")

    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    if size_mb > max_mb:
        raise Exception(f"Image too large: {size_mb:.1f} MB (limit silnika: {max_mb} MB)")

    fmt = detect_image_format(local_path)

    if fmt in ("png", "jpeg"):
        return local_path

    if fmt == "webp":
        raise Exception(
            f"{os.path.basename(local_path)} to WebP niezależnie od rozszerzenia. "
            "API przyjmuje JPG/PNG; przekonwertuj lokalnie przed płatnym taskiem."
        )

    raise Exception(f"Nieobsługiwany format obrazu ({fmt}). API przyjmuje JPG/PNG.")


def upload_to_kie(local_path: str) -> str:
    """Upload pliku do natywnego magazynu kie.ai (TTL 24h), zwróć publiczny URL.

    Retry 3x na 5xx / błędach sieci — jak w kie_image.py przy ImgBB.
    """
    filename = os.path.basename(local_path)
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"  Uploading {filename} to kie.ai ({size_mb:.1f} MB)...")

    last_error = None
    for attempt in range(3):
        try:
            with open(local_path, "rb") as f:
                res = requests.post(
                    FILE_UPLOAD_URL,
                    headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                    files={"file": (filename, f)},
                    data={"uploadPath": "images"},
                    timeout=120
                )
            if res.status_code == 200:
                url = extract_upload_url(res.json())
                print(f"  Uploaded: {url}")
                return url
            if res.status_code < 500:
                raise Exception(f"kie.ai upload failed {res.status_code}: {res.text}")
            last_error = f"{res.status_code}: {res.text}"
        except requests.RequestException as e:
            last_error = str(e)

        if attempt < 2:
            backoff = 2 ** attempt
            print(f"  Upload attempt {attempt + 1} failed ({last_error}), retrying in {backoff}s...")
            time.sleep(backoff)

    raise Exception(f"kie.ai upload failed after 3 attempts: {last_error}")


def extract_upload_url(payload: dict) -> str:
    """Wyłuskaj publiczny URL z odpowiedzi uploadu — zależnie od kształtu (flat lub {data:...})."""
    body = payload.get("data", payload) if isinstance(payload, dict) else {}
    url = body.get("fileUrl") or body.get("downloadUrl")
    if not url:
        raise Exception(f"Upload response bez URL-a: {payload}")
    return url


def build_video_payload(engine_key: str, prompt: str, image_urls: list, duration,
                        aspect_ratio: str, resolution: str, mode: str, sound: bool) -> dict:
    """Zbuduj payload dla wybranego silnika.

    Klatki zawsze podaje się tu jako listę [first, end] — mapowanie na kształt
    konkretnego API robi builder z rejestru ENGINES.
    """
    return ENGINES[engine_key]["build"]({
        "prompt": prompt,
        "image_urls": image_urls,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "mode": mode,
        "sound": sound,
    })


def write_task_file(path: str, payload: dict):
    """Zapisz stan odzysku atomowo przed pierwszym pollingiem."""
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


def create_video_task(payload: dict) -> str:
    """Utwórz task generacji wideo, zwróć taskId."""
    response = requests.post(
        f"{BASE_URL}/jobs/createTask",
        headers={"Authorization": f"Bearer {KIE_API_KEY}"},
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    # kie.ai odpowiada HTTP 200 nawet na błąd — prawdziwy kod i powód siedzą w body.
    # Bez tego brak `data` kończył się nieczytelnym TypeError zamiast komunikatu API.
    if not data.get("data"):
        raise Exception(f"API error {data.get('code')}: {data.get('msg')}")
    if "taskId" not in data["data"]:
        raise Exception(f"Unexpected response: {data}")

    return data["data"]["taskId"]


def poll_video_task(task_id: str, max_attempts: int = POLL_MAX_ATTEMPTS) -> dict:
    """Polluj status aż success/fail, zwróć sparsowany resultJson."""
    for attempt in range(max_attempts):
        time.sleep(POLL_INTERVAL)

        response = requests.get(
            f"{BASE_URL}/jobs/recordInfo",
            headers={"Authorization": f"Bearer {KIE_API_KEY}"},
            params={"taskId": task_id},
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Poll error {response.status_code}: {response.text}")

        data = response.json()["data"]
        state = data.get("state", "unknown")

        if state == "success":
            return json.loads(data.get("resultJson", "{}"))
        if state == "fail":
            raise Exception(f"Generation failed: {data.get('failMsg') or data.get('failCode', 'Unknown error')}")

        elapsed = (attempt + 1) * POLL_INTERVAL
        print(f"[{attempt + 1}/{max_attempts}] Renderuję wideo... (status: {state}, {elapsed}s)")

    raise Exception(
        f"Timeout after {max_attempts * POLL_INTERVAL} seconds. "
        f"Task nadal może się renderować — odzyskaj wynik: kie_video.py recover {task_id} <output>"
    )


def download_file(url: str, output_path: str):
    """Pobierz MP4 strumieniowo i atomowo; odrzuć odpowiedź niebędącą MP4."""
    response = requests.get(url, stream=True, timeout=300)
    if response.status_code != 200:
        raise Exception(f"Download error {response.status_code}")
    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 16):
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        with open(temporary, "rb") as handle:
            head = handle.read(12)
        if len(head) < 12 or head[4:8] != b"ftyp":
            raise Exception("Downloaded result is not an MP4 file (missing ftyp magic)")
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


def download_result(result: dict, output: str):
    """Wyłuskaj URL wideo z wyniku i zapisz."""
    urls = result.get("resultUrls")
    if not urls:
        raise Exception(f"No result URLs in response: {result}")
    print(f"Downloading video...")
    download_file(urls[0], output)
    print(f"Video saved to: {output}")


def run_video_generation(engine_key: str, prompt: str, output: str, image_paths: list, duration,
                         aspect_ratio: str, resolution: str, mode: str, sound: bool,
                         task_file: str = None):
    """Wspólna logika generacji — walidacja, przygotuj klatki, upload, task, polling, download."""
    engine = ENGINES[engine_key]
    validate_engine_args(engine_key, duration, resolution, aspect_ratio, mode, sound, bool(image_paths))

    if len(image_paths) > 1 and not engine["supports_end_frame"]:
        raise Exception(f"{engine['label']} nie obsługuje klatki końcowej — pomiń --end")

    image_urls = [upload_to_kie(prepare_image(p, engine["max_image_mb"])) for p in image_paths]

    payload = build_video_payload(engine_key, prompt, image_urls, duration,
                                  aspect_ratio, resolution, mode, sound)

    print(f"Creating video task...")
    print(f"  Engine: {engine['label']} → model {payload['model']}")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    params = ", ".join(f"{k}={v}" for k, v in payload["input"].items()
                       if k not in ("prompt", "image_urls", "first_frame_url", "last_frame_url"))
    print(f"  Params: {params}")
    if image_urls:
        roles = "first+end frame" if len(image_urls) == 2 else "first frame"
        print(f"  Reference images: {len(image_urls)} ({roles})")

    task_id = create_video_task(payload)
    task_state = {
        "schema": 1,
        "kind": "video",
        "task_id": task_id,
        "output": str(Path(output).resolve()),
        "engine": engine_key,
        "model": payload["model"],
        "duration": int(duration),
        "aspect_ratio": aspect_ratio,
        "state": "created",
        "created_at": int(time.time()),
    }
    write_task_file(task_file, task_state)
    # Task file jest trwalszy niż sam stdout i powstaje przed pollingiem.
    print(f"  Task ID: {task_id}")
    print(f"  >>> RECOVERY: kie_video.py recover {task_id} {output}")
    if task_file:
        print(f"  Recovery state: {task_file}")

    result = poll_video_task(task_id)
    download_result(result, output)
    task_state["state"] = "downloaded"
    write_task_file(task_file, task_state)


def recover(task_id: str, output: str, task_file: str = None):
    """Odzyskaj gotowy (lub renderujący się) wynik po task_id."""
    state = None
    if task_file:
        state = read_task_file(task_file)
        task_id = task_id or state["task_id"]
        output = output or state["output"]
    if not task_id or not output:
        raise Exception("recover wymaga task_id i output albo kompletnego --task-file")
    print(f"Sprawdzam task {task_id}...")
    result = poll_video_task(task_id)
    download_result(result, output)
    if task_file:
        state["state"] = "downloaded"
        write_task_file(task_file, state)


def add_common_video_args(sub, default_aspect=None):
    sub.add_argument("--model", default="kling", choices=list(ENGINES.keys()), dest="engine",
                     help="Silnik: kling (default) / seedance / seedance25 / minimax")
    sub.add_argument("--duration", default="5", help="Długość w sekundach (default: 5)")
    sub.add_argument("--aspect-ratio", default=default_aspect, dest="aspect_ratio",
                     help="Proporcje — dozwolone wartości zależą od silnika")
    sub.add_argument("--resolution", default=None,
                     help="Seedance 2.0: 480p/720p/1080p/4k · Seedance 2.5: 480p/720p · MiniMax: 768P/2K (Kling używa --mode)")
    sub.add_argument("--mode", default=None, choices=MODES, help="TYLKO Kling: std/pro/4K (default: std)")
    sub.add_argument("--sound", action="store_true", help="Dźwięk — Kling i Seedance (default: off)")
    sub.add_argument("--task-file", help="Atomic recovery-state JSON written before polling")


def main():
    if not KIE_API_KEY:
        print("Error: KIE_API_KEY environment variable not set")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Kie.ai Video Generator — Kling 3.0 / Seedance 2.0 / Seedance 2.5 / MiniMax H3")
    subparsers = parser.add_subparsers(dest="mode_cmd", required=True)

    # generate (text -> video)
    gen = subparsers.add_parser("generate", help="Generate video from text prompt")
    gen.add_argument("prompt", help="Text prompt")
    gen.add_argument("output", help="Output .mp4 path")
    add_common_video_args(gen, default_aspect="16:9")

    # image-to-video (first frame + optional end frame)
    i2v = subparsers.add_parser("image-to-video", help="Generate video from first (+ optional end) frame")
    i2v.add_argument("prompt", help="Prompt opisujący ruch/animację")
    i2v.add_argument("output", help="Output .mp4 path")
    i2v.add_argument("--first", required=True, help="First frame (JPG/PNG; Kling/Seedance 2.0 10MB, Seedance 2.5/MiniMax 30MB)")
    i2v.add_argument("--end", help="End frame (opcjonalny; ten sam plik = seamless loop)")
    add_common_video_args(i2v)

    # models — ściąga bez wywoływania API
    subparsers.add_parser("models", help="Wypisz dostępne silniki i ich parametry")

    # recover
    rec = subparsers.add_parser("recover", help="Odzyskaj wynik po task_id")
    rec.add_argument("task_id", nargs="?", help="Task ID (opcjonalny z --task-file)")
    rec.add_argument("output", nargs="?", help="Output .mp4 (opcjonalny z --task-file)")
    rec.add_argument("--task-file", help="Recovery-state JSON from generate/image-to-video")

    args = parser.parse_args()

    if args.mode_cmd == "models":
        for key, e in ENGINES.items():
            lo, hi = e["duration_range"]
            print(f"{key:9s} {e['label']}")
            print(f"          duration {lo}-{hi}s · "
                  f"{'--mode ' + '/'.join(MODES) if not e['resolutions'] else '--resolution ' + '/'.join(e['resolutions'])}")
            print(f"          aspect: {', '.join(e['aspect_ratios'])}"
                  f"{'  (t2v only)' if key == 'minimax' else ''}")
            print(f"          end frame: {'tak' if e['supports_end_frame'] else 'nie'} · "
                  f"dźwięk: {'tak' if e['supports_sound'] else 'nie'} · "
                  f"max obraz: {e['max_image_mb']} MB")
        return

    if args.mode_cmd == "recover":
        recover(args.task_id, args.output, args.task_file)
        return

    if args.mode_cmd == "image-to-video":
        image_paths = [args.first]
        if args.end:
            image_paths.append(args.end)
    else:  # generate
        image_paths = []

    run_video_generation(
        args.engine, args.prompt, args.output, image_paths,
        args.duration, args.aspect_ratio, args.resolution, args.mode, args.sound,
        args.task_file
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
