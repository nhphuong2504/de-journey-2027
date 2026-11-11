## SQL baseline 2026-11-09
| # | Câu | Kết quả (Đúng / Sai / Bỏ) | Phút | Kẹt ở đâu |
|---|-----|---------------------------|------|-----------|
| 1 | Histogram of Tweets (Easy) | Đúng sau gợi ý | 15 + 9 | Join thừa về `tweets` sau CTE làm nhân dòng; `GROUP BY t.tweet_bucket` sai bảng; thiếu lọc năm 2022; cần gợi ý để gộp tầng 2 trên CTE |
| 2 | Page With No Likes (Easy) | Đúng | ~6 | Không kẹt. Lưu ý: kiểm tra NULL trên khóa join (`pl.page_id`) thay vì cột thường (`liked_date`) |
| 3 | Average Post Hiatus Part 1 (Easy) | Đúng sau gợi ý | 10 + 4 | Quên điều kiện ≥2 bài (HAVING); trừ timestamp ra interval, cần ép `::date` |
| 4 | Second Day Confirmation (Easy) | Đúng | ~7 | Không kẹt. Thói quen: ghi tiền tố bảng cho mọi cột (`e.user_id`, `t.action_date`); cân nhắc DISTINCT |
| 5 | User's Third Transaction (Medium) | Đúng sau gợi ý | 16 + 1 | ORDER BY DESC (đếm từ cuối); dùng RANK thay ROW_NUMBER (hòa hạng làm mất hạng 3) |
| 6 | Top Three Salaries (Medium) | Đúng sau gợi ý | ? | Chọn đúng DENSE_RANK; quên DESC (lấy lương thấp nhất); thiếu ORDER BY đầu ra theo đề; partition theo tên thay vì id |
| 7 | Tweets' Rolling Averages (Medium) | Chưa làm | | Dừng 2026-11-10 21:30, làm tiếp sau |
| 8 | Sending vs. Opening Snaps (Medium) | Chưa làm | | Dừng 2026-11-10 21:30, làm tiếp sau |
| 9 | Supercloud Customer (Medium) | Chưa làm | | Dừng 2026-11-10 21:30, làm tiếp sau |
| 10 | Active User Retention (Hard) | Chưa làm | | Dừng 2026-11-10 21:30, làm tiếp sau |


## Chủ đề yếu
- Aggregation 2 tầng (gộp trên kết quả đã gộp): dùng thẳng CTE, không join lại bảng gốc
- Lọc theo ngày/năm (EXTRACT, khoảng ngày)
- HAVING vs WHERE: điều kiện trên kết quả gộp (COUNT, SUM...) đặt ở HAVING
- Kiểu dữ liệu ngày: timestamp − timestamp = interval; ép `::date` để ra số ngày
- Đọc kỹ điều kiện ẩn trong đề (vd "ít nhất 2 bài")
- Window: chọn ROW_NUMBER / RANK / DENSE_RANK theo cách xử lý hòa; hướng ORDER BY trong OVER
- Đọc yêu cầu sắp xếp đầu ra ở cuối đề; ORDER BY trong OVER() không sắp xếp kết quả
