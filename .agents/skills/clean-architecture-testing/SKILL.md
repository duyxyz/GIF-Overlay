---
name: Clean Architecture & Testing
description: Quy định nghiêm ngặt về phân tách logic, kiến trúc sạch và bắt buộc kiểm thử cho mọi tính năng.
---

# Clean Architecture & Testing Standard (Web & App)

## 1. Logic Separation (Phân tách Logic)
- **Presentation Layer (Giao diện)**: 
    - **Web**: Components (React/Vue/HTML).
    - **App**: Mobile Screens/Widgets (React Native, Flutter, Swift/Kotlin).
    - Chỉ chứa logic hiển thị. Không chứa logic nghiệp vụ hoặc gọi API trực tiếp.
- **Domain Layer (Nghiệp vụ)**: Chứa các Business Logic, Entities, và Use Cases độc lập với nền tảng.
- **Data Layer (Dữ liệu)**: Quản lý API, Caching (LocalStorage/SQLite), và Repositories.

## 2. State Management
- **Web**: Dùng **Zustand** cho trạng thái đơn giản/vừa. Dùng **Redux Toolkit** khi state phức tạp, cần time-travel debug hoặc nhiều slice liên kết nhau.
- **Mobile (Flutter)**: Dùng **Provider** cho scope nhỏ. Dùng **BLoC** khi cần tách biệt Event/State rõ ràng và testable.
- **Quy tắc chung**: State toàn cục chỉ lưu dữ liệu thực sự cần share. State cục bộ (UI state) phải nằm trong component/widget, không đưa lên global store.

## 3. Naming Conventions (Quy chuẩn đặt tên)
- **Web/App Files**: Sử dụng `kebab-case` hoặc theo chuẩn riêng của nền tảng (ví dụ: PascalCase cho Component).
- **Suffixes**:
    - `*.component.*`, `*.screen.*`, `*.widget.*`: Cho thành phần giao diện.
    - `*.service.*`, `*.usecase.*`: Cho logic nghiệp vụ.
    - `*.test.*`: Cho Unit Test.
- **Platform Agnostic**: Ưu tiên đặt tên file phản ánh chức năng hơn là công nghệ (ví dụ: `auth.service.ts` thay vì `auth.axios.ts`).

## 4. Folder Structure
```
# Web (React/Next.js)
src/
  components/      # UI thuần túy, tái sử dụng
  features/        # Mỗi feature có components, services, hooks riêng
  services/        # Business logic, API calls
  store/           # State management
  types/           # TypeScript types/interfaces

# Mobile (Flutter)
lib/
  features/        # Mỗi feature có presentation, domain, data
    auth/
      presentation/ # Screens, Widgets
      domain/       # UseCases, Entities
      data/         # Repositories, Models
  shared/          # Widget dùng chung
  core/            # Config, constants, themes
```

## 5. Testing Requirements (Yêu cầu kiểm thử)
- **Unit Testing (Universal)**: Sử dụng **Jest** hoặc framework mặc định của nền tảng (ví dụ: `flutter_test`). Bắt buộc cho Domain Layer.
- **UI/Integration Testing**:
    - **Web**: React Testing Library, Playwright.
    - **App**: Interaction tests, Widget tests.
- **End-to-End (E2E) Testing**:
    - **Web**: Cypress, Playwright.
    - **App**: Maestro, Appium hoặc công cụ native tương đương.

## 6. Platform Optimization
- **Responsive (Web)**: Luôn kiểm tra Mobile-first design.
- **Performance (App)**: Kiểm tra memory leaks, tối ưu hóa kích thước bundle/binary.
- **Offline-first**: Thiết kế lớp Data để hỗ trợ caching và hoạt động offline khi cần thiết.

## 7. Error Handling (Xử lý lỗi)
- Không sử dụng `console.log` để log lỗi trong sản phẩm thực tế.
- Sử dụng cấu trúc `try/catch` có mục đích, kèm theo thông báo thân thiện cho người dùng và log chi tiết cho hệ thống (ví dụ: Sentry).
- Luôn định nghĩa các Error Class riêng cho các lỗi nghiệp vụ đặc thù.

## 8. Workflow
- Trước khi hoàn thành một yêu cầu, Agent phải kiểm tra xem đã có tệp test tương ứng chưa. Nếu chưa có, **chỉ đề xuất** tạo test ở cuối câu trả lời — không tự tạo khi chưa được yêu cầu.
- Tuyệt đối không xóa bỏ các tệp test cũ trừ khi logic tương ứng bị loại bỏ.
