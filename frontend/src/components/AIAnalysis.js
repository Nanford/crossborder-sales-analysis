import React, { useState } from 'react';
import { Button, Typography, Spin, Result, Alert } from 'antd';
import { RobotOutlined, LineChartOutlined } from '@ant-design/icons';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const { Title } = Typography;


const AIAnalysis = ({ top_sales, top_increased, top_decreased, country_distribution, platform_comparison, salesperson_comparison }) => {
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
        platform_comparison: platform_comparison || {},
        salesperson_comparison: salesperson_comparison || []
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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4}><RobotOutlined /> AI智能分析</Title>
        <Button 
          type="primary"
          icon={<LineChartOutlined />}
          onClick={generateAnalysis}
          loading={loading}
          disabled={loading || !top_sales || top_sales.length === 0}
        >
          {analysis ? '重新生成分析' : '生成分析报告'}
        </Button>
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '30px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '10px' }}>AI正在分析数据，请稍候...</div>
        </div>
      ) : error ? (
        <Alert 
          type="error" 
          message="分析生成失败" 
          description={error}
          action={
            <Button size="small" danger onClick={generateAnalysis}>
              重试
            </Button>
          }
        />
      ) : analysis ? (
        <div className="markdown-content">
          <ReactMarkdown>
            {analysis}
          </ReactMarkdown>
        </div>
      ) : (
        <Result
          icon={<RobotOutlined />}
          title="等待生成分析"
          subTitle="点击上方按钮开始生成AI分析报告"
        />
      )}
    </div>
  );
};

// 添加样式
const styles = `
  .markdown-content {
    padding: 16px;
    font-size: 14px;
    line-height: 1.6;
  }
  
  .markdown-content h1 {
    font-size: 24px;
    font-weight: bold;
    margin: 20px 0;
  }
  
  .markdown-content h2 {
    font-size: 20px;
    font-weight: bold;
    margin: 16px 0;
  }
  
  .markdown-content h3 {
    font-size: 18px;
    font-weight: bold;
    margin: 14px 0;
  }
  
  .markdown-content p {
    margin: 12px 0;
    line-height: 1.6;
  }
  
  .markdown-content ul {
    margin: 12px 0;
    padding-left: 20px;
  }
  
  .markdown-content li {
    margin: 6px 0;
  }
  
  .markdown-content strong {
    color: #1890ff;
    font-weight: bold;
  }
`;

// 将样式添加到文档中
const styleSheet = document.createElement("style");
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default AIAnalysis; 