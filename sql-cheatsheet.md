# SQL Cheatsheet (PostgreSQL)

> Dùng cho DataLemur và phỏng vấn DE. Gặp pattern mới thì thêm vào đây.

---

## 1. Khung 5 bước trước khi viết code

1. **Output & grain**: kết quả cần những cột nào? Mỗi dòng là gì (1 user / 1 ngày / 1 user-tháng)?
2. **Bảng & khóa**: dùng bảng nào, nối bằng cột nào, quan hệ 1-1 hay 1-nhiều (1-nhiều dễ nhân bản dòng)?
3. **Pattern**: dịch keyword trong đề sang kỹ thuật (bảng mục 3).
4. **Viết từng bước bằng CTE**, chạy và nhìn kết quả trung gian.
5. **Soát bẫy**: NULL, duplicate, chia số nguyên, đồng hạng (tie), lọc sai chỗ (WHERE vs HAVING).

Trước khi code, viết ra:
```
Grain: ...
Tables/keys: ...
Pattern: ...
```

---

## 2. Thứ tự thực thi (logical order)

```
FROM / JOIN → WHERE → GROUP BY → HAVING → SELECT → window functions → DISTINCT → ORDER BY → LIMIT
```

Hệ quả:
- Không dùng alias của SELECT trong WHERE / GROUP BY (Postgres cho GROUP BY alias, nhưng đừng dựa vào).
- Không lọc kết quả window function trong WHERE → bọc CTE rồi lọc ở ngoài.
- Lọc trên aggregate → `HAVING`, không phải `WHERE`.

---

## 3. Keyword → Pattern

| Problem says | Think of |
|---|---|
| "only…", "in 2022", "where…", "excluding…" | `WHERE` |
| "for each…", "per…", "by…" | `GROUP BY` |
| "at least N…", "more than X…", "who have…" (after counting) | `HAVING` |
| "never", "no…", "without", "did not", "have not" | anti-join `LEFT JOIN … WHERE b.id IS NULL` / `NOT EXISTS` |
| "percentage", "ratio", "rate", "share of…" | `SUM(CASE WHEN …) * 1.0 / COUNT(*)` |
| "Nth", "second highest", "top N per…", "highest in each…" | `ROW_NUMBER` / `RANK` / `DENSE_RANK OVER (PARTITION BY …)` |
| "rolling", "moving average", "over the last N days" | `AVG(...) OVER (ORDER BY … ROWS BETWEEN N PRECEDING AND CURRENT ROW)` |
| "compared to previous", "day-over-day", "change from last…" | `LAG` / `LEAD` |
| "first", "last", "earliest", "most recent" | `MIN` / `MAX`, hoặc `ROW_NUMBER` |
| "cumulative", "running total" | `SUM(...) OVER (ORDER BY …)` |
| "consecutive", "streak" | gaps & islands (`ROW_NUMBER` + date difference) |
| "both A and B", "in A but not B" | `INTERSECT` / `EXCEPT`, hoặc `JOIN` / anti-join |
| "unique", "distinct users" | `COUNT(DISTINCT col)` |
| "duplicate", "appears more than once" | `GROUP BY … HAVING COUNT(*) > 1` |
| "each month", "monthly", "weekly" | `DATE_TRUNC('month', ts)` / `EXTRACT(MONTH FROM ts)` |
| "retention", "returned the next month" | self-join / `EXISTS` trên tháng trước |
| "pivot", "one column per…" | `SUM(CASE WHEN cat = 'x' THEN val END) AS x` |

---

## 4. Cú pháp nhanh

### SELECT & lọc
```sql
SELECT col1, col2 AS alias
FROM t
WHERE col IN ('a', 'b')
  AND amount BETWEEN 10 AND 100        -- bao gồm 2 đầu
  AND name ILIKE '%solar%'             -- ILIKE = không phân biệt hoa thường
  AND deleted_at IS NULL               -- KHÔNG dùng = NULL
ORDER BY col1 DESC, col2
LIMIT 10;
```

### Aggregate
```sql
COUNT(*)              -- đếm mọi dòng
COUNT(col)            -- bỏ qua NULL
COUNT(DISTINCT col)   -- giá trị khác nhau
SUM(col), AVG(col), MIN(col), MAX(col)

SELECT user_id, COUNT(*) AS n
FROM events
WHERE event_type = 'click'     -- lọc dòng TRƯỚC khi gom
GROUP BY user_id
HAVING COUNT(*) >= 3;          -- lọc nhóm SAU khi gom
```

