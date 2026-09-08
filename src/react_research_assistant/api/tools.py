from fastapi import APIRouter

from react_research_assistant.models.search import SearchRequest, SearchResponse
from react_research_assistant.services.search import search_facts


router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search mock world facts",
    description=(
        "Searches the supplied mock world-fact table. "
        "This tool contains no Tideline facts. "
        "No match returns an empty results list with HTTP 200."
    ),
)
def search_tool(request: SearchRequest) -> SearchResponse:
    """Run keyword search against the supplied mock fact table."""

    results = search_facts(query=request.query)

    return SearchResponse(results=results)
