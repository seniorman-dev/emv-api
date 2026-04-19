# app.py

from flask import Flask, request, jsonify
from emv_parser import extract_card_data

app = Flask(__name__)


@app.route("/emv/parse", methods=["POST"])
def parse_emv():
    """
    POST /emv/parse

    Accepts a JSON body with a list of APDU record responses.
    Each record is a flat list of integers (byte values 0–255).
    SW1 SW2 bytes at the end of each record are automatically stripped.

    Request body:
    {
        "records": [
            [112, 129, 78, 90, ...],   ← READ RECORD response 1 (with or without SW)
            [112, 69, 95, 32, ...],    ← READ RECORD response 2
        ]
    }

    Response (success):
    {
        "success": true,
        "data": {
            "pan": "4532XXXXXXXX1234",
            "expiry": "2027/09",
            "cardholder_name": "DOE/JOHN",
            "track2_equivalent": "453211...D2709...",
            "pan_sequence_number": "01"
        }
    }

    Response (error):
    {
        "success": false,
        "error": "reason here"
    }
    """

    # ── 1. Parse request body
    body = request.get_json(silent=True)

    if body is None:
        return jsonify({
            "success": False,
            "error": "Invalid or missing JSON body"
        }), 400

    if "records" not in body:
        return jsonify({
            "success": False,
            "error": "Missing 'records' field in request body"
        }), 400

    records = body["records"]

    # ── 2. Validate records format 
    if not isinstance(records, list) or len(records) == 0:
        return jsonify({
            "success": False,
            "error": "'records' must be a non-empty list of byte arrays"
        }), 400

    for i, record in enumerate(records):
        if not isinstance(record, list):
            return jsonify({
                "success": False,
                "error": f"Record at index {i} is not a list"
            }), 400
        if not all(isinstance(b, int) and 0 <= b <= 255 for b in record):
            return jsonify({
                "success": False,
                "error": f"Record at index {i} contains invalid byte values"
            }), 400

    # ── 3. Strip SW1 SW2 from each record (last 2 bytes)
    # Seaory SDK returns response + SW1 SW2 at the end
    # SW 90 00 = success. We strip them before TLV parsing.
    cleaned_records = []
    for record in records:
        if len(record) >= 2:
            sw1, sw2 = record[-2], record[-1]
            if sw1 == 0x90 and sw2 == 0x00:
                cleaned_records.append(record[:-2])  # strip SW
            else:
                cleaned_records.append(record)  # pass as-is, parser will handle
        else:
            cleaned_records.append(record)

    # ── 4. Extract card data 
    try:
        card_data = extract_card_data(cleaned_records)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Parsing exception: {str(e)}"
        }), 500

    # ── 5. Validate that we got at least a PAN 
    if not card_data.get("pan"):
        return jsonify({
            "success": False,
            "error": "PAN not found. Ensure READ RECORD responses are included.",
            "raw_tags_found": list(card_data.keys())
        }), 422

    # ── 6. Return success
    return jsonify({
        "success": True,
        "data": card_data
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)