from rest_framework.decorators import api_view
from rest_framework import status
from kagebunshin.common.utils import api_response
from api.sparql_client import run_sparql
from api.views import sparql_to_json

import re

FORBIDDEN_PATTERNS = [
    r'^\s*INSERT\b',
    r'^\s*DELETE\b',
    r'^\s*UPDATE\b',
    r'^\s*LOAD\b',
    r'^\s*CREATE\b',
    r'^\s*DROP\b',
    r'^\s*CLEAR\b',
    r'^\s*ADD\b',
    r'^\s*MOVE\b',
    r'^\s*COPY\b',
    r'^\s*ALTER\b',
]

def find_forbidden_keyword(query: str):
    lines = query.splitlines()
    for line in lines:
        for pattern in FORBIDDEN_PATTERNS:
            if re.match(pattern, line, flags=re.IGNORECASE):
                # ambil keyword dari pattern
                keyword = pattern.strip(r'^\s*\b').split('\\b')[0].strip()
                return keyword.upper()
    return None

def normalize_query(query: str) -> str:
    return "\n".join(line.rstrip() for line in query.strip().splitlines())

def is_select_query(query: str):
    text = query.strip().upper()

    # SELECT harus muncul
    if "SELECT" not in text:
        return False
    
    # SELECT harus muncul sebelum WHERE
    select_pos = text.find("SELECT")
    where_pos = text.find("WHERE")

    # kalau WHERE tidak ada, dihandle validate_query
    if where_pos != -1 and select_pos > where_pos:
        return False

    return True


def validate_query(query: str):
    if not query or not isinstance(query, str):
        return "Query tidak boleh kosong."

    normalized = normalize_query(query)
    upper_q = normalized.upper()

    forbidden = find_forbidden_keyword(normalized)
    if forbidden:
        return f"Query mengandung operasi yang dilarang yaitu {forbidden}"

    if not is_select_query(normalized):
        return "Hanya query SELECT yang diperbolehkan."

    if "WHERE" not in upper_q:
        return "Query tidak valid, bagian WHERE tidak ditemukan."

    if "{" not in upper_q or "}" not in upper_q:
        return "Query harus mengandung kurung {}."

    return None

@api_view(['POST'])
def execute_query(request):
    query = request.data.get("query")

    if not query:
        return api_response(status.HTTP_400_BAD_REQUEST, "Query SPARQL tidak boleh kosong", {})

    error = validate_query(query)
    if error:
        return api_response(status.HTTP_400_BAD_REQUEST, error, {})

    result = run_sparql(query)

    if "error" in result:
        raw_error = result.get("error") or ""
        lower = raw_error.lower()

        # graphdb mati
        if ("connection refused" in lower 
            or "failed to establish" in lower
            or "max retries exceeded" in lower
            or "timed out" in lower):
            return api_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Database tidak merespon. Silahkan coba lagi nanti.",
                {}
            )

        # error lain (query salah, malformed, dll)
        return api_response(
            status.HTTP_400_BAD_REQUEST,
            f"Query gagal dijalankan: {raw_error}",
            {}
        )
    
    simplified = sparql_to_json(result)
    return api_response(status.HTTP_200_OK, "Query berhasil dijalankan", simplified)
