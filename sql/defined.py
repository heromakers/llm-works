from sql.query_base import query_data


def query_sales_list(
    buyerId: int = None,
    itemId: int = None,
    sellerId: int = None,
    fromDate: str = None,
    toDate: str = None,
    listCount: int = None,
    skipCount: int = None,
) -> list[dict]:
    where_sql = "WHERE 1 = 1"
    params = {}
    if buyerId:
        where_sql += " AND sls.buyer_id = %(buyerId)s"
        params["buyerId"] = buyerId
    if itemId:
        where_sql += " AND sls.item_id = %(itemId)s"
        params["itemId"] = itemId
    if sellerId:
        where_sql += " AND itm.seller_id = %(sellerId)s"
        params["itemId"] = sellerId
    if fromDate or toDate:
        if not fromDate:
            fromDate = "2000-01-01"
        if not toDate:
            toDate = "2999-12-31"
        where_sql += " AND DATE(sls.sales_at) BETWEEN %(fromDate)s AND %(toDate)s"
        params["fromDate"] = fromDate
        params["toDate"] = toDate

    list_sql = f"""
        SELECT sls.*
            ,usr.user_name
            ,itm.item_name
            ,itm.price
            ,slr.seller_name
        FROM t_sales sls
        JOIN t_user usr ON usr.user_id = sls.buyer_id
        JOIN t_item itm ON itm.item_id = sls.item_id
        JOIN t_seller slr ON slr.seller_id = itm.seller_id
        {where_sql}
        ORDER BY sls.sales_id DESC
    """
    if listCount:
        list_sql += f" LIMIT {skipCount or 0}, {listCount}"

    rows = query_data(list_sql, params)
    if rows is None:
        return [], []
    
    data = []
    for row in rows:
        data.append([row["sales_id"], row["item_id"], row["buyer_id"], row["quantity"], row["discount"], row["total_amount"], row["sales_at"].strftime("%Y-%m-%d %H:%M:%S"), row["user_name"], row["item_name"], row["price"], row["seller_name"]])
    return data, ["ID", "상품 ID", "구매자 ID", "수량", "할인금액", "총금액", "판매일시", "구매자명", "상품명", "상품가격", "판매자명"]


def query_sales_group_by_date(
    buyerId: int = None,
    itemId: int = None,
    sellerId: int = None,
    fromDate: str = None,
    toDate: str = None,
) -> list[dict]:
    where_sql = "WHERE 1 = 1"
    params = {}
    if buyerId:
        where_sql += " AND sls.buyer_id = %(buyerId)s"
        params["buyerId"] = buyerId
    if itemId:
        where_sql += " AND sls.item_id = %(itemId)s"
        params["itemId"] = itemId
    if sellerId:
        where_sql += " AND itm.seller_id = %(sellerId)s"
        params["itemId"] = sellerId
    if fromDate or toDate:
        if not fromDate:
            fromDate = "2000-01-01"
        if not toDate:
            toDate = "2999-12-31"
        where_sql += " AND DATE(sls.sales_at) BETWEEN %(fromDate)s AND %(toDate)s"
        params["fromDate"] = fromDate
        params["toDate"] = toDate

    list_sql = f"""
        SELECT mt.sales_date
            ,SUM(mt.quantity) as quantity
            ,SUM(mt.discount) as discount
            ,SUM(mt.total_amount) as total_amount
        FROM (
            SELECT sls.*
                ,DATE(sls.sales_at) as sales_date
                ,usr.user_name
                ,itm.item_name
                ,itm.price
                ,slr.seller_name
            FROM t_sales sls
            JOIN t_user usr ON usr.user_id = sls.buyer_id
            JOIN t_item itm ON itm.item_id = sls.item_id
            JOIN t_seller slr ON slr.seller_id = itm.seller_id
            {where_sql}
        ) mt
        GROUP BY mt.sales_date
        ORDER BY mt.sales_date
    """

    rows = query_data(list_sql, params)
    return rows