### JOIN
```sql
INNER JOIN  -- chỉ dòng khớp cả 2 bên
LEFT JOIN   -- giữ hết bên trái, bên phải không khớp → NULL
FULL JOIN   -- giữ hết cả 2
CROSS JOIN  -- tích Descartes (ghép mọi cặp)

SELECT a.id, b.val
FROM a
LEFT JOIN b
  ON a.id = b.a_id
 AND b.status = 'active';   -- điều kiện bảng phải đặt ở ON để giữ đúng LEFT JOIN
```
> Đặt `b.status = 'active'` ở WHERE sẽ biến LEFT JOIN thành INNER JOIN.

### CASE WHEN
```sql
CASE
  WHEN score >= 90 THEN 'A'
  WHEN score >= 80 THEN 'B'
  ELSE 'C'
END AS grade
```

### CTE & subquery
```sql
WITH step1 AS (
  SELECT ...
),
step2 AS (
  SELECT ... FROM step1
)
SELECT * FROM step2;

-- subquery trong WHERE
WHERE salary < (SELECT MAX(salary) FROM employee)

-- EXISTS / NOT EXISTS
WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.a_id = a.id)
```

### Set operations
```sql
SELECT id FROM a
UNION        -- gộp, bỏ trùng   (UNION ALL: giữ trùng, nhanh hơn)
INTERSECT    -- có ở cả 2
EXCEPT       -- có ở a, không có ở b
SELECT id FROM b;
```

### Window functions
```sql
func() OVER (PARTITION BY grp ORDER BY col [frame])
```

| Loại | Hàm | Ghi chú |
|---|---|---|
| Ranking | `ROW_NUMBER()` | 1,2,3,4 (không đồng hạng) |
| | `RANK()` | 1,2,2,4 (đồng hạng, nhảy số) |
| | `DENSE_RANK()` | 1,2,2,3 (đồng hạng, không nhảy) |
| | `NTILE(4)` | chia thành 4 nhóm |
| Offset | `LAG(col, 1)` / `LEAD(col, 1)` | giá trị dòng trước / sau |
| | `FIRST_VALUE(col)` / `LAST_VALUE(col)` | LAST_VALUE cần frame đầy đủ |
| Aggregate | `SUM/AVG/COUNT/MIN/MAX(col) OVER (...)` | không gom dòng |

Frame:
```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW              -- 3 dòng gần nhất
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW      -- từ đầu đến hiện tại
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  -- cả partition
```
> Có `ORDER BY` mà không ghi frame → mặc định `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` (running total).

### Ngày giờ (Postgres)
```sql
ts::DATE                                   -- timestamp → date
DATE_TRUNC('month', ts)                    -- về đầu tháng (giữ kiểu timestamp)
EXTRACT(YEAR FROM ts), EXTRACT(MONTH FROM ts), EXTRACT(DOW FROM ts)  -- DOW: 0 = Chủ nhật
ts + INTERVAL '7 days'
CURRENT_DATE, NOW()
date2 - date1                              -- DATE - DATE = số ngày (integer)
ts2::DATE - ts1::DATE                      -- số ngày giữa 2 timestamp
EXTRACT(EPOCH FROM ts2 - ts1) / 3600       -- số giờ
TO_CHAR(ts, 'YYYY-MM')                     -- format
```

### Chuỗi
```sql
LOWER(s), UPPER(s), TRIM(s), LENGTH(s)
s1 || ' ' || s2           -- nối chuỗi (hoặc CONCAT)
SUBSTRING(s FROM 1 FOR 3)
SPLIT_PART(s, ',', 1)
REPLACE(s, 'a', 'b')
STRING_AGG(name, ', ' ORDER BY name)   -- gộp nhiều dòng thành 1 chuỗi
```

### NULL, ép kiểu, làm tròn
```sql
COALESCE(col, 0)            -- NULL → 0
NULLIF(denominator, 0)      -- tránh chia cho 0
col::NUMERIC, CAST(col AS INT)
ROUND(x::NUMERIC, 2)        -- Postgres: ROUND(…, 2) cần kiểu NUMERIC
a * 1.0 / b                 -- tránh chia số nguyên
```

---

## 5. Pattern templates

### Anti-join: "never / without"
```sql
SELECT a.id
FROM a
LEFT JOIN b ON a.id = b.a_id
WHERE b.a_id IS NULL;
```

### Top N per group
```sql
WITH ranked AS (
  SELECT *,
         DENSE_RANK() OVER (PARTITION BY category ORDER BY spend DESC) AS rnk
  FROM sales
)
SELECT * FROM ranked WHERE rnk <= 2;
```

