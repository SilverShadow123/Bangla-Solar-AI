
from unittest.mock import Mock, patch

from tools.location import get_location_coordinates


def test_get_location_coordinates():
    fake_response = Mock()

    fake_response.json.return_value = [
        {
            "display_name": "Barishal, Bangladesh",
            "lat": "22.7010",
            "lon": "90.3535",
        }
    ]

    with patch("tools.location.requests.get", return_value=fake_response):
        result = get_location_coordinates("Barishal, Bangladesh")

    assert result["found"] is True
    assert result["location"] == "Barishal, Bangladesh"
    assert result["latitude"] == 22.7010
    assert result["longitude"] == 90.3535

    fake_response.raise_for_status.assert_called_once()
