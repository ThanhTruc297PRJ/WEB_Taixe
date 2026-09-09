// Theme dùng chung cho toàn web admin (ConfigProvider của Ant Design).
// Tông "xanh dương chuyên nghiệp": brand indigo, bo góc mềm, nền xám nhạt,
// sidebar tối. Đổi màu ở đây là đổi toàn hệ thống.

export const BRAND = {
  primary: '#2563EB', // indigo-600
  primaryHover: '#1D4ED8',
  sider: '#0F172A', // slate-900
  siderActive: '#1E293B', // slate-800
}

const theme = {
  token: {
    colorPrimary: BRAND.primary,
    colorInfo: BRAND.primary,
    colorBgLayout: '#F1F5F9', // slate-100
    borderRadius: 10,
    fontFamily:
      "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif",
    fontSize: 14,
    wireframe: false,
  },
  components: {
    Layout: {
      siderBg: BRAND.sider,
      headerBg: '#FFFFFF',
      headerHeight: 60,
      headerPadding: '0 24px',
      bodyBg: '#F1F5F9',
    },
    Menu: {
      darkItemBg: BRAND.sider,
      darkSubMenuItemBg: BRAND.sider,
      darkItemSelectedBg: BRAND.primary,
      darkItemHoverBg: BRAND.siderActive,
      darkItemColor: '#94A3B8', // slate-400
      darkItemSelectedColor: '#FFFFFF',
      itemHeight: 42,
      itemMarginInline: 10,
      itemBorderRadius: 8,
    },
    Card: {
      borderRadiusLG: 14,
      paddingLG: 20,
    },
    Table: {
      headerBg: '#F8FAFC',
      headerColor: '#475569',
      rowHoverBg: '#F1F5F9',
      borderColor: '#E2E8F0',
      cellPaddingBlock: 14,
    },
    Button: {
      controlHeight: 36,
      fontWeight: 500,
      primaryShadow: 'none',
      defaultShadow: 'none',
    },
    Segmented: {
      trackBg: '#E2E8F0',
      itemSelectedBg: '#FFFFFF',
    },
    Statistic: {
      contentFontSize: 26,
    },
  },
}

export default theme
