"""Tests para funciones utilitarias del módulo de scraping."""

import pytest
from utils import (
    clean_text,
    extract_number,
    normalize_name,
    normalize_phone,
    validate_coordinates,
    validate_rating,
)


class TestCleanText:
    def test_removes_extra_spaces(self):
        assert clean_text("  hello   world  ") == "hello world"

    def test_returns_none_for_empty(self):
        assert clean_text("") is None
        assert clean_text(None) is None

    def test_preserves_normal_text(self):
        assert clean_text("hello world") == "hello world"

    def test_collapses_newlines(self):
        assert clean_text("hello\n  world") == "hello world"


class TestExtractNumber:
    def test_extracts_integer(self):
        assert extract_number("Rating: 4") == 4.0

    def test_extracts_decimal(self):
        assert extract_number("4.5 estrellas") == 4.5

    def test_returns_none_for_no_number(self):
        assert extract_number("sin numero") is None

    def test_returns_none_for_empty(self):
        assert extract_number("") is None
        assert extract_number(None) is None

    def test_extracts_first_number(self):
        assert extract_number("42 de 100") == 42.0


class TestValidateRating:
    def test_valid_rating(self):
        assert validate_rating(4.5) is True
        assert validate_rating(0.0) is True
        assert validate_rating(5.0) is True

    def test_invalid_rating(self):
        assert validate_rating(-0.1) is False
        assert validate_rating(5.1) is False
        assert validate_rating(10.0) is False


class TestValidateCoordinates:
    def test_valid_la_paz_coordinates(self):
        assert validate_coordinates(-16.5, -68.1) is True

    def test_invalid_coordinates(self):
        assert validate_coordinates(0.0, 0.0) is False
        assert validate_coordinates(-16.5, -70.0) is False  # longitud fuera
        assert validate_coordinates(-15.0, -68.1) is False  # latitud fuera


class TestNormalizePhone:
    def test_strips_non_digits(self):
        assert normalize_phone("+591 2 2345678") == "59122345678"

    def test_returns_none_for_short(self):
        assert normalize_phone("123") is None

    def test_returns_none_for_empty(self):
        assert normalize_phone("") is None
        assert normalize_phone(None) is None

    def test_valid_phone(self):
        assert normalize_phone("22345678") == "22345678"


class TestNormalizeName:
    def test_lowercases(self):
        assert normalize_name("RESTAURANTE") == "restaurante"

    def test_strips_punctuation(self):
        assert normalize_name("Café's & Bar!") == "cafés bar"

    def test_collapses_spaces(self):
        assert normalize_name("  El   Patio  ") == "el patio"

    def test_empty_returns_empty(self):
        assert normalize_name("") == ""
        assert normalize_name(None) == ""
