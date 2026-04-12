---
name: Code Quality & Debugging Excellence
description: Quy chuẩn về kiểm soát mã nguồn, log lỗi và các checklist để tìm diệt bug nhanh nhất.
---

# Code Quality & Debugging Standard

## 1. Traceability (Khả năng truy vết)
- **Conventional Commits**: Luôn sử dụng tiền tố (feat, fix, refactor, chore) trong commit message để dễ dàng tra cứu lịch sử thay đổi.
- **Self-Documenting Code**: Ưu tiên đặt tên hàm/biến cực kỳ rõ ràng thay vì viết comment giải thích. Nếu một đoạn code cần comment, hãy cân nhắc refactor nó trước.
- **Git Blame Friendly**: Không gộp quá nhiều thay đổi không liên quan vào một commit. Tách nhỏ các thay đổi để dễ dàng "blame" và hoàn tác khi có lỗi.

## 2. Structured Logging & Monitoring (Ghi log & Giám sát)
- **Log Levels**: Sử dụng đúng cấp độ log (DEBUG, INFO, WARN, ERROR). Không dùng `console.log` thuần túy trong môi trường production.
- **Contextual Data**: Khi log lỗi, LUÔN đính kèm các dữ liệu ngữ cảnh (ví dụ: `userId`, `action`, `payload`) nhưng phải bảo mật thông tin nhạy cảm.
- **Trace IDs**: Đảm bảo log có gắn ID phiên làm việc hoặc ID yêu cầu để theo dõi toàn bộ luồng của một lỗi duy nhất.
- **Error Monitoring**: Tích hợp Sentry (Web/App) ngay từ đầu. Bọc các khối mã quan trọng trong `Error Boundaries` (React) hoặc `Catch All` handlers để tránh crash toàn bộ ứng dụng.

## 3. Defensive Programming (Lập trình phòng vệ)
- **Input Validation**: Luôn kiểm tra tính hợp lệ của dữ liệu đầu vào (Zod, Joi, hoặc logic thủ công) trước khi xử lý.
- **Fail Fast**: Thiết kế hệ thống để lỗi xảy ra ngay lập tức tại điểm có vấn đề, thay vì để nó lan truyền sang các module khác.
- **Default States**: Luôn định nghĩa trạng thái mặc định an toàn cho UI và dữ liệu để tránh lỗi "undefined" hoặc "null".

## 4. Debugging Checklist for Agent
Mỗi khi gặp bug hoặc viết code mới, Agent phải tự hỏi:
1. "Nếu đoạn code này lỗi ở máy khách hàng, tôi có đủ log để biết tại sao không?"
2. "Tôi đã kiểm tra dữ liệu đầu vào là null hoặc undefined chưa?"
3. "Hàm này có đang xử lý quá nhiều trách nhiệm không?" (Phải tuân thủ Single Responsibility Principle).
4. "Tôi đã có Unit Test cho trường hợp lỗi (Edge Case) này chưa?"
## 5. Code Review Checklist
Trước khi đưa code ra, Agent phải tự kiểm tra:
- [ ] Code có đang vi phạm Single Responsibility Principle không?
- [ ] Có giá trị `null`/`undefined` nào chưa được xử lý không?
- [ ] Có magic number hay hard-coded string nào cần đưa vào constant không?
- [ ] Tên hàm/biến có mô tả đúng chức năng không?
- [ ] Có đoạn code nào lặp lại (DRY violation) cần refactor không?
- [ ] Có dependency nào được thêm vào mà chưa được yêu cầu không?

## 6. Performance Profiling
- **Khi nào cần lo**: Khi thao tác mất > 300ms (Web) hoặc gây drop frame (App), khi list/table render > 100 item, khi có vòng lặp lồng nhau trên tập dữ liệu lớn.
- **Web**: Dùng Chrome DevTools (Performance tab, Lighthouse) để đo. Ưu tiên `useMemo`/`useCallback` khi re-render thực sự là vấn đề.
- **Mobile (Flutter)**: Dùng Flutter DevTools (Widget Rebuild tracker). Tránh `setState` ở widget cha khi chỉ cần rebuild widget con.
- **Quy tắc vàng**: Đừng tối ưu sớm — đo trước, tối ưu sau khi có bằng chứng rõ ràng.
