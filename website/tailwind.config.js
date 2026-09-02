/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  // Ứng dụng render trong #root. Neo utility của Tailwind vào #root để chúng
  // thắng reset/preset của Ant Design khi hai bên đụng cùng một thuộc tính,
  // tránh phải rải `!important` thủ công trong JSX.
  important: '#root',
  theme: {
    extend: {},
  },
  plugins: [],
}
