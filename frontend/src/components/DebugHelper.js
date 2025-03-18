import React, { useState } from 'react';
import { Button, Card, Drawer, Space, Typography, Divider } from 'antd';
import { BugOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Text, Paragraph, Title } = Typography;

const DebugHelper = () => {
  const [visible, setVisible] = useState(false);
  const [apiResponses, setApiResponses] = useState({});
  const [loading, setLoading] = useState(false);

  const testApis = async () => {
    setLoading(true);
    const endpoints = [
      'top-sales-volume',
      'top-sales-amount',
      'top-increased',
      'top-decreased',
      'country-distribution',
      'platform-comparison',
      'salesperson-comparison'
    ];

    const responses = {};

    for (const endpoint of endpoints) {
      try {
        const response = await axios.get(`http://localhost:8000/analysis/${endpoint}/`);
        responses[endpoint] = {
          status: response.status,
          data: response.data,
          success: true
        };
      } catch (error) {
        responses[endpoint] = {
          status: error.response?.status || 'Unknown',
          error: error.message,
          success: false
        };
      }
    }

    setApiResponses(responses);
    setLoading(false);
  };

  return (
    <>
      <Button 
        type="dashed" 
        icon={<BugOutlined />} 
        onClick={() => setVisible(true)}
        style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}
      >
        调试工具
      </Button>
      
      <Drawer 
        title="数据看板调试工具" 
        width={600} 
        open={visible}
        onClose={() => setVisible(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button type="primary" onClick={testApis} loading={loading}>
            测试所有API端点
          </Button>
          
          <Divider />
          
          {Object.keys(apiResponses).map(endpoint => (
            <Card 
              key={endpoint} 
              title={`/${endpoint}`} 
              size="small" 
              style={{ marginBottom: 16 }}
              extra={
                <Text type={apiResponses[endpoint].success ? "success" : "danger"}>
                  {apiResponses[endpoint].status}
                </Text>
              }
            >
              {apiResponses[endpoint].success ? (
                <>
                  <Title level={5}>响应数据:</Title>
                  <Paragraph>
                    <pre style={{ maxHeight: 200, overflow: 'auto' }}>
                      {JSON.stringify(apiResponses[endpoint].data, null, 2)}
                    </pre>
                  </Paragraph>
                  <Text type="secondary">
                    数据类型: {Array.isArray(apiResponses[endpoint].data) ? 'Array' : 'Object'}, 
                    长度: {Array.isArray(apiResponses[endpoint].data) ? apiResponses[endpoint].data.length : '不适用'}
                  </Text>
                </>
              ) : (
                <Text type="danger">{apiResponses[endpoint].error}</Text>
              )}
            </Card>
          ))}
        </Space>
      </Drawer>
    </>
  );
};

export default DebugHelper; 