"""Tests para la clase DataCleaner."""

import pytest
from data_cleaner import DataCleaner, CleaningReport


class TestDataCleanerPipeline:
    def test_full_pipeline_runs(self, sample_restaurant_records):
        cleaner = DataCleaner(sample_restaurant_records)
        cleaned, report = cleaner.run_pipeline()

        assert isinstance(cleaned, list)
        assert isinstance(report, CleaningReport)
        assert report.total_input == len(sample_restaurant_records)
        assert report.total_output <= report.total_input
        assert len(cleaned) == report.total_output

    def test_adds_data_quality_field(self, sample_restaurant_records):
        cleaner = DataCleaner(sample_restaurant_records)
        cleaned, _ = cleaner.run_pipeline()

        for record in cleaned:
            assert "data_quality" in record
            assert 0.0 <= record["data_quality"] <= 1.0


class TestDeduplication:
    def test_removes_exact_duplicates(self):
        records = [
            {"nombre": "Test Restaurant", "fuente": "Google Maps", "rating": 4.5},
            {"nombre": "Test Restaurant", "fuente": "Google Maps", "rating": 4.0},
        ]
        cleaner = DataCleaner(records)
        cleaned, report = cleaner.run_pipeline()

        assert len(cleaned) == 1
        assert report.duplicates_removed == 1

    def test_keeps_most_complete_record(self):
        records = [
            {"nombre": "Test", "fuente": "Google Maps", "rating": None, "telefono": None},
            {"nombre": "Test", "fuente": "Google Maps", "rating": 4.5, "telefono": "12345678"},
        ]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()

        assert len(cleaned) == 1
        assert cleaned[0]["rating"] == 4.5

    def test_different_sources_not_deduplicated(self):
        records = [
            {"nombre": "Test", "fuente": "Google Maps", "rating": 4.5},
            {"nombre": "Test", "fuente": "TripAdvisor", "rating": 4.0},
        ]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()

        assert len(cleaned) == 2


class TestNormalizeRatings:
    def test_clamps_high_rating(self):
        records = [{"nombre": "Test", "fuente": "test", "rating": 6.0}]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert cleaned[0]["rating"] == 5.0

    def test_clamps_negative_rating(self):
        records = [{"nombre": "Test", "fuente": "test", "rating": -1.0}]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert cleaned[0]["rating"] == 0.0

    def test_comma_decimal_rating(self):
        records = [{"nombre": "Test", "fuente": "test", "rating": "4,5"}]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert cleaned[0]["rating"] == 4.5


class TestNormalizeCoordinates:
    def test_rejects_out_of_range(self):
        records = [{
            "nombre": "Test", "fuente": "test",
            "latitud": 0.0, "longitud": 0.0,
        }]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert cleaned[0]["latitud"] is None
        assert cleaned[0]["longitud"] is None


class TestDetectZones:
    def test_detects_zone_from_address(self):
        records = [{
            "nombre": "Test", "fuente": "test",
            "direccion": "Av. 20 de Octubre 456, La Paz",
            "zona": None,
        }]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert cleaned[0]["zona"] == "Sopocachi"

    def test_preserves_existing_zone(self):
        records = [{
            "nombre": "Test", "fuente": "test",
            "direccion": "Av. 20 de Octubre, La Paz",
            "zona": "Miraflores",
        }]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert cleaned[0]["zona"] == "Miraflores"


class TestNormalizeCuisine:
    def test_normalizes_synonyms(self):
        records = [{
            "nombre": "Test", "fuente": "test",
            "tipo_cocina": "burgers, fast food",
        }]
        cleaner = DataCleaner(records)
        cleaned, _ = cleaner.run_pipeline()
        assert "Hamburguesas" in cleaned[0]["tipo_cocina"]
        assert "Comida Rapida" in cleaned[0]["tipo_cocina"]


class TestCleaningReport:
    def test_report_string_representation(self):
        report = CleaningReport(
            total_input=100,
            total_output=95,
            duplicates_removed=5,
            records_with_fixes=20,
            field_corrections={"rating_normalizado": 3},
            null_field_counts={"telefono": 40},
        )
        report_str = str(report)
        assert "100" in report_str
        assert "95" in report_str
        assert "5" in report_str
