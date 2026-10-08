import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Response:
    def __init__(self, content=b"", status_code=200, body=None, text=""):
        self.content = content
        self.status_code = status_code
        self._body = body or {}
        self.text = text

    def json(self):
        return self._body

    def iter_content(self, chunk_size=65536):
        yield self.content


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.image = load_script("kie_image")
        self.image.KIE_API_KEY = "test-key"

    def test_generate_does_not_require_imgbb(self):
        self.image.IMGBB_API_KEY = None
        with mock.patch.object(sys, "argv", ["kie_image.py", "generate", "prompt", "out.png"]), \
             mock.patch.object(self.image, "run_generation") as run:
            self.image.main()
        run.assert_called_once()

    def test_download_renames_to_real_magic_bytes(self):
        webp = b"RIFF" + (4).to_bytes(4, "little") + b"WEBP" + b"data"
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(self.image.requests, "get", return_value=Response(content=webp)):
            actual = self.image.download_image("https://example.test/x", str(Path(tmp) / "asset.png"))
            self.assertTrue(actual.endswith(".webp"))
            self.assertEqual(Path(actual).read_bytes(), webp)
            self.assertFalse((Path(tmp) / "asset.png").exists())

    def test_strict_format_mismatch_writes_nothing(self):
        jpeg = b"\xff\xd8\xff" + b"data"
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(self.image.requests, "get", return_value=Response(content=jpeg)):
            target = Path(tmp) / "asset.png"
            with self.assertRaisesRegex(Exception, "Format mismatch"):
                self.image.download_image("https://example.test/x", str(target), strict_format=True)
            self.assertFalse(target.exists())

    def test_task_file_exists_before_first_poll(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_file = Path(tmp) / "task.json"
            output = Path(tmp) / "out.png"

            def polling(task_id):
                state = json.loads(task_file.read_text())
                self.assertEqual(state["task_id"], "task-123")
                self.assertEqual(state["state"], "created")
                return {"resultUrls": ["https://example.test/out"]}

            with mock.patch.object(self.image, "create_task", return_value="task-123"), \
                 mock.patch.object(self.image, "poll_task", side_effect=polling), \
                 mock.patch.object(self.image, "download_image", return_value=str(output)):
                self.image.run_generation(
                    "prompt", str(output), [], "16:9", "1K", "png",
                    task_file=str(task_file), strict_format=True,
                )
            self.assertEqual(json.loads(task_file.read_text())["state"], "downloaded")

    def test_recover_never_creates_new_task(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(self.image, "create_task", side_effect=AssertionError("must not create")), \
             mock.patch.object(self.image, "poll_task", return_value={"resultUrls": ["https://example.test/out"]}), \
             mock.patch.object(self.image, "download_image", return_value=str(Path(tmp) / "out.png")):
            self.image.recover_image("existing-task", str(Path(tmp) / "out.png"))

    def test_ambiguous_create_response_is_not_retried(self):
        response = Response(body={"code": 200, "data": {}})
        with mock.patch.object(self.image.requests, "post", return_value=response) as post:
            with self.assertRaisesRegex(Exception, "API error"):
                self.image.create_task("prompt", [], "1:1", "1K", "png")
        post.assert_called_once()


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.video = load_script("kie_video")
        self.video.KIE_API_KEY = "test-key"

    def test_image_to_video_requires_explicit_aspect(self):
        with self.assertRaisesRegex(Exception, "jawnego --aspect-ratio"):
            self.video.validate_engine_args("kling", 5, None, None, "std", False, True)

    def test_webp_is_rejected_without_ffmpeg_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.png"
            path.write_bytes(b"RIFF" + (4).to_bytes(4, "little") + b"WEBP" + b"data")
            with self.assertRaisesRegex(Exception, "to WebP"):
                self.video.prepare_image(str(path))

    def test_video_task_file_exists_before_poll(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_file = Path(tmp) / "video-task.json"
            output = Path(tmp) / "out.mp4"

            def polling(task_id):
                state = json.loads(task_file.read_text())
                self.assertEqual(state["task_id"], "video-123")
                self.assertEqual(state["state"], "created")
                return {"resultUrls": ["https://example.test/out"]}

            with mock.patch.object(self.video, "create_video_task", return_value="video-123"), \
                 mock.patch.object(self.video, "poll_video_task", side_effect=polling), \
                 mock.patch.object(self.video, "download_result"):
                self.video.run_video_generation(
                    "kling", "prompt", str(output), [], 5, "16:9", None,
                    "std", False, str(task_file),
                )
            self.assertEqual(json.loads(task_file.read_text())["state"], "downloaded")

    def test_video_recover_never_creates_task(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(self.video, "create_video_task", side_effect=AssertionError("must not create")), \
             mock.patch.object(self.video, "poll_video_task", return_value={"resultUrls": ["https://example.test/out"]}), \
             mock.patch.object(self.video, "download_result"):
            self.video.recover("existing", str(Path(tmp) / "out.mp4"))

    def test_download_rejects_non_mp4(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(self.video.requests, "get", return_value=Response(content=b"not an mp4")):
            target = Path(tmp) / "out.mp4"
            with self.assertRaisesRegex(Exception, "not an MP4"):
                self.video.download_file("https://example.test/out", str(target))
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