### Nth event per user
```sql
WITH t AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_ts) AS rn
  FROM events
)
SELECT * FROM t WHERE rn = 3;
```

### Nth highest value overall
```sql
SELECT DISTINCT salary
FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
  FROM employee
) x
WHERE rnk = 2;
```

### Percentage / conditional aggregation
```sql
SELECT
  ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS success_pct
FROM jobs;
```

### Pivot
```sql
SELECT
  user_id,
  SUM(CASE WHEN device = 'laptop' THEN 1 ELSE 0 END) AS laptop_views,
  SUM(CASE WHEN device IN ('phone', 'tablet') THEN 1 ELSE 0 END) AS mobile_views
FROM viewership
GROUP BY user_id;
```

### Rolling average
```sql
SELECT day, value,
       ROUND(AVG(value) OVER (
         ORDER BY day
         ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       )::NUMERIC, 2) AS rolling_3d
FROM daily;
```

### Running total
```sql
SELECT day, amount,
       SUM(amount) OVER (ORDER BY day) AS running_total
FROM daily;
```

### Change vs previous (day-over-day)
```sql
SELECT day, value,
       value - LAG(value) OVER (ORDER BY day) AS diff,
       ROUND(100.0 * (value - LAG(value) OVER (ORDER BY day))
             / NULLIF(LAG(value) OVER (ORDER BY day), 0), 2) AS pct_change
FROM daily;
```

### Dedupe: giữ bản ghi mới nhất
```sql
WITH t AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS rn
  FROM raw_table
)
SELECT * FROM t WHERE rn = 1;
```

### Gaps & islands: chuỗi ngày liên tiếp
```sql
WITH d AS (
  SELECT DISTINCT user_id, event_ts::DATE AS day FROM events
),
g AS (
  SELECT user_id, day,
         day - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY day))::INT AS grp
  FROM d
)
SELECT user_id, MIN(day) AS start_day, MAX(day) AS end_day, COUNT(*) AS streak
FROM g
GROUP BY user_id, grp;
```

### Missing dates (tìm ngày thiếu dữ liệu)
```sql
WITH cal AS (
  SELECT generate_series('2026-01-01'::DATE, '2026-01-31'::DATE, INTERVAL '1 day')::DATE AS day
)
SELECT c.day
FROM cal c
LEFT JOIN solar_readings r ON c.day = r.ts::DATE
WHERE r.ts IS NULL;
```

### Month-over-month retention
```sql
SELECT EXTRACT(MONTH FROM cur.event_date) AS month,
       COUNT(DISTINCT cur.user_id) AS retained_users
FROM user_actions cur
WHERE EXISTS (
  SELECT 1 FROM user_actions prev
  WHERE prev.user_id = cur.user_id
    AND DATE_TRUNC('month', prev.event_date)
        = DATE_TRUNC('month', cur.event_date) - INTERVAL '1 month'
)
GROUP BY 1;
```

---

## 6. Bẫy thường gặp

- [ ] `= NULL` → phải dùng `IS NULL`.
- [ ] `COUNT(col)` bỏ qua NULL; cần đếm dòng thì `COUNT(*)`.
- [ ] `5 / 2 = 2` → nhân `1.0` hoặc cast `NUMERIC`.
- [ ] `ROUND(double, 2)` lỗi trong Postgres → `ROUND(x::NUMERIC, 2)`.
- [ ] Điều kiện bảng phải đặt ở WHERE làm mất tác dụng LEFT JOIN.
- [ ] JOIN 1-nhiều làm SUM bị nhân đôi → aggregate trước rồi mới join.
- [ ] Lọc window function ngay trong WHERE → phải bọc CTE.
- [ ] Đồng hạng: "second highest" thường cần `DENSE_RANK`, không phải `ROW_NUMBER`.
- [ ] `BETWEEN` với timestamp: `'2022-12-31'` chỉ tới 00:00 → dùng `< '2023-01-01'`.
- [ ] Quên `DISTINCT` khi đề nói "unique users".
- [ ] Đề yêu cầu `ORDER BY` / làm tròn → đọc lại phần output trước khi submit.

---

## 7. Khi phỏng vấn

1. Nhắc lại đề + hỏi làm rõ (NULL? trùng? tie xử lý thế nào?).
2. Nói grain và pattern trước khi viết.
3. Viết bằng CTE, đặt tên rõ ràng.
4. Tự chạy tay với 2–3 dòng dữ liệu mẫu.
5. Nói về hiệu năng nếu được hỏi: index, lọc sớm, tránh `SELECT *`, aggregate trước khi join.
