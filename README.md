# WEB_Taixe — Driver Monitoring Admin Web

Admin dashboard cho hệ thống giám sát tài xế, xây dựng bằng React (Vite) + TailwindCSS + Ant Design + Firebase Auth.

## Tech stack

- [React 19](https://react.dev/) + [Vite](https://vite.dev/)
- [TailwindCSS v3](https://tailwindcss.com/)
- [Ant Design](https://ant.design/) + `@ant-design/icons`
- [React Router v7](https://reactrouter.com/) (Protected Routes)
- [Firebase Auth](https://firebase.google.com/docs/auth) (đăng nhập Quản trị viên)

## Cấu trúc thư mục

```
src/
├── assets/          # Hình ảnh, icons, logo
├── components/      # UI components tái sử dụng (Button, Table, Modal...)
├── contexts/        # React Context (AuthContext, useAuth...)
├── layouts/         # Layout chính (Sidebar, Header, DashboardLayout)
├── pages/           # Các màn hình (Login, Dashboard, Drivers, Incidents...)
├── services/        # Cấu hình API, Firebase, WebSocket
├── routes/          # Cấu hình React Router & Protected Routes
├── App.jsx
├── index.css
└── main.jsx
```

## Cấu hình Firebase

1. Vào [Firebase Console](https://console.firebase.google.com/) → project của bạn → **Project settings** → **General** → phần **Your apps** → chọn (hoặc tạo) Web app → copy các giá trị config.
2. Bật **Authentication → Sign-in method → Email/Password**.
3. Copy `.env.example` thành `.env` (file này đã bị `.gitignore`, không commit) và điền giá trị:

```bash
cp .env.example .env
```

```
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

4. Tạo ít nhất 1 tài khoản Quản trị viên trong **Authentication → Users** để đăng nhập thử.

## Scripts

```bash
npm install     # Cài dependencies
npm run dev     # Chạy dev server
npm run build   # Build production
npm run preview # Preview bản build
npm run lint    # Lint với ESLint
npm run format  # Format code với Prettier
```
