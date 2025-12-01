from rest_framework.decorators import api_view
from rest_framework import status
from api.sparql_client import run_sparql
from api.views import sparql_to_json
from kagebunshin.common.utils import api_response

# pakai run_sparql dari api/sparql_client.py untuk ambil data dari GraphDB
# pakai sparql_to_json dari api/views.py untuk ratain (mempermudah) hasil SPARQL ke JSON biasa
# return dibungkus pake api_response dari kagebunshin/common/utils.py biar konsisten
# jangan lupa bikin .env

@api_view(['GET'])
def get_data(request):
    query = """
    SELECT ?s ?p ?o
    WHERE {
      ?s ?p ?o
    }
    LIMIT 10
    """
    result = run_sparql(query) 

    if "error" in result:
        return api_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Gagal ambil data", result)
    
    data = sparql_to_json(result)
    return api_response(status.HTTP_200_OK, "Berhasil ambil data", data)