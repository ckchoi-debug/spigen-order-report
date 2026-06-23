import base64
import pandas as pd
import snowflake.connector
import sys

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

def out(s):
    sys.stdout.buffer.write((s + "\n").encode('utf-8'))

# M01xx 전체 MATKL 목록
out("=== M01xx MATKL 전체 목록 ===")
df = qry("""
SELECT a.MATKL, COUNT(DISTINCT a.MATNR) AS CNT, MIN(t.MAKTX) AS DESC1
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E' AND a.MATKL LIKE 'M01%'
GROUP BY a.MATKL
ORDER BY a.MATKL
""")
out(df.to_string())

# M0079 차량 vs 비차량 분류
out("\n=== M0079 차량 vs 비차량 ===")
df2 = qry("""
SELECT
  CASE WHEN UPPER(t.MAKTX) LIKE '%CAR%' OR UPPER(t.MAKTX) LIKE '%VEHICLE%'
            OR UPPER(t.MAKTX) LIKE '%TESLA%' OR UPPER(t.MAKTX) LIKE '%MDLY%'
            OR UPPER(t.MAKTX) LIKE '%MDL%' THEN 'Car' ELSE 'Non-car' END AS TYPE,
  COUNT(DISTINCT a.MATNR) AS CNT
FROM S3.SAP.MARA a
JOIN S3.SAP.MAKT t ON a.MATNR = t.MATNR
WHERE t.SPRAS = 'E' AND a.MATKL = 'M0079'
GROUP BY 1
""")
out(df2.to_string())
