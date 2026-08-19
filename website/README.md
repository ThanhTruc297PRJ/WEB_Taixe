# WEB_Taixe — Driver Monitoring Admin Web

Admin dashboard cho hệ thống giám sát tài xế, xây dựng bằng React (Vite) + TailwindCSS + Ant Design.

## Tech stack

- [React 19](https://react.dev/) + [Vite](https://vite.dev/)
- [TailwindCSS v3](https://tailwindcss.com/)
- [Ant Design](https://ant.design/) + `@ant-design/icons`
- [React Router v7](https://reactrouter.com/) (Protected Routes)

## Cấu trúc thư mục

```
src/
├── assets/          # Hình ảnh, icons, logo
├── components/      # UI components tái sử dụng (Button, Table, Modal...)
├── layouts/         # Layout chính (Sidebar, Header, DashboardLayout)
├── pages/           # Các màn hình (Login, Dashboard, Drivers, Incidents...)
├── services/        # Cấu hình API, Firebase, WebSocket
├── routes/          # Cấu hình React Router & Protected Routes
├── App.jsx
├── index.css
└── main.jsx
```

## Scripts

```bash
npm install     # Cài dependencies
npm run dev     # Chạy dev server
npm run build   # Build production
npm run preview # Preview bản build
npm run lint    # Lint với ESLint
npm run format  # Format code với Prettier
```
