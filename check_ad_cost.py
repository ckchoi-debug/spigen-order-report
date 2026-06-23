import sys, base64, snowflake.connector, pandas as pd
sys.path.insert(0, r'C:\Users\User\Downloads\snowflake')
from tutor_snowflake_usage import SF_ACCOUNT, SF_USER, SF_ROLE, SF_WAREHOUSE, SF_DATABASE, private_key

conn = snowflake.connector.connect(
    account=SF_ACCOUNT, user=SF_USER,
    private_key=base64.b64decode(private_key),
    role=SF_ROLE, warehouse=SF_WAREHOUSE, database=SF_DATABASE,
)
cur = conn.cursor()

# 1. COLUMN_DEFINITIONS 컬럼 목록 먼저 확인
print("=== COLUMN_DEFINITIONS 컬럼 목록 ===")
cur.execute("SELECT * FROM S3.SAP.COLUMN_DEFINITIONS LIMIT 3")
cols = [d[0] for d in cur.description]
print("컬럼:", cols)
df = pd.DataFrame(cur.fetchall(), columns=cols)
print(df.to_string())

# 2. CE11000 관련 정의 전체
print("\n=== CE11000 필드 정의 ===")
cur.execute("SELECT * FROM S3.SAP.COLUMN_DEFINITIONS WHERE TABLE_NAME = 'CE11000' ORDER BY COLUMN_NAME")
cols2 = [d[0] for d in cur.description]
df2 = pd.DataFrame(cur.fetchall(), columns=cols2)
print(df2.to_string())

# 3. SKAT 한국어 광고 검색 (SPRAS 확인)
print("\n=== SKAT 사용 가능 언어 ===")
cur.execute("SELECT DISTINCT SPRAS FROM S3.SAP.SKAT LIMIT 20")
print(cur.fetchall())

conn.close()
