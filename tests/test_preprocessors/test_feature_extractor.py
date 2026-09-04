"""Tests for robust feature extraction."""

import pandas as pd

from whatsapp_analyzer.preprocessors.feature_extractor import process_locations


def test_process_locations_accepts_encoded_coordinates():
    data = pd.DataFrame({
        "message": ["Shared https://maps.google.com/?q=52.5200%2C13.4050"]
    })

    processed, locations = process_locations(data)

    assert processed.loc[0, "is_location"] == 1
    assert pd.isna(processed.loc[0, "message"])
    assert locations.to_dict("records") == [{"lat": 52.52, "lon": 13.405}]


def test_process_locations_ignores_malformed_google_maps_url():
    data = pd.DataFrame({"message": ["maps.google link without coordinates"]})

    processed, locations = process_locations(data)

    assert processed.loc[0, "is_location"] == 1
    assert locations.empty
    assert list(locations.columns) == ["lat", "lon"]


def test_process_locations_rejects_out_of_range_coordinates():
    data = pd.DataFrame({"message": ["https://maps.google.com/?q=120,200"]})

    _, locations = process_locations(data)

    assert locations.empty
