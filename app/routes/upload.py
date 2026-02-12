from flask import Blueprint, request, jsonify
from app.utils.validators import allowed_file
from app.services.file_processor import process_excel, process_pdf

upload_bp = Blueprint("upload", __name__)


def _to_native(value):
    """Convert numpy / pandas types to native Python"""
    if value is None:
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime().isoformat()
        except Exception:
            pass
    return value


def _convert(obj):
    """Recursively convert objects to JSON-safe types"""
    if isinstance(obj, list):
        return [_convert(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _convert(value) for key, value in obj.items()}
    return _to_native(obj)


@upload_bp.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    results = []

    final_table = []
    final_max = None
    final_min = None

    for file in files:
        if not file or file.filename == "":
            continue

        if not allowed_file(file.filename):
            return jsonify({"error": f"Invalid file type: {file.filename}"}), 400

        # Process file directly from memory without saving
        filename = file.filename
        
        results.append({
            "filename": filename,
            "status": "processed"
        })

        # Reset file pointer to beginning
        file.seek(0)
        
        # Process file from memory
        if filename.lower().endswith(".pdf"):
            table, max_balance, min_balance = process_pdf(file)
        else:
            table, max_balance, min_balance = process_excel(file)

        # Merge / assign results (last file wins)
        final_table = table or []
        final_max = max_balance
        final_min = min_balance

    return jsonify({
        "message": "Files processed successfully",
        "files": results,
        "table": _convert(final_table),
        "max_balance": _to_native(final_max),
        "min_balance": _to_native(final_min)
    }), 200

@upload_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200