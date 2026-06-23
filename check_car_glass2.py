import base64
import pandas as pd
import snowflake.connector

SF_ACCOUNT   = "IEPIBKQ-OG88268"
SF_USER      = "TUTOR_SA"
SF_ROLE      = "TUTOR_USER"
SF_WAREHOUSE = "LECTURE_WH"
SF_DATABASE  = "S3"
private_key  = 'MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCpekByvBI7+VFKxQzkdgMc94XhhA3OCY5HJI3+9/ATI/+T2ABLoBFZAbUuKSYpjarB4JGazh2vB3fm/EFmtZ0uxWs+s7ir+MApPpCEbuX44uNvoq1YLygn7hofymhdBKDS/KOpRMXeUac/5+lal7niBNPscYUNnfM5hewl9Chkcd2T/xBVku6kFDPG5Xig6E+VhrN0LPDuKsGzlTB78ew10toh3d08tnAR5KTFQ1NedNdhxNGRP5ICkCkFpj9s2eppph4jdxjv2kZGu5C53upLfQjhWRwNGBgi4Q402S6pyztFX1mEkqXrdIREMEQ/DvTLWOtC1bNDFE8Cpd0QOpH3AgMBAAECggEANLq/K5N9XuCS3N8TRE+9ZzlSE9jYzLanaFYkweQVc3cbUT3+1Yi/bQB9hRezcnFL5BeBZfdkP+1kbl8k4BZ4ibFNzUvwlL0H2K1JHJM+hSHenoCwS0Qcy9OmmCaLMwm6GfsV1pf5slKYZWc78P5NDNfwsdueCJ8QqmCTGTnuiVVrwXlakBeze6TzYOjfjToYrpJEI8W9veHAGNRvJSEwVG3+btdOQlbX0eIFH5hj9tSfLwdZzwm+Dgn5H3gjfCX+QV3+ucuzzT/AKFRz5RbpoCN74xRo1FKCS+nVNAuKMR8y5RGgmcS6n4lPqNV2GcffN+/9lhbhQYuMNxt3UqsW3QKBgQDnnY7gZrI9MxHn/cM7AlS8RFbdysGAO2HYl29GZrbPDCb18AhKNAy22meaorxxpURsMsWc0KUcoyilhImzDAMaOfoIRiR8NRO3fHqCrbWdTLiwxulY0eYMfBsLzptIP8Tfvf4n5kCU/4EHa95S43qj0xhBea7cTksKK7TyCRFGLQKBgQC7UffV+M4nqPXncu3LEU0MtUGNm+MU5uTVNzweNCMFihBLXC3ImOxjSdVGbZxwDIIoLsIHOtSi9k6lkQCwjsvl4f36yUxwtnzK9uqrFU9aE6NX5s6nR/wSFjitgt0km+NKpTwfmn/vyTtBTtlcRAIIhJtqcG1JdrtF8uLNDs1TMwKBgHIhe5QsRsxNbBdrPlbHkUWsTzm/fZZYrKB0DsscNhzUmiY6f3tBJrq76K2UX1OI4qyGYEYjshjodVEKfGgUFTtJMmH9XmEuLmcOGbhnLMU0VxYVDktMMxYX2aP5zR7O/Y5bKvAyT8ScGtKzXrxth7NOg/dPpNC+a8+5NdLGkRKJAoGBAJoVqe0btdDP3j8dvdc9iwi6DItEwL2P1IpC3jPmJSzITfD/iTWp/UELGeHOBlHxKBuPotE5pnHKdBUjOtMBE14s0LO7ZCKPKgX2qEBEzjpFTybeV/0obIQgPU0VCX20sXnUg6lneHexKwnkp02LL7T8B6+9fVhhz1iRm9ibpXAbAoGAEO93ETK3Nk9qVH+CMtIepHuJWBSQQMHEWDbE+vk9oUtoNd3BneOeG+i2k+0h26ecIOohByX9YjTyfNGlEPvMsvvqBas+T5M/6UYeeBLvul7t6y70ugIIxUDvj7tL4Zr7iWZfVh4Pvrl8H/LaHxItcTa9YLrvNroDbCIwiA3WYtw='

def qry(sql):
    conn = snowflake.connector.connect(
        account=SF_ACCOUNT, user=SF_USER,
        private_key=base64.b64decode(private_key),
        role=SF_ROLE, warehouse=SF_WAREHOUSE,
        database=SF_DATABASE, schema='SAP',
    )
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    finally:
        conn.close()

