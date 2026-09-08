from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    query : str = Field (
        ...,
        description= "Natural language search query",
        examples = ["Population of France", "Area of Germany"],
        min_length=1,
        max_length=500
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query must not be empty or only whitespaces")
        return v

class SearchResult(BaseModel):
    id : int = Field (
        description ="Identifier of the fact in table",
        examples=[1]
    )

    keywords : list[str] = Field (
        description="Keywords associated with facts",
        examples=[["population", "france"]]
    )

    snippet : str = Field (
        description="Short text snippet describing the fact",
        examples=["Germany has a total area of 357,022 square kilometres."]
    )

    source : str = Field (
        description="Source URI for the fact",
        examples=["mock://worldfacts/germany"]
    )

class SearchResponse(BaseModel):
    results: list[SearchResult] = Field (
        description=["List of matching facts from the seed table, capped at 5 entries."],
        examples=[
            [
                {"id":4, 
                  "keywords":"area, germany", 
                  "snippet":"Germany has a total area of 357,022 square kilometres.", 
                  "source":"mock://worldfacts/germany"
                }
            ]
        ],
)












