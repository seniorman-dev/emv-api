# emv_parser.py


def parse_tlv(data: list) -> dict:
    """
    Recursively parses TLV (Tag-Length-Value) encoded EMV bytes.
    Returns a flat dict of { "TAG_HEX": [value bytes] }
    """
    result = {}
    i = 0

    while i < len(data):
        if i >= len(data):
            break

        # ── Read Tag
        tag = data[i]
        i += 1

        # Two-byte tag: low 5 bits of first byte are all 1s
        if (tag & 0x1F) == 0x1F:
            if i >= len(data):
                break
            tag = (tag << 8) | data[i]
            i += 1

        # ── Read Length
        if i >= len(data):
            break

        length = data[i]
        i += 1

        # Long-form length encoding
        if length & 0x80:
            num_len_bytes = length & 0x7F
            length = 0
            for _ in range(num_len_bytes):
                if i >= len(data):
                    break
                length = (length << 8) | data[i]
                i += 1

        # ── Read Value
        value = data[i:i + length]
        i += length

        # Store using uppercase hex tag string
        if tag <= 0xFF:
            tag_str = f"{tag:02X}"
        else:
            tag_str = f"{tag:04X}"

        result[tag_str] = list(value)

        # ── Recurse into Constructed Tags 
        # A tag is "constructed" if bit 6 (0x20) of its first byte is set
        first_byte = (tag >> 8) if tag > 0xFF else tag
        if first_byte & 0x20:
            nested = parse_tlv(list(value))
            result.update(nested)

    return result


def format_pan(pan_bytes: list) -> str:
    """
    PAN bytes are BCD encoded. Convert to hex string and strip trailing F padding.
    e.g. [0x45, 0x32, 0x11, 0xFF] → '453211'
    """
    return ''.join(f'{b:02X}' for b in pan_bytes).rstrip('F')


def format_expiry(exp_bytes: list) -> str:
    """
    Expiry is YYMM BCD encoded.
    e.g. [0x27, 0x09] → '2027/09'
    """
    hex_str = ''.join(f'{b:02X}' for b in exp_bytes)
    year = hex_str[:2]
    month = hex_str[2:]
    return f"20{year}/{month}"


def format_cardholder_name(name_bytes: list) -> str:
    """
    Cardholder name is ASCII encoded.
    Format is usually: SURNAME/FIRSTNAME
    """
    return ''.join(chr(b) for b in name_bytes).strip()


def extract_card_data(apdu_records: list) -> dict:
    """
    Accepts a list of raw APDU record response byte arrays.
    Each item is a list of ints (one READ RECORD response).
    Parses all TLV data and extracts card fields.

    Args:
        apdu_records: [ [0x70, 0x81, ...], [0x70, 0x45, ...], ... ]

    Returns:
        {
            "pan": "4532XXXXXXXX1234",
            "expiry": "2027/09",
            "cardholder_name": "DOE/JOHN",
            "track2_equivalent": "...",
            "pan_sequence_number": "01"
        }
    """
    all_tlv = {}

    for record_bytes in apdu_records:
        try:
            tlv = parse_tlv(record_bytes)
            all_tlv.update(tlv)
        except Exception:
            continue  # skip malformed records

    card_data = {}

    # Tag 5A — PAN
    if "5A" in all_tlv:
        card_data["pan"] = format_pan(all_tlv["5A"])

    # Tag 5F24 — Expiry Date (YYMM)
    if "5F24" in all_tlv:
        card_data["expiry"] = format_expiry(all_tlv["5F24"])

    # Tag 5F20 — Cardholder Name
    if "5F20" in all_tlv:
        card_data["cardholder_name"] = format_cardholder_name(all_tlv["5F20"])

    # Tag 57 — Track 2 Equivalent Data
    if "57" in all_tlv:
        card_data["track2_equivalent"] = ''.join(
            f'{b:02X}' for b in all_tlv["57"]
        )

    # Tag 5F34 — PAN Sequence Number
    if "5F34" in all_tlv:
        card_data["pan_sequence_number"] = f"{all_tlv['5F34'][0]:02X}"

    # Tag 9F07 — Application Usage Control
    if "9F07" in all_tlv:
        card_data["application_usage_control"] = ''.join(
            f'{b:02X}' for b in all_tlv["9F07"]
        )

    return card_data