# 1. M0079에서 CAR 키워드 포함 MATNR 샘플
print("=== M0079 내 CAR 관련 제품 샘플 ===")
df1 = qry("""
SELECT t.MAKTX, a.MATKL, a.MATNR
FROM S3.SAP.MAKT t
JOIN S3.SAP.MARA a ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND a.MATKL = 'M0079'
  AND (UPPER(t.MAKTX) LIKE '%CAR%' OR UPPER(t.MAKTX) LIKE '%VEHICLE%' OR UPPER(t.MAKTX) LIKE '%NAVIG%')
ORDER BY t.MAKTX
LIMIT 30
""")
print(df1.to_string())

# 2. M0124에서 tRSl (차량용 글라스 보호필름) 샘플
print("\n=== M0124 내 tRSl 차량 글라스 제품 샘플 ===")
df2 = qry("""
SELECT t.MAKTX, a.MATKL, a.MATNR
FROM S3.SAP.MAKT t
JOIN S3.SAP.MARA a ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND a.MATKL = 'M0124'
ORDER BY t.MAKTX
LIMIT 50
""")
print(df2.to_string())

# 3. tRSl 또는 tRSlHD 키워드로 전체 검색 - 차량 글라스 보호필름 전용 MATKL 있는지
print("\n=== tRSl (차량 글라스 보호필름) 전체 MATKL 현황 ===")
df3 = qry("""
SELECT a.MATKL, COUNT(DISTINCT a.MATNR) AS CNT, MIN(t.MAKTX) AS SAMPLE
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND (UPPER(t.MAKTX) LIKE '%TRSL%' OR UPPER(t.MAKTX) LIKE '%TRSPHD%')
GROUP BY a.MATKL
ORDER BY CNT DESC
""")
print(df3.to_string())

# 4. 차량 네비/대시보드/Tesla 화면 보호 관련 모든 MATKL 탐색
print("\n=== 차량 화면보호 글라스 관련 MATKL 탐색 (Tesla/Navi/Cluster/Display) ===")
df4 = qry("""
SELECT a.MATKL, COUNT(DISTINCT a.MATNR) AS CNT, MIN(t.MAKTX) AS SAMPLE1, MAX(t.MAKTX) AS SAMPLE2
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND (
    UPPER(t.MAKTX) LIKE '%TESLA%'
    OR UPPER(t.MAKTX) LIKE '%NAVIG%'
    OR UPPER(t.MAKTX) LIKE '%CLUSTER%'
    OR UPPER(t.MAKTX) LIKE '%DASHCAM%'
    OR UPPER(t.MAKTX) LIKE '%CARNAV%'
    OR (UPPER(t.MAKTX) LIKE '%BMW%' AND UPPER(t.MAKTX) LIKE '%GLASS%')
    OR (UPPER(t.MAKTX) LIKE '%BMW%' AND UPPER(t.MAKTX) LIKE '%TRSL%')
    OR (UPPER(t.MAKTX) LIKE '%IONIQ%' AND (UPPER(t.MAKTX) LIKE '%GLASS%' OR UPPER(t.MAKTX) LIKE '%TRSL%'))
  )
GROUP BY a.MATKL
ORDER BY CNT DESC
""")
print(df4.to_string())

# 5. 기존 분석에서 제외된 MATKL 중 차량 관련된 것 추가 탐색
print("\n=== 기타 차량 관련 MATKL 후보 (M0079 제외 CAR 키워드) ===")
df5 = qry("""
SELECT a.MATKL, COUNT(DISTINCT a.MATNR) AS CNT, MIN(t.MAKTX) AS SAMPLE
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND a.MATKL NOT IN ('M0124','M0079','M0045','M0085','M0086','M0102','M0127',
                       'M0044','M0081','M0082','M0083','M0097','M0099',
                       'M0129','M0047','M0143','M0094','M0126','M0080','M0096')
  AND (
    UPPER(t.MAKTX) LIKE '%CARNAV%'
    OR UPPER(t.MAKTX) LIKE '%CAR NAVI%'
    OR UPPER(t.MAKTX) LIKE '%CARAUDIO%'
    OR UPPER(t.MAKTX) LIKE '%CARDISPLAY%'
    OR (UPPER(t.MAKTX) LIKE '%CAR%' AND (UPPER(t.MAKTX) LIKE '%FILM%' OR UPPER(t.MAKTX) LIKE '%SSPF%' OR UPPER(t.MAKTX) LIKE '%TRSL%' OR UPPER(t.MAKTX) LIKE '%NEOFL%'))
  )
GROUP BY a.MATKL
ORDER BY CNT DESC
""")
print(df5.to_string())
