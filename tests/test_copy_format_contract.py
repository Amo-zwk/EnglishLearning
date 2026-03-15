import unittest

from src.copy_format_contract import (
    ExtractionRequest,
    extract_copy_format_phrase_pairs,
    make_front_dedupe_key,
)


class CopyFormatExtractionContractTests(unittest.TestCase):
    def test_extracts_two_valid_segments_and_preserves_input_word(self) -> None:
        request = ExtractionRequest(
            input_word="abandon",
            ai_response=(
                "解析内容。\n"
                "常见搭配 放弃计划 (复制专用: $abandon the plan$ $放弃计划$)\n"
                "常见搭配 放弃希望 (复制专用: $abandon hope$ $放弃希望$)"
            ),
        )

        result = extract_copy_format_phrase_pairs(request)

        self.assertEqual(result.input_word, "abandon")
        self.assertEqual(len(result.phrases), 2)
        self.assertEqual(result.phrases[0].front, "abandon the plan")
        self.assertEqual(result.phrases[0].back, "放弃计划")
        self.assertEqual(result.phrases[1].front, "abandon hope")
        self.assertEqual(result.phrases[1].back, "放弃希望")

    def test_rejects_segment_missing_chinese_and_keeps_other_valid_segments(
        self,
    ) -> None:
        request = ExtractionRequest(
            input_word="bear",
            ai_response=(
                "(复制专用: $bear responsibility$ $承担责任$)\n"
                "(复制专用: $bear in mind$ $   $)\n"
                "(复制专用: $bear hardship$ $忍受苦难$)"
            ),
        )

        result = extract_copy_format_phrase_pairs(request)

        self.assertEqual(
            [phrase.front for phrase in result.phrases],
            ["bear responsibility", "bear hardship"],
        )
        self.assertEqual(
            [phrase.back for phrase in result.phrases], ["承担责任", "忍受苦难"]
        )

    def test_returns_empty_phrase_list_when_no_valid_copy_format_segments_exist(
        self,
    ) -> None:
        request = ExtractionRequest(
            input_word="claim",
            ai_response="这里是解释文本，没有复制专用内容，只有含义说明。",
        )

        result = extract_copy_format_phrase_pairs(request)

        self.assertEqual(result.input_word, "claim")
        self.assertEqual(result.phrases, [])

    def test_ignores_explanation_text_and_keeps_only_copy_format_pair(self) -> None:
        request = ExtractionRequest(
            input_word="deliver",
            ai_response=(
                "这个短语常用于正式语境。\n"
                "重点记忆它的固定搭配。\n"
                "deliver a speech 演讲 (复制专用: $deliver a speech$ $发表演讲$)"
            ),
        )

        result = extract_copy_format_phrase_pairs(request)

        self.assertEqual(len(result.phrases), 1)
        self.assertEqual(result.phrases[0].front, "deliver a speech")
        self.assertEqual(result.phrases[0].back, "发表演讲")

    def test_dedupe_key_normalizes_surrounding_whitespace_only(self) -> None:
        self.assertEqual(
            make_front_dedupe_key(" deliver a speech "),
            make_front_dedupe_key("deliver a speech"),
        )


if __name__ == "__main__":
    unittest.main()
