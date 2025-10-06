import pymysql
from dbutils.pooled_db import PooledDB

DB_CONNECTION_STRING = "mysql+pymysql://frenz4u:cw78789!@211.45.162.18:3306/starter"
DB_HOST = "211.45.162.18"
DB_USER = "frenz4u"
DB_PASSWORD = "cw78789!"
DB_NAME = "starter"

# 커넥션 풀 설정
pool = PooledDB(
    creator=pymysql,  # 사용할 DB API 모듈
    maxconnections=10,  # 최대 커넥션 수
    mincached=2,  # 초기 캐시 연결 수 (최소한으로 유지할 연결 수)
    maxcached=8,  # 최대 캐시 연결 수
    maxshared=5,  # 최대 공유 연결 수
    blocking=True,  # 커넥션 수가 최대일 때 대기할 지 여부
    maxusage=None,  # 커넥션 최대 사용 횟수 (None은 제한 없음)
    setsession=[],  # 연결 시작 시 실행할 명령어 목록
    ping=0,  # 핑 테스트 (0: 핑 없음, 1: 모든 연결에 대해, ...)
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    db=DB_NAME,
    charset="utf8",
    cursorclass=pymysql.cursors.DictCursor,  # 결과를 딕셔너리 형태로 반환
)


# 커넥션 풀에서 연결 가져오기
def query_data(sql, params=None):
    # 풀에서 연결 획득
    conn = pool.connection()
    cur = conn.cursor()

    # SQL 실행
    cur.execute(sql, params)

    # 데이터 가져오기
    rows = cur.fetchall()

    # 연결 반환 (실제로는 풀로 돌아감)
    cur.close()
    conn.close()

    return rows