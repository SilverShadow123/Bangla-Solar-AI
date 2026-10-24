
from unittest.mock import Mock, patch

import pytest

from tools.solar_resource import get_solar_resource


def test_invalid_latitude():
    with pytest.raises(ValueError):
        get_solar_resource(100, 90)


def test_invalid_longitude():
    with pytest.raises(ValueError):
        get_solar_resource(22, 200)


@patch("tools.solar_resource.requests.get")
def test_solar_resource_success(mock_get):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "outputs": {
            "totals": {
                "fixed": {"E_y": 1500}
            }
        }
    }
    mock_get.return_value = mock_response

    result = get_solar_resource(22.49, 90.35)

    assert result["estimated_yearly_generation_kwh"] == 1500
    assert result["estimated_monthly_generation_kwh"] == 125
    assert result["is_estimate"] is True
