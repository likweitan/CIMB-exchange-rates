"""HTTP routes for exchange rate data."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services import get_latest_rates, get_rates
from app.services.supabase_client import (
    SupabaseConfigurationError,
    supabase_configured,
)

api_bp = Blueprint("api", __name__)


@api_bp.get("/rates")
def list_rates():
    """Return exchange rates ordered by most recent first."""
    limit = request.args.get("limit", type=int)
    try:
        data = get_rates(limit=limit)
    except SupabaseConfigurationError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify({"data": data, "count": len(data)})


@api_bp.get("/rates/latest")
def latest_rates():
    """Return the most recent rate for each platform."""
    try:
        data = get_latest_rates()
    except SupabaseConfigurationError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify({"data": data, "count": len(data)})


@api_bp.get("/health")
def healthcheck():
    """Basic healthcheck endpoint."""
    return jsonify(
        {
            "status": "ok",
            "supabase_configured": supabase_configured(),
        }
    )
