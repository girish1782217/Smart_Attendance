from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.main import create_app


def _app_with_test_routes():
    app = create_app()

    @app.get("/__test/app-error")
    def _raise_app_error():
        raise NotFoundError("Widget not found.", code="WIDGET_NOT_FOUND")

    @app.get("/__test/unhandled-error")
    def _raise_unhandled_error():
        raise RuntimeError("boom: sensitive internal detail")

    return app


def test_app_error_returns_standard_envelope():
    with TestClient(_app_with_test_routes(), raise_server_exceptions=False) as client:
        response = client.get("/__test/app-error")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {"code": "WIDGET_NOT_FOUND", "message": "Widget not found."},
    }


def test_unhandled_error_returns_generic_envelope_without_leaking_details():
    with TestClient(_app_with_test_routes(), raise_server_exceptions=False) as client:
        response = client.get("/__test/unhandled-error")

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "boom" not in body["error"]["message"]
    assert "sensitive" not in body["error"]["message"]
