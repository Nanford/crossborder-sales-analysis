import React, { useState } from 'react';
import { Upload, Button, message, Alert, Card, Typography, Spin } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Dragger } = Upload;
const { Title, Paragraph } = Typography;

const DataImport = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const props = {
    name: 'file',
    multiple: false,
    action: 'http://localhost:8000/upload/',
    accept: '.xlsx,.xls,.csv',
    onChange(info) {
      const { status } = info.file;
      
      if (status === 'uploading') {
        setUploading(true);
        setUploadResult(null);
      }
      
      if (status === 'done') {
        setUploading(false);
        message.success(`${info.file.name} 文件上传成功`);
        setUploadResult({
          success: true,
          message: info.file.response.message
        });
      } else if (status === 'error') {
        setUploading(false);
        message.error(`${info.file.name} 文件上传失败`);
        setUploadResult({
          success: false,
          message: info.file.response?.detail || '上传失败，请重试'
        });
      }
    },
    customRequest({ file, onSuccess, onError }) {
      const formData = new FormData();
      formData.append('file', file);
      
      axios
        .post('http://localhost:8000/upload/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then(response => {
          onSuccess(response.data, file);
        })
        .catch(error => {
          console.error('上传文件失败:', error);
          const errorMsg = error.response?.data?.detail || '服务器错误，请检查后端日志';
          message.error(`上传失败: ${errorMsg}`);
          onError({ ...error, message: errorMsg });
        });
    },
  };

  return (
    <div>
      <Title level={2}>数据导入</Title>
      <Paragraph>
        支持上传Excel(.xlsx, .xls)或CSV文件，系统会自动处理和分析数据。
      </Paragraph>
      
      <Card style={{ marginBottom: 16 }}>
        <Dragger {...props} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持Excel和CSV格式的销售数据文件
          </p>
        </Dragger>
        
        {uploading && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Spin>
              <div style={{ padding: '30px', background: 'rgba(0,0,0,0.05)' }}>
                <p>正在上传和处理数据...</p>
              </div>
            </Spin>
          </div>
        )}
        
        {uploadResult && (
          <Alert
            message={uploadResult.success ? "上传成功" : "上传失败"}
            description={uploadResult.message}
            type={uploadResult.success ? "success" : "error"}
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
      
      <Card title="数据格式说明">
        <Paragraph>上传的数据需要包含以下列：</Paragraph>
        <ul>
          <li>sku - 商品SKU编码</li>
          <li>spu - 商品SPU编码</li>
          <li>名称 - 商品名称</li>
          <li>平台 - 销售平台</li>
          <li>店铺 - 销售店铺</li>
          <li>销量 - 商品销量</li>
          <li>销售额 - 商品销售额</li>
          <li>毛利率 - 毛利率</li>
          <li>周 - 数据所属周期（"本周"或"上周"）</li>
        </ul>
        <Paragraph>其他字段也会被处理，但上述字段是必需的。</Paragraph>
      </Card>
    </div>
  );
};

export default DataImport; 