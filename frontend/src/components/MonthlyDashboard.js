import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Spin, Empty, Select, Typography, Statistic, Divider, Alert, Button, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import ReactMarkdown from 'react-markdown';

const { Title, Text } = Typography;
const { Option } = Select;

const MonthlyDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableMonths, setAvailableMonths] = useState([]);
  const [currentMonth, setCurrentMonth] = useState('');
  const [previousMonth, setPreviousMonth] = useState('');
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false);
  const [aiAnalysisError, setAiAnalysisError] = useState(null);
  const [aiAnalysisResult, setAiAnalysisResult] = useState('');
  const [data, setData] = useState({
    topSalesVolume: [],
    topSalesAmount: [],
    topIncreased: [],
    topDecreased: [],
    countryDistribution: [],
    platformComparison: {},
    salespersonComparison: []
  });

  // 颜色配置
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];
  const COLORS_COUNTRY = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#FF0000'];
  const INCREASE_COLOR = '#00C49F';
  const DECREASE_COLOR = '#FF0000';

  // 格式化数字，可选择是否添加货币符号
  const formatNumber = (num, isCurrency = false) => {
    if (num === undefined || num === null) return 'N/A';
    
    if (isCurrency) {
      // 使用美元符号
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 2,
        minimumFractionDigits: 2
      }).format(num);
    }
    
    if (num >= 1000) {
      return `$${(num/1000).toFixed(1)}k`;
    } else {
      return `$${parseFloat(num).toFixed(2)}`; // 确保小于1000的值保留两位小数并正确解析
    }
  };

  // 加载可用月份
  const loadAvailableMonths = async () => {
    try {
      const response = await axios.get('http://localhost:8000/analysis/available-months/');
      if (response.data && response.data.length > 0) {
        setAvailableMonths(response.data);
        // 默认选择最近两个月
        if (response.data.length >= 2) {
          setCurrentMonth(response.data[0]);
          setPreviousMonth(response.data[1]);
        } else if (response.data.length === 1) {
          setCurrentMonth(response.data[0]);
        }
      }
    } catch (err) {
      console.error('加载月份数据时出错', err);
      setError(`无法加载月份数据: ${err.message}`);
    }
  };

  // 加载所有数据
  const loadAllData = async () => {
    if (!currentMonth) return;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('开始加载月度数据...');
      
      // 创建带有超时的请求配置
      const axiosConfig = {
        timeout: 180000,  // 180秒超时
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      };
      
      // 并行加载所有数据
      const [
        topSalesVolumeRes,
        topSalesAmountRes,
        topIncreasedRes,
        topDecreasedRes,
        countryDistributionRes,
        platformComparisonRes,
        salespersonComparisonRes
      ] = await Promise.all([
        axios.get(`http://localhost:8000/analysis/month-top-sales-volume/?month=${currentMonth}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/month-top-sales-amount/?month=${currentMonth}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/month-top-increased/?current_month=${currentMonth}&previous_month=${previousMonth}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/month-top-decreased/?current_month=${currentMonth}&previous_month=${previousMonth}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/month-country-distribution/?current_month=${currentMonth}&previous_month=${previousMonth}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/month-platform-comparison/?current_month=${currentMonth}&previous_month=${previousMonth}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/month-salesperson-comparison/?current_month=${currentMonth}&previous_month=${previousMonth}`, axiosConfig)
      ]);
      
      // 打印API响应状态
      console.log('月度数据API响应');
      console.log('销量Top10', topSalesVolumeRes.status);
      console.log('销售额Top10', topSalesAmountRes.status);
      
      // 设置状态
      setData({
        topSalesVolume: topSalesVolumeRes.data || [],
        topSalesAmount: topSalesAmountRes.data || [],
        topIncreased: topIncreasedRes.data || [],
        topDecreased: topDecreasedRes.data || [],
        countryDistribution: countryDistributionRes.data || [],
        platformComparison: platformComparisonRes.data || {},
        salespersonComparison: salespersonComparisonRes.data || []
      });
    } catch (err) {
      console.error('加载月度数据时出错', err);
      setError(`加载数据失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    loadAvailableMonths();
  }, []);

  // 月份变化时加载数据
  useEffect(() => {
    if (currentMonth && previousMonth) {
      loadAllData();
    }
  }, [currentMonth, previousMonth]);

  // 月份选择器变化处理
  const handleCurrentMonthChange = (value) => {
    setCurrentMonth(value);
  };

  const handlePreviousMonthChange = (value) => {
    setPreviousMonth(value);
  };

  // 刷新数据
  const handleRefresh = () => {
    loadAllData();
  };

  // 生成AI分析
  const generateAIAnalysis = async () => {
    if (!currentMonth || !previousMonth) {
      setAiAnalysisError('请先选择要对比的月份');
      return;
    }

    setAiAnalysisLoading(true);
    setAiAnalysisError(null);
    
    try {
      // 准备要发送给AI分析服务的数据
      const analysisData = {
        top_sales_amount: data.topSalesAmount,
        top_increased: data.topIncreased,
        top_decreased: data.topDecreased,
        country_distribution: data.countryDistribution,
        platform_comparison: data.platformComparison,
        salesperson_comparison: data.salespersonComparison
      };
      
      const response = await axios.post('http://localhost:8000/analysis/generate-monthly-ai-analysis/', analysisData, {
        timeout: 180000, // 3分钟超时
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      
      if (response.data && response.data.analysis) {
        setAiAnalysisResult(response.data.analysis);
      } else {
        setAiAnalysisError('AI分析生成失败，服务器返回空数据');
      }
    } catch (err) {
      console.error('生成AI分析时出错', err);
      setAiAnalysisError(`AI分析生成失败: ${err.message || '未知错误'}`);
    } finally {
      setAiAnalysisLoading(false);
    }
  };

  // 销量Top10柱状图配置
  const getTopSalesVolumeOption = () => {
    if (!data.topSalesVolume || data.topSalesVolume.length === 0) {
      return { title: { text: '销量Top10' } };
    }

    // 数据准备 - 截断产品名称
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const xData = data.topSalesVolume.map(item => shortenName(item.product_name)).slice(0, 10);
    const yData = data.topSalesVolume.map(item => item.value || 0).slice(0, 10);
    const originalNames = data.topSalesVolume.map(item => item.product_name).slice(0, 10);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          // 显示完整产品名称
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>销量: ${params[0].value}`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: { type: 'value' },
      series: [{
        name: '销量',
        type: 'bar',
        data: yData,
        itemStyle: {
          color: function(params) {
            return COLORS[params.dataIndex % COLORS.length];
          }
        },
        label: {
          show: true,
          position: 'top'
        }
      }]
    };
  };

  // 销售额Top10柱状图配置
  const getTopSalesAmountOption = () => {
    if (!data.topSalesAmount || data.topSalesAmount.length === 0) {
      return { title: { text: '销售额Top10' } };
    }

    // 数据准备 - 截断产品名称
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const xData = data.topSalesAmount.map(item => shortenName(item.product_name)).slice(0, 10);
    const yData = data.topSalesAmount.map(item => item.value || 0).slice(0, 10);
    const originalNames = data.topSalesAmount.map(item => item.product_name).slice(0, 10);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          // 显示完整产品名称和格式化金额
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>销售额: ${formatNumber(params[0].value, true)}`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: { type: 'value' },
      series: [{
        name: '销售额',
        type: 'bar',
        data: yData,
        itemStyle: {
          color: function(params) {
            return COLORS[params.dataIndex % COLORS.length];
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: function(params) {
            return formatNumber(params.value);
          }
        }
      }]
    };
  };

  // 环比销量上升Top10柱状图配置
  const getTopIncreasedOption = () => {
    if (!data.topIncreased || data.topIncreased.length === 0) {
      return { title: { text: '环比销售额上升Top10' } };
    }

    // 数据准备 - 截断产品名称
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const xData = data.topIncreased.map(item => shortenName(item.product_name)).slice(0, 10);
    const yData = data.topIncreased.map(item => item.amount_change || 0).slice(0, 10);
    const changeRates = data.topIncreased.map(item => item.change_rate || 0).slice(0, 10);
    const originalNames = data.topIncreased.map(item => item.product_name).slice(0, 10);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          // 显示完整产品名称和环比变化率
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>
                  销售额增长: ${formatNumber(params[0].value, true)}<br/>
                  增长率: ${changeRates[index].toFixed(2)}%`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: { type: 'value' },
      series: [{
        name: '销售额增长',
        type: 'bar',
        data: yData,
        itemStyle: {
          color: INCREASE_COLOR
        },
        label: {
          show: true,
          position: 'top',
          formatter: function(params) {
            const index = params.dataIndex;
            return `+${formatNumber(params.value)}`;
          }
        }
      }]
    };
  };

  // 环比销量下降Top10柱状图配置
  const getTopDecreasedOption = () => {
    if (!data.topDecreased || data.topDecreased.length === 0) {
      return { title: { text: '环比销售额下降Top10' } };
    }

    // 数据准备 - 截断产品名称
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const xData = data.topDecreased.map(item => shortenName(item.product_name)).slice(0, 10);
    const yData = data.topDecreased.map(item => item.amount_change || 0).slice(0, 10);
    const changeRates = data.topDecreased.map(item => item.change_rate || 0).slice(0, 10);
    const originalNames = data.topDecreased.map(item => item.product_name).slice(0, 10);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          // 显示完整产品名称和环比变化率
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>
                  销售额下降: ${formatNumber(params[0].value, true)}<br/>
                  下降率: ${Math.abs(changeRates[index]).toFixed(2)}%`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: { type: 'value' },
      series: [{
        name: '销售额下降',
        type: 'bar',
        data: yData,
        itemStyle: {
          color: DECREASE_COLOR
        },
        label: {
          show: true,
          position: 'top',
          formatter: function(params) {
            const index = params.dataIndex;
            return `${formatNumber(params.value)}`;
          }
        }
      }]
    };
  };

  // 国家销售额分布饼图配置
  const getCountryPieOption = () => {
    if (!data.countryDistribution || data.countryDistribution.length === 0) {
      return { title: { text: '国家销售额分布' } };
    }

    const pieData = data.countryDistribution.map(item => ({
      name: item.country || '未知',
      value: item.value || 0
    }));

    return {
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          return `${params.name}: ${formatNumber(params.value, true)} (${params.percent}%)`;
        }
      },
      legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 10,
        top: 20,
        bottom: 20,
      },
      series: [
        {
          name: '国家销售额',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 18,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: pieData
        }
      ]
    };
  };

  // 国家销售额环比柱状图配置
  const getCountryGrowthOption = () => {
    if (!data.countryDistribution || data.countryDistribution.length === 0) {
      return { title: { text: '国家销售额环比' } };
    }

    // 只展示前10个国家
    const countries = data.countryDistribution.slice(0, 10).map(item => item.country || '未知');
    const growth = data.countryDistribution.slice(0, 10).map(item => item.change_rate || 0);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '8%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      yAxis: {
        type: 'category',
        data: countries,
      },
      series: [
        {
          name: '环比增长',
          type: 'bar',
          data: growth,
          label: {
            show: true,
            position: 'right',
            formatter: '{c}%'
          },
          itemStyle: {
            color: function(params) {
              return params.value >= 0 ? INCREASE_COLOR : DECREASE_COLOR;
            }
          }
        }
      ]
    };
  };

  // 销量Top10表格配置
  const salesVolumeColumns = [
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 100
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: '销量',
      dataIndex: 'value',
      key: 'value',
      render: (val) => Math.round(val || 0),
      width: 100
    }
  ];

  // 销售额Top10表格配置
  const salesAmountColumns = [
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 100
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: '销售额',
      dataIndex: 'value',
      key: 'value',
      render: (val) => formatNumber(val, true),
      width: 120
    }
  ];

  // 平台环比对比雷达图配置
  const getPlatformRadarOption = () => {
    if (!data.platformComparison || !data.platformComparison.platforms) {
      return { title: { text: '平台销售数据环比' } };
    }

    const platforms = data.platformComparison.platforms || [];
    const indicators = [
      { name: '销售额', max: 100 },
      { name: '销量', max: 100 },
      { name: '订单数', max: 100 },
      { name: '毛利率', max: 100 }
    ];

    let radarData = [];
    
    // 计算环比变化率
    platforms.forEach(platform => {
      const current = data.platformComparison.current[platform] || {};
      const previous = data.platformComparison.previous[platform] || {};
      
      // 获取当前和上月数据
      const currentSalesAmount = current.sales_amount || 0;
      const previousSalesAmount = previous.sales_amount || 0;
      
      const currentSalesVolume = current.sales_volume || 0;
      const previousSalesVolume = previous.sales_volume || 0;
      
      const currentOrderCount = current.order_count || 0;
      const previousOrderCount = previous.order_count || 0;
      
      const currentProfitRate = current.profit_rate || 0;
      const previousProfitRate = previous.profit_rate || 0;
      
      // 计算环比变化率
      let salesAmountChange = 0;
      if (previousSalesAmount > 0) {
        salesAmountChange = ((currentSalesAmount - previousSalesAmount) / previousSalesAmount) * 100;
      }
      
      let salesVolumeChange = 0;
      if (previousSalesVolume > 0) {
        salesVolumeChange = ((currentSalesVolume - previousSalesVolume) / previousSalesVolume) * 100;
      }
      
      let orderCountChange = 0;
      if (previousOrderCount > 0) {
        orderCountChange = ((currentOrderCount - previousOrderCount) / previousOrderCount) * 100;
      }
      
      let profitRateChange = currentProfitRate - previousProfitRate;
      
      // 加入雷达图数据
      radarData.push({
        value: [
          salesAmountChange,
          salesVolumeChange,
          orderCountChange,
          profitRateChange
        ],
        name: platform
      });
    });

    return {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        type: 'scroll',
        bottom: 0
      },
      radar: {
        indicator: indicators,
        splitArea: {
          areaStyle: {
            color: ['rgba(114, 172, 209, 0.2)',
              'rgba(114, 172, 209, 0.4)',
              'rgba(114, 172, 209, 0.6)',
              'rgba(114, 172, 209, 0.8)',
              'rgba(114, 172, 209, 1)'],
            shadowColor: 'rgba(0, 0, 0, 0.2)',
            shadowBlur: 10
          }
        }
      },
      series: [{
        name: '平台环比',
        type: 'radar',
        data: radarData
      }]
    };
  };

  // 销售人员环比对比表格列
  const salespersonColumns = [
    {
      title: '销售',
      dataIndex: 'sales_person',
      key: 'sales_person',
      width: '15%',
      render: (text) => <span style={{ fontWeight: 'bold' }}>{text}</span>
    },
    {
      title: '销售额对比',
      children: [
        {
          title: '当月',
          dataIndex: 'current_amount',
          key: 'current_amount',
          width: '15%',
          render: (value) => <span>{formatNumber(value, true)}</span>
        },
        {
          title: '环比',
          dataIndex: 'amount_change_rate',
          key: 'amount_change_rate',
          width: '10%',
          render: (value) => (
            <span style={{ color: value >= 0 ? INCREASE_COLOR : DECREASE_COLOR }}>
              {value >= 0 ? '+' : ''}{value}%
            </span>
          )
        }
      ]
    },
    {
      title: '销量对比',
      children: [
        {
          title: '当月',
          dataIndex: 'current_volume',
          key: 'current_volume',
          width: '10%',
          render: (value) => <span>{value}</span>
        },
        {
          title: '环比',
          dataIndex: 'volume_change_rate',
          key: 'volume_change_rate',
          width: '10%',
          render: (value) => (
            <span style={{ color: value >= 0 ? INCREASE_COLOR : DECREASE_COLOR }}>
              {value >= 0 ? '+' : ''}{value}%
            </span>
          )
        }
      ]
    },
    {
      title: '订单数对比',
      children: [
        {
          title: '当月',
          dataIndex: 'current_orders',
          key: 'current_orders',
          width: '10%',
          render: (value) => <span>{value}</span>
        },
        {
          title: '环比',
          dataIndex: 'orders_change_rate',
          key: 'orders_change_rate',
          width: '10%',
          render: (value) => (
            <span style={{ color: value >= 0 ? INCREASE_COLOR : DECREASE_COLOR }}>
              {value >= 0 ? '+' : ''}{value}%
            </span>
          )
        }
      ]
    },
    {
      title: '毛利率对比',
      children: [
        {
          title: '当月',
          dataIndex: 'current_profit_rate',
          key: 'current_profit_rate',
          width: '10%',
          render: (value) => <span>{value}%</span>
        },
        {
          title: '环比',
          dataIndex: 'profit_rate_change',
          key: 'profit_rate_change',
          width: '10%',
          render: (value) => (
            <span style={{ color: value >= 0 ? INCREASE_COLOR : DECREASE_COLOR }}>
              {value >= 0 ? '+' : ''}{value}%
            </span>
          )
        }
      ]
    }
  ];

  // 渲染UI
  return (
    <div className="monthly-dashboard">
      <div style={{ padding: '20px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col span={6}>
            <Title level={2}>月度数据看板</Title>
          </Col>
          <Col span={12}>
            <Row gutter={16}>
              <Col span={10}>
                <Select
                  placeholder="选择当前月"
                  style={{ width: '100%' }}
                  value={currentMonth}
                  onChange={handleCurrentMonthChange}
                >
                  {availableMonths.map(month => (
                    <Option key={month} value={month}>{month}</Option>
                  ))}
                </Select>
              </Col>
              <Col span={10}>
                <Select
                  placeholder="选择上一月"
                  style={{ width: '100%' }}
                  value={previousMonth}
                  onChange={handlePreviousMonthChange}
                >
                  {availableMonths.map(month => (
                    <Option key={month} value={month}>{month}</Option>
                  ))}
                </Select>
              </Col>
              <Col span={4}>
                <Button 
                  type="primary" 
                  icon={<ReloadOutlined />} 
                  onClick={handleRefresh}
                  disabled={!currentMonth || !previousMonth}
                >
                  刷新
                </Button>
              </Col>
            </Row>
          </Col>
        </Row>

        {error && (
          <Alert
            message="数据加载错误"
            description={error}
            type="error"
            closable
            style={{ marginTop: 16, marginBottom: 16 }}
          />
        )}

        <Spin spinning={loading} tip="加载数据中...">
          {/* 数据可视化部分 */}
          <div className="dashboard-content" style={{ marginTop: 24 }}>
            {/* 行1：销量Top10和销售额Top10 */}
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="月度商品销量Top10">
                  {data.topSalesVolume && data.topSalesVolume.length > 0 ? (
                    <>
                      <ReactECharts option={getTopSalesVolumeOption()} style={{ height: 300 }} />
                      <div style={{ marginTop: 16 }}>
                        <Table
                          dataSource={data.topSalesVolume}
                          columns={salesVolumeColumns}
                          pagination={false}
                          size="small"
                          rowKey={(record, index) => `sales-volume-${index}`}
                        />
                      </div>
                    </>
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="月度商品销售额Top10">
                  {data.topSalesAmount && data.topSalesAmount.length > 0 ? (
                    <>
                      <ReactECharts option={getTopSalesAmountOption()} style={{ height: 300 }} />
                      <div style={{ marginTop: 16 }}>
                        <Table
                          dataSource={data.topSalesAmount}
                          columns={salesAmountColumns}
                          pagination={false}
                          size="small"
                          rowKey={(record, index) => `sales-amount-${index}`}
                        />
                      </div>
                    </>
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
            </Row>

            {/* 行2：环比销售额上升和下降Top10 */}
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Card title="月度环比销售额上升Top10">
                  {data.topIncreased && data.topIncreased.length > 0 ? (
                    <ReactECharts option={getTopIncreasedOption()} style={{ height: 400 }} />
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="月度环比销售额下降Top10">
                  {data.topDecreased && data.topDecreased.length > 0 ? (
                    <ReactECharts option={getTopDecreasedOption()} style={{ height: 400 }} />
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
            </Row>

            {/* 行3：国家销售额分布和环比 */}
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Card title="月度国家销售额分布">
                  {data.countryDistribution && data.countryDistribution.length > 0 ? (
                    <ReactECharts option={getCountryPieOption()} style={{ height: 400 }} />
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="月度国家销售额环比">
                  {data.countryDistribution && data.countryDistribution.length > 0 ? (
                    <ReactECharts option={getCountryGrowthOption()} style={{ height: 400 }} />
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
            </Row>

            {/* 行4：平台销售数据环比 */}
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={24}>
                <Card title="平台月度销售数据环比">
                  {data.platformComparison && data.platformComparison.platforms && data.platformComparison.platforms.length > 0 ? (
                    <ReactECharts option={getPlatformRadarOption()} style={{ height: 400 }} />
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
            </Row>

            {/* 行5：销售人员数据表格 */}
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={24}>
                <Card title="销售人员月度数据对比">
                  {data.salespersonComparison && data.salespersonComparison.length > 0 ? (
                    <Table
                      columns={salespersonColumns}
                      dataSource={data.salespersonComparison.map((item, index) => ({ ...item, key: index }))}
                      bordered
                      pagination={false}
                      scroll={{ x: 1200 }}
                      size="small"
                    />
                  ) : (
                    <Empty description="暂无数据" />
                  )}
                </Card>
              </Col>
            </Row>

            {/* 行6：AI分析报告 */}
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={24}>
                <Card 
                  title="AI月度销售数据分析" 
                  extra={
                    <Button 
                      type="primary" 
                      onClick={generateAIAnalysis} 
                      loading={aiAnalysisLoading}
                      disabled={loading || !currentMonth || !previousMonth}
                    >
                      生成AI分析
                    </Button>
                  }
                >
                  {aiAnalysisError && (
                    <Alert
                      message="AI分析生成错误"
                      description={aiAnalysisError}
                      type="error"
                      closable
                      style={{ marginBottom: 16 }}
                    />
                  )}
                  
                  {aiAnalysisLoading ? (
                    <div style={{ textAlign: 'center', padding: '40px 0' }}>
                      <Spin tip="正在生成AI分析，这可能需要一些时间..." />
                    </div>
                  ) : aiAnalysisResult ? (
                    <div 
                      className="markdown-content" 
                      style={{
                        padding: '0 16px',
                        maxHeight: '600px',
                        overflow: 'auto'
                      }}
                    >
                      <ReactMarkdown>
                        {aiAnalysisResult}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <Empty 
                      description={
                        <span>
                          点击"生成AI分析"按钮，获取基于当前数据的智能分析报告
                        </span>
                      }
                    />
                  )}
                </Card>
              </Col>
            </Row>
          </div>
        </Spin>

        {/* 添加markdown内容的样式 */}
        <style jsx="true">{`
          .markdown-content h1 {
            font-size: 1.8em;
            margin-top: 1em;
            margin-bottom: 0.5em;
          }
          .markdown-content h2 {
            font-size: 1.5em;
            margin-top: 0.8em;
            margin-bottom: 0.4em;
          }
          .markdown-content h3 {
            font-size: 1.2em;
            margin-top: 0.6em;
            margin-bottom: 0.3em;
          }
          .markdown-content p {
            margin-bottom: 0.8em;
            line-height: 1.6;
          }
          .markdown-content ul, .markdown-content ol {
            margin-left: 2em;
            margin-bottom: 1em;
          }
          .markdown-content strong {
            font-weight: 600;
            color: #1890ff;
          }
        `}</style>
      </div>
    </div>
  );
};

export default MonthlyDashboard; 