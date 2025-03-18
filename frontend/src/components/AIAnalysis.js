import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, Spin, Result, Divider, Alert } from 'antd';
import { RobotOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const { Title, Paragraph, Text } = Typography;

const AIAnalysis = ({ top_sales, top_increased, top_decreased, country_distribution, platform_comparison }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 准备发送给AI分析接口的数据
      const analysisData = {
        top_sales_amount: top_sales || [],
        top_increased: top_increased || [],
        top_decreased: top_decreased || [],
        country_distribution: country_distribution || [],
        platform_comparison: platform_comparison || {}
      };
      
      console.log("发送AI分析请求，数据:", analysisData);
      
      const response = await axios.post(
        'http://localhost:8000/ai/generate-analysis/',
        analysisData,
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 100000 // 100秒超时
        }
      );
      
      console.log("AI分析响应:", response.data);
      setAnalysis(response.data.analysis || '无法生成分析内容');
    } catch (err) {
      console.error("AI分析生成失败:", err);
      setError(`生成分析失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 当数据变化时重新生成分析
  useEffect(() => {
    if (top_sales && top_sales.length > 0) {
      generateAnalysis();
    }
  }, [top_sales, top_increased, top_decreased, country_distribution, platform_comparison]);

  return (
    <Card 
      title={<Title level={4}><RobotOutlined /> AI智能分析</Title>}
      extra={
        <Button 
          icon={<ReloadOutlined />} 
          onClick={generateAnalysis} 
          loading={loading}
          disabled={loading}
        >
          重新生成
        </Button>
      }
      className="analysis-card"
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '30px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '10px' }}>AI正在分析数据，请稍候...</div>
        </div>
      ) : error ? (
        <Alert type="error" message="分析生成失败" description={error} />
      ) : analysis ? (
        <div className="markdown-container">
          <ReactMarkdown>{analysis}</ReactMarkdown>
        </div>
      ) : (
        <Result
          icon={<RobotOutlined />}
          title="尚未生成分析"
          subTitle="请上传销售数据后自动生成分析"
        />
      )}
    </Card>
  );
};

export default AIAnalysis; 