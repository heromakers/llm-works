from typing import Generic, TypeVar, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResultStatus(Enum):
    SUCCESS = "success"
    FAIL = "fail"
    EXPIRED = "expired"
    INVALID = "invalid"
    MALFORMED = "malformed"
    DENIED = "denied"
    ERROR = "error"


class ApiResult(BaseModel, Generic[T]):
    status: ResultStatus = ResultStatus.SUCCESS
    reason: str = ""
    message: str = ""
    data: Optional[T] = None
    count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)