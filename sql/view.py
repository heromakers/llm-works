from typing import Optional
from common.api_result import ApiResult, ResultStatus
from fastapi import APIRouter
from fastapi import Query
from fastapi import Path
from sql import defined as fixed_dao


router = APIRouter(prefix="/api/ml2sql")


@router.get("", response_model=ApiResult[dict])
async def get_sales_list(
    buyerId: Optional[int] = Query(0, ge=0),
    itemId: Optional[int] = Query(0, ge=0),
    sellerId: Optional[int] = Query(0, ge=0),
    fromDate: Optional[str] = Query(None),
    toDate: Optional[str] = Query(None),
    listCount: Optional[int] = Query(0, ge=0),
    skipCount: Optional[int] = Query(0, ge=0),
) -> ApiResult[list[dict]]:
    try:
        api_result = ApiResult[dict]()
        api_result.data = fixed_dao.query_sales_list(
            buyerId=buyerId,
            itemId=itemId,
            sellerId=sellerId,
            fromDate=fromDate,
            toDate=toDate,
            listCount=listCount,
            skipCount=skipCount,
        )
    except Exception as e:
        print("get_sales_list Exception", e)
        api_result.status = ResultStatus.ERROR
        api_result.reason = "Exception"
        api_result.message = str(e)
    return api_result


@router.get("/group_by_date", response_model=ApiResult[dict])
async def get_sales_group_by_date(
    buyerId: Optional[int] = Query(0, ge=0),
    itemId: Optional[int] = Query(0, ge=0),
    sellerId: Optional[int] = Query(0, ge=0),
    fromDate: Optional[str] = Query(None),
    toDate: Optional[str] = Query(None),
) -> ApiResult[list[dict]]:
    try:
        api_result = ApiResult[dict]()
        api_result.data = fixed_dao.query_sales_group_by_date(
            buyerId=buyerId,
            itemId=itemId,
            sellerId=sellerId,
            fromDate=fromDate,
            toDate=toDate,
        )
    except Exception as e:
        print("get_sales_list Exception", e)
        api_result.status = ResultStatus.ERROR
        api_result.reason = "Exception"
        api_result.message = str(e)
    return api_result