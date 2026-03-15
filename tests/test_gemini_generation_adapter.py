import unittest

from src.gemini_generation_adapter import (
    GeminiGenerationAdapter,
    MissingGeminiConfigurationError,
    build_generation_prompt,
    extract_api_key,
    extract_response_text,
    load_api_key,
)


class GeminiGenerationAdapterTests(unittest.TestCase):
    def test_extracts_api_key_from_metadata_text(self) -> None:
        raw_text = (
            "API 密钥详细信息\n"
            "API 密钥\n"
            "AIzaSyExampleKey1234567890abcd\n"
            "名称\nGemini API Key\n"
        )

        self.assertEqual(
            extract_api_key(raw_text),
            "AIzaSyExampleKey1234567890abcd",
        )

    def test_raises_when_api_key_text_is_missing(self) -> None:
        with self.assertRaises(MissingGeminiConfigurationError):
            extract_api_key("这里只是普通文本")

    def test_prefers_environment_key_over_file_content(self) -> None:
        api_key = load_api_key(environ={"GEMINI_API_KEY": "AIzaSyEnvKey1234567890abcd"})

        self.assertEqual(api_key, "AIzaSyEnvKey1234567890abcd")

    def test_builds_generation_prompt_from_prompt_text_and_word(self) -> None:
        prompt = build_generation_prompt("原始提示", "abandon")

        self.assertIn("原始提示", prompt)
        self.assertIn("现在只执行任务一：单词解析", prompt)
        self.assertIn("待解析单词：abandon", prompt)

    def test_extracts_joined_text_from_gemini_response(self) -> None:
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "第一段"},
                            {"text": "第二段"},
                        ]
                    }
                }
            ]
        }

        self.assertEqual(extract_response_text(response), "第一段\n第二段")

    def test_returns_content_dictionary_from_generate_word(self) -> None:
        recorded_request = {}

        def fake_post(url, payload, headers):
            recorded_request["url"] = url
            recorded_request["payload"] = payload
            recorded_request["headers"] = headers
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "(复制专用: $abandon hope$ $放弃希望$)"}]
                        }
                    }
                ]
            }

        adapter = GeminiGenerationAdapter.from_local_files(
            environ={
                "GEMINI_API_KEY": "AIzaSyEnvKey1234567890abcd",
                "COPY_FORMAT_PROMPT_FILE": "/home/usercoder/project1/英语二的备考prompt.txt",
                "COPY_FORMAT_GEMINI_MODEL": "gemini-2.5-pro",
            },
            post_json=fake_post,
        )

        result = adapter.generate_word("abandon")

        self.assertIn("generativelanguage.googleapis.com", recorded_request["url"])
        self.assertEqual(
            recorded_request["headers"]["x-goog-api-key"],
            "AIzaSyEnvKey1234567890abcd",
        )
        self.assertIn(
            "待解析单词：abandon",
            recorded_request["payload"]["contents"][0]["parts"][0]["text"],
        )
        self.assertEqual(result["content"], "(复制专用: $abandon hope$ $放弃希望$)")


if __name__ == "__main__":
    unittest.main()
