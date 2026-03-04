"""Tests for tools.sanitize module."""

from tools.sanitize import wrap_untrusted, UNTRUSTED_PREAMBLE


class TestWrapUntrusted:
    def test_basic_wrapping(self):
        result = wrap_untrusted("hello")
        assert result == "<student_input>hello</student_input>"

    def test_strips_existing_tags(self):
        result = wrap_untrusted("before <student_input>injected</student_input> after")
        assert "<student_input>" not in result[len("<student_input>"):-len("</student_input>")]
        assert "injected" in result

    def test_strips_self_closing_tags(self):
        result = wrap_untrusted("text <student_input/> more")
        inner = result[len("<student_input>"):-len("</student_input>")]
        assert "<student_input" not in inner

    def test_empty_input(self):
        assert wrap_untrusted("") == ""

    def test_case_insensitive_tag_stripping(self):
        result = wrap_untrusted("text <Student_Input>injected</Student_Input> more")
        inner = result[len("<student_input>"):-len("</student_input>")]
        assert "Student_Input" not in inner

    def test_preserves_other_tags(self):
        result = wrap_untrusted("<b>bold</b>")
        assert "<b>bold</b>" in result

    def test_preamble_is_nonempty(self):
        assert len(UNTRUSTED_PREAMBLE) > 0
        assert "untrusted" in UNTRUSTED_PREAMBLE.lower()
