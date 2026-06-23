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

# 기존에 포함된 MATKL 목록 외에 차량 글라스 전용 그룹이 있는지 확인
print("=== 기존 제외된 MATKL 중 차량 글라스/필름 탐색 ===")
df = qry("""
SELECT a.MATKL, COUNT(DISTINCT a.MATNR) AS CNT, MIN(t.MAKTX) AS SAMPLE
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND a.MATKL NOT IN ('M0124','M0079','M0045','M0085','M0086','M0102','M0127',
                       'M0044','M0081','M0082','M0083','M0097','M0099',
                       'M0129','M0047','M0143','M0094','M0126','M0080','M0096')
  AND (
    (UPPER(t.MAKTX) LIKE '%TRSL%' AND (UPPER(t.MAKTX) LIKE '%CAR%' OR UPPER(t.MAKTX) LIKE '%TESLA%' OR UPPER(t.MAKTX) LIKE '%BMW%' OR UPPER(t.MAKTX) LIKE '%HONDA%' OR UPPER(t.MAKTX) LIKE '%FORD%'))
    OR (UPPER(t.MAKTX) LIKE '%TREZ%' AND (UPPER(t.MAKTX) LIKE '%CAR%' OR UPPER(t.MAKTX) LIKE '%TESLA%' OR UPPER(t.MAKTX) LIKE '%MDL%'))
    OR (UPPER(t.MAKTX) LIKE '%NEOFL%' AND UPPER(t.MAKTX) LIKE '%CAR%')
    OR (UPPER(t.MAKTX) LIKE '%SSPF%' AND UPPER(t.MAKTX) LIKE '%CAR%')
  )
GROUP BY a.MATKL
ORDER BY CNT DESC
LIMIT 20
""")
print(df.to_string())

# M0079 전체 규모 파악: 차량 vs 비차량 비율
print("\n=== M0079 차량 vs 비차량 분류 ===")
df2 = qry("""
SELECT
  CASE WHEN UPPER(t.MAKTX) LIKE '%CAR%' OR UPPER(t.MAKTX) LIKE '%VEHICLE%' OR UPPER(t.MAKTX) LIKE '%TESLA%' OR UPPER(t.MAKTX) LIKE '%MDL%' THEN 'Car-related' ELSE 'Non-car' END AS TYPE,
  COUNT(DISTINCT a.MATNR) AS CNT,
  MIN(t.MAKTX) AS SAMPLE
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E' AND a.MATKL = 'M0079'
GROUP BY 1
""")
print(df2.to_string())

# 차량 글라스 전용 MATKL 탐색 (M01로 시작하는 전체)
print("\n=== M01xx 전체 MATKL 목록과 대표 설명 ===")
df3 = qry("""
SELECT a.MATKL, COUNT(DISTINCT a.MATNR) AS CNT, MIN(t.MAKTX) AS SAMPLE
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E'
  AND a.MATKL LIKE 'M01%'
GROUP BY a.MATKL
ORDER BY a.MATKL
""")
print(df3.to_string())
