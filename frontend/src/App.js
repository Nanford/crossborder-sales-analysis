import React from 'react';
import { Layout, Menu, theme } from 'antd';
import { DatabaseOutlined, LineChartOutlined, UploadOutlined } from '@ant-design/icons';
import { BrowserRouter as Router, Route, Routes, Link, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DataImport from './components/DataImport';
import DebugHelper from './components/DebugHelper';

const { Header, Content, Footer, Sider } = Layout;

const App = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider breakpoint="lg" collapsedWidth="0">
          <div className="demo-logo-vertical" />
          <Menu
            theme="dark"
            mode="inline"
            defaultSelectedKeys={['1']}
            items={[
              {
                key: '1',
                icon: <LineChartOutlined />,
                label: <Link to="/dashboard">数据看板</Link>,
              },
              {
                key: '2',
                icon: <UploadOutlined />,
                label: <Link to="/import">数据导入</Link>,
              },
            ]}
          />
        </Sider>
        <Layout>
          <Header style={{ padding: 0, background: colorBgContainer }} />
          <Content style={{ margin: '24px 16px 0' }}>
            <div
              style={{
                padding: 24,
                minHeight: 360,
                background: colorBgContainer,
                borderRadius: borderRadiusLG,
              }}
            >
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/import" element={<DataImport />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          </Content>
          <Footer style={{ textAlign: 'center' }}>
            跨境电商销售数据分析系统 ©{new Date().getFullYear()}
          </Footer>
        </Layout>
      </Layout>
      <DebugHelper />
    </Router>
  );
};

export default App; 