"""
Flask application exposing DVF aggregates for downstream dataviz dashboards.
"""

from flask import Flask, jsonify, request

try:
    from backend.services.dvf_loader import (
        get_arrondissement_summary,
        get_arrondissement_timeseries,
        get_available_years,
        refresh_cache,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running as script
    from services.dvf_loader import (
        get_arrondissement_summary,
        get_arrondissement_timeseries,
        get_available_years,
        refresh_cache,
    )


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.get("/api/health")
    def healthcheck():
        return {"status": "ok"}

    @app.post("/api/cache/reload")
    def reload_cache():
        refresh_cache()
        return {"status": "reloaded"}

    @app.get("/api/dvf/years")
    def list_years():
        return jsonify(get_available_years())

    @app.get("/api/dvf/arrondissements")
    def arrondissements():
        year = request.args.get("year", type=int)
        type_local = request.args.get("type_local")
        payload = get_arrondissement_summary(year=year, type_local=type_local)
        return jsonify({"items": payload, "year": year})

    @app.get("/api/dvf/arrondissements/<code_commune>/timeseries")
    def arrondissement_timeseries(code_commune: str):
        type_local = request.args.get("type_local")
        payload = get_arrondissement_timeseries(code_commune, type_local=type_local)
        return jsonify({"items": payload, "code_commune": str(code_commune)})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
