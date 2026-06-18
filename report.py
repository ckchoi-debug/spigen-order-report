"""
Spigen SAP Order Report -> Google Chat
GitHub Actions 환경에서 실행되는 독립 스크립트
환경변수: SF_PRIVATE_KEY, GCHAT_WEBHOOK_URL
"""

import os
import base64
import sys
import requests
from datetime import datetime
import snowflake.connector
import pandas as pd

# ── 환경변수에서 인증 정보 로드 ──────────────────────────────────────────────
SF_ACCOUNT   = "IEPIBKQ-OG88268"
SF_USER      = "TUTOR_SA"
SF_ROLE      = "TUTOR_USER"
SF_WAREHOUSE = "LECTURE_WH"
SF_DATABASE  = "S3"

SF_PRIVATE_KEY   = os.environ["SF_PRIVATE_KEY"]       # GitHub Secret
GCHAT_WEBHOOK    = os.environ["GCHAT_WEBHOOK_URL"]    # GitHub Secret

TOP_N = 20


# ── Snowflake 연결 및 쿼리 ────────────────────────────────────────────────────

def query(sql, schema=None):
    conn = snowflake.connector.connect(
        account=SF_ACCOUNT,
        user=SF_USER,
        private_key=base64.b64decode(SF_PRIVATE_KEY),
        role=SF_ROLE,
        warehouse=SF_WAREHOUSE,
        database=SF_DATABASE,
        schema=schema,
    )
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    finally:
        conn.close()


# ── SQL ───────────────────────────────────────────────────────────────────────

SQL_OPEN = f"""
WITH latest_per_order AS (
    SELECT VBELN, MAX(FILE_DATE) AS LATEST_DATE
    FROM S3.SAP.VBAK
    WHERE FILE_DATE >= '2026-01-01'
    GROUP BY VBELN
)
SELECT
    v.VBELN, v.AUDAT, v.AUART, v.KUNNR,
    v.LFSTK, v.GBSTK, v.NETWR, v.WAERK,
    DATEDIFF('day', v.AUDAT, CURRENT_DATE()) AS ORDER_AGE_DAYS
FROM S3.SAP.VBAK v
JOIN latest_per_order l ON v.VBELN = l.VBELN AND v.FILE_DATE = l.LATEST_DATE
WHERE v.LFSTK IN ('A','B')
  AND v.GBSTK != 'C'
  AND v.AUDAT >= '2026-01-01'
ORDER BY v.NETWR DESC
LIMIT {TOP_N}
"""

SQL_DELAY = """
WITH latest_vbak AS (
    SELECT v.VBELN, v.AUDAT, v.AUART, v.KUNNR, v.LFSTK, v.NETWR, v.WAERK
    FROM S3.SAP.VBAK v
    JOIN (
        SELECT VBELN, MAX(FILE_DATE) AS LATEST_DATE
        FROM S3.SAP.VBAK
        WHERE FILE_DATE >= '2026-01-01'
        GROUP BY VBELN
    ) l ON v.VBELN = l.VBELN AND v.FILE_DATE = l.LATEST_DATE
    WHERE v.LFSTK IN ('A','B') AND v.GBSTK != 'C'
),
latest_vbep AS (
    SELECT ep.VBELN, ep.POSNR, ep.EDATU, ep.WMENG, ep.LMENG,
           ep.WMENG - ep.LMENG AS REMAIN_QTY,
           DATEDIFF('day', ep.EDATU, CURRENT_DATE()) AS DELAY_DAYS
    FROM S3.SAP.VBEP ep
    JOIN (
        SELECT VBELN, POSNR, MAX(FILE_DATE) AS LATEST_DATE
        FROM S3.SAP.VBEP
        WHERE FILE_DATE >= '2026-01-01'
        GROUP BY VBELN, POSNR
    ) lep ON ep.VBELN = lep.VBELN AND ep.POSNR = lep.POSNR AND ep.FILE_DATE = lep.LATEST_DATE
    WHERE ep.EDATU < CURRENT_DATE()
      AND ep.WMENG > ep.LMENG
      AND ep.WMENG > 0
)
SELECT ep.VBELN, ep.POSNR, ak.AUDAT, ep.EDATU,
       ep.WMENG, ep.REMAIN_QTY, ep.DELAY_DAYS,
       ak.KUNNR, ak.NETWR, ak.WAERK, ak.AUART
FROM latest_vbep ep
JOIN latest_vbak ak ON ep.VBELN = ak.VBELN
ORDER BY ep.DELAY_DAYS DESC
LIMIT 20
"""


# ── 메시지 포맷 ────────────────────────────────────────────────────────────────

def fmt_open(df):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    total_value = df.groupby('WAERK')['NETWR'].sum()

    lines = [f"*[미처리 판매오더] {today} 기준*",
             f"총 {len(df)}건 (금액순 상위 {TOP_N}건)"]
    for cur, val in total_value.items():
        lines.append(f"  합계({cur}): {val:,.0f}")
    lines.append("")
    lines.append("```")
    lines.append(f"{'오더번호':<12} {'오더일':<12} {'유형':<6} {'상태':<8} {'금액':>12} {'통화':<5} {'경과':>5}")
    lines.append("-" * 65)
    for _, r in df.iterrows():
        st = "미납품" if r['LFSTK'] == 'A' else "부분납품"
        lines.append(f"{r['VBELN']:<12} {str(r['AUDAT']):<12} {r['AUART']:<6} {st:<8} "
                     f"{r['NETWR']:>12,.0f} {r['WAERK']:<5} {int(r['ORDER_AGE_DAYS']):>3}일")
    lines.append("```")
    return "\n".join(lines)


def fmt_delay(df):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if df.empty:
        return f"*[납기 지연] {today} 기준*\n납기 지연 건 없음"

    lines = [f"*[납기 지연] {today} 기준*",
             f"총 {len(df)}건 (지연일수순)"]
    lines.append("")
    lines.append("```")
    lines.append(f"{'오더번호':<12} {'항목':<6} {'오더일':<12} {'요청납기':<12} {'잔량':>8} {'지연':>5}")
    lines.append("-" * 65)
    for _, r in df.iterrows():
        lines.append(f"{r['VBELN']:<12} {str(r['POSNR']).zfill(5):<6} {str(r['AUDAT']):<12} "
                     f"{str(r['EDATU']):<12} {r['REMAIN_QTY']:>8,.0f} {int(r['DELAY_DAYS']):>3}일")
    lines.append("```")
    return "\n".join(lines)


# ── 전송 ──────────────────────────────────────────────────────────────────────

def send(text):
    resp = requests.post(GCHAT_WEBHOOK, json={"text": text}, timeout=15)
    resp.raise_for_status()
    return resp.status_code


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main():
    print("Querying Snowflake...")
    df_open  = query(SQL_OPEN,  schema='SAP')
    df_delay = query(SQL_DELAY, schema='SAP')
    print(f"Open orders: {len(df_open)}, Delayed: {len(df_delay)}")

    msg = fmt_open(df_open) + "\n\n" + fmt_delay(df_delay)

    status = send(msg)
    print(f"Sent to Google Chat: {status}")


if __name__ == "__main__":
    main()
