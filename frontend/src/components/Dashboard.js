import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Spin, Empty, Select, Typography, Statistic, Divider, Alert, Button, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import AIAnalysis from './AIAnalysis';

const { Title, Text } = Typography;
const { Option } = Select;

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [weekFilter, setWeekFilter] = useState('all');
  const [data, setData] = useState({
    topSalesVolume: [],
    topSalesAmount: [],
    topIncreased: [],
    topDecreased: [],
    countryDistribution: [],
    platformComparison: {},
    platformDetail: [], // 新增平台详细数据
    salespersonComparison: [],
    platformSalesDistribution: {} // 新增数据
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
    
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 2,
      minimumFractionDigits: 0
    }).format(num);
  };

  // 加载所有数据
  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('开始加载数据...');
      
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
        platformDetailRes,
        salespersonComparisonRes,
        platformSalesDistributionRes // 新增API响应
      ] = await Promise.all([
        axios.get(`http://localhost:8000/analysis/top-sales-volume/?week=${weekFilter === 'all' ? '' : weekFilter}`, axiosConfig),
        axios.get(`http://localhost:8000/analysis/top-sales-amount/?week=${weekFilter === 'all' ? '' : weekFilter}`, axiosConfig),
        axios.get('http://localhost:8000/analysis/top-increased/', axiosConfig),
        axios.get('http://localhost:8000/analysis/top-decreased/', axiosConfig),
        axios.get('http://localhost:8000/analysis/country-distribution/', axiosConfig),
        axios.get('http://localhost:8000/analysis/platform-comparison/', axiosConfig),
        axios.get('http://localhost:8000/analysis/platform-detail/', axiosConfig),
        axios.get('http://localhost:8000/analysis/salesperson-comparison/', axiosConfig),
        axios.get('http://localhost:8000/analysis/platform-sales-distribution/', axiosConfig)
      ]);
      
      // 打印API响应状态和数据结构
      console.log('API响应状态:');
      console.log('销量Top5 状态:', topSalesVolumeRes.status);
      console.log('销售额Top5 状态:', topSalesAmountRes.status);
      
      // 检查API响应内容
      if (Array.isArray(topSalesVolumeRes.data) && topSalesVolumeRes.data.length > 0) {
        console.log('销量Top5示例数据:', topSalesVolumeRes.data[0]);
      } else {
        console.warn('销量Top5 API返回空数据或格式不是数组');
      }
      
      if (Array.isArray(topSalesAmountRes.data) && topSalesAmountRes.data.length > 0) {
        console.log('销售额Top5示例数据:', topSalesAmountRes.data[0]);
      } else {
        console.warn('销售额Top5 API返回空数据或格式不是数组');
      }
      
      // 设置状态
      setData({
        topSalesVolume: topSalesVolumeRes.data || [],
        topSalesAmount: topSalesAmountRes.data || [],
        topIncreased: topIncreasedRes.data || [],
        topDecreased: topDecreasedRes.data || [],
        countryDistribution: countryDistributionRes.data || [],
        platformComparison: platformComparisonRes.data || {},
        platformDetail: platformDetailRes.data || [],
        salespersonComparison: salespersonComparisonRes.data || [],
        platformSalesDistribution: platformSalesDistributionRes.data || {}
      });
    } catch (err) {
      console.error('加载数据时出错:', err);
      setError(`加载数据失败: ${err.message || '未知错误'}`);
      
      // 检查是否有部分数据可用
      if (data.topSalesVolume.length > 0 || data.topSalesAmount.length > 0) {
        console.log('使用已有的部分数据');
      } else {
        // 只在没有任何数据时显示错误信息
        setError(`无法连接到数据源: ${err.message}. 请检查API服务是否运行。`);
      }
    } finally {
      setLoading(false);
    }
  };

  // 页面加载或选择周次变化时加载数据
  useEffect(() => {
    loadAllData();
  }, [weekFilter]);

  // 销量Top5柱状图配置 - 优化X轴标签
  const getTopSalesVolumeOption = () => {
    if (!data.topSalesVolume || data.topSalesVolume.length === 0) {
      return { title: { text: '销量Top5' } };
    }

    // 数据准备 - 截断产品名
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const xData = data.topSalesVolume.map(item => shortenName(item.product_name)).slice(0, 5);
    const yData = data.topSalesVolume.map(item => item.value || 0).slice(0, 5);
    const originalNames = data.topSalesVolume.map(item => item.product_name).slice(0, 5);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          // 显示完整产品名
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>销量: ${formatNumber(params[0].value)}`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%', // 增加底部空间给标签
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          interval: 0,  // 强制显示所有标签
          rotate: 45,   // 增加旋转角度
          fontSize: 10,
          formatter: function(value) {
            // 控制X轴标签显示
            return value;
          }
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

  // 销售额Top5柱状图配置
  const getTopSalesAmountOption = () => {
    if (!data.topSalesAmount || data.topSalesAmount.length === 0) {
      return { title: { text: '销售额Top5' } };
    }

    // 数据准备 - 截断产品名
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const xData = data.topSalesAmount.map(item => shortenName(item.product_name)).slice(0, 5);
    const yData = data.topSalesAmount.map(item => item.value || 0).slice(0, 5);
    const originalNames = data.topSalesAmount.map(item => item.product_name).slice(0, 5);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          // 显示完整产品名
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>销售额: ${formatNumber(params[0].value, true)}`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%', // 增加底部空间给标签
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
      yAxis: { 
        type: 'value',
        axisLabel: {
          formatter: function(value) {
            // 美元简写表示
            if (value >= 1000) {
              return '$' + (value / 1000).toFixed(0) + 'k';
            }
            return '$' + value;
          }
        }
      },
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
            if (params.value >= 1000) {
              return '$' + (params.value / 1000).toFixed(1) + 'k';
            }
            return '$' + params.value;
          }
        }
      }]
    };
  };

  // 环比上升Top5柱状图配置
  const getTopIncreasedOption = () => {
    if (!data.topIncreased || data.topIncreased.length === 0) {
      return { title: { text: '环比上升Top5' } };
    }

    // 截断产品名
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const products = data.topIncreased.map(item => shortenName(item.product_name)).slice(0, 5);
    const rates = data.topIncreased.map(item => item.change_rate || 0).slice(0, 5);
    const originalNames = data.topIncreased.map(item => item.product_name).slice(0, 5);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>增长率: +${params[0].value.toFixed(2)}%`;
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
        data: products,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: { 
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        name: '增长率',
        type: 'bar',
        data: rates,
        itemStyle: {
          color: INCREASE_COLOR
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }]
    };
  };

  // 环比下降Top5柱状图配置
  const getTopDecreasedOption = () => {
    if (!data.topDecreased || data.topDecreased.length === 0) {
      return { title: { text: '环比下降Top5' } };
    }

    // 截断产品名
    const shortenName = (name) => {
      if (!name) return '未知产品';
      return name.length > 10 ? name.substring(0, 10) + '...' : name;
    };
    
    const products = data.topDecreased.map(item => shortenName(item.product_name)).slice(0, 5);
    const rates = data.topDecreased.map(item => Math.abs(item.change_rate) || 0).slice(0, 5);
    const originalNames = data.topDecreased.map(item => item.product_name).slice(0, 5);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const index = params[0].dataIndex;
          return `${originalNames[index]}<br/>下降率: -${params[0].value.toFixed(2)}%`;
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
        data: products,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: { 
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        name: '下降率',
        type: 'bar',
        data: rates,
        itemStyle: {
          color: DECREASE_COLOR
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }]
    };
  };

  // 国家销售分布饼图选项 - 增强显示
  const getCountryPieOption = () => {
    if (!data.countryDistribution || data.countryDistribution.length === 0) {
      return { title: { text: '国家销售分布' } };
    }

    // 数据准备
    const countries = data.countryDistribution.map(item => item.country);
    const salesData = data.countryDistribution.map(item => ({
      name: item.country || '未知',
      value: item.value || 0  // 使用API返回的正确字段名
    }));
    
    // 计算总销售额
    const totalSales = salesData.reduce((sum, item) => sum + item.value, 0);

    return {
      title: {
        text: '各国家销售分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          // 显示完整的信息：国家、销售额、百分比
          return `${params.name}<br/>销售额: ${formatNumber(params.value, true)}<br/>占比: ${params.percent}%`;
        }
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        data: countries
      },
      series: [
        {
          name: '销售额分布',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            position: 'outside',
            formatter: function(params) {
              // 显示国家名和金额
              return `${params.name}: $${(params.value / 1000).toFixed(1)}k`;
            },
            fontSize: 12,
            color: '#333'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 10
          },
          data: salesData,
          color: COLORS_COUNTRY,
          // 添加中心文本显示总销售额
          center: ['50%', '50%']
        }
      ],
      // 添加总销售额显示在中心
      graphic: {
        type: 'text',
        left: 'center',
        top: 'center',
        style: {
          text: `总额\n${formatNumber(totalSales, true)}`,
          fontSize: 14,
          fontWeight: 'bold',
          textAlign: 'center',
          fill: '#333'
        }
      }
    };
  };

  // 国家销售环比图表选项 - 增强显示
  const getCountryGrowthOption = () => {
    if (!data.countryDistribution || data.countryDistribution.length === 0) {
      return { title: { text: '国家销售环比' } };
    }

    // 使用正确的字段名
    const countries = data.countryDistribution.map(item => item.country || '未知'); 
    const growthRates = data.countryDistribution.map(item => item.change_rate || 0);
    const currentValues = data.countryDistribution.map(item => item.value || 0);
    const previousValues = data.countryDistribution.map(item => {
      // 根据环比变化率计算上期销售额
      const current = item.value || 0;
      const rate = item.change_rate || 0;
      return rate !== 0 ? current / (1 + rate/100) : current;
    });

    return {
      title: {
        text: '各国家销售环比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const index = params[0].dataIndex;
          const currentValue = formatNumber(currentValues[index], true);
          const prevValue = formatNumber(previousValues[index], true);
          const rate = growthRates[index].toFixed(2);
          return `${params[0].name}<br/>
                  本期: ${currentValue}<br/>
                  上期: ${prevValue}<br/>
                  环比: ${rate}%`;
        },
        axisPointer: {
          type: 'shadow'
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
        data: countries,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        name: '环比增长',
        type: 'bar',
        data: growthRates,
        itemStyle: {
          color: function(params) {
            return params.value >= 0 ? INCREASE_COLOR : DECREASE_COLOR;
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: function(params) {
            return params.value >= 0 ? 
                   `+${params.value.toFixed(1)}%` : 
                   `${params.value.toFixed(1)}%`;
          },
          fontSize: 12,
          color: function(params) {
            return params.value >= 0 ? INCREASE_COLOR : DECREASE_COLOR;
          }
        }
      }]
    };
  };

  // 销售人员业绩对比图表选项
  const getSalespersonComparisonOption = () => {
    if (!data.salespersonComparison || data.salespersonComparison.length === 0) {
      return { title: { text: '销售人员业绩对比' } };
    }

    // 只显示前8名销售人员
    const topSalespeople = data.salespersonComparison.slice(0, 8);
    
    // 准备图表数据
    const salespersons = topSalespeople.map(item => item.sales_person || '未知');
    const salesAmount = topSalespeople.map(item => item.sales_amount || 0);
    const changeRates = topSalespeople.map(item => item.change_rate || 0);

    return {
      title: {
        text: '销售人员业绩与环比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function(params) {
          const salesIndex = params.findIndex(p => p.seriesName === '销售额');
          const changeIndex = params.findIndex(p => p.seriesName === '环比变化');
          
          return `${params[0].name}<br/>
                  销售额: ${formatNumber(params[salesIndex].value, true)}<br/>
                  环比: ${params[changeIndex].value >= 0 ? '+' : ''}${params[changeIndex].value.toFixed(2)}%`;
        }
      },
      legend: {
        data: ['销售额', '环比变化'],
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '20%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: salespersons,
        axisLabel: {
          interval: 0,
          rotate: 30,
          fontSize: 10
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '销售额',
          position: 'left',
          axisLabel: {
            formatter: function(value) {
              return '$' + (value / 1000).toFixed(0) + 'k';
            }
          }
        },
        {
          type: 'value',
          name: '环比变化',
          position: 'right',
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: '销售额',
          type: 'bar',
          data: salesAmount,
          yAxisIndex: 0,
          itemStyle: {
            color: COLORS[0]
          },
          label: {
            show: true,
            position: 'top',
            formatter: function(params) {
              return '$' + (params.value / 1000).toFixed(1) + 'k';
            }
          }
        },
        {
          name: '环比变化',
          type: 'line',
          data: changeRates,
          yAxisIndex: 1,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: function(params) {
              return params.value >= 0 ? INCREASE_COLOR : DECREASE_COLOR;
            }
          },
          label: {
            show: true,
            position: 'top',
            formatter: function(params) {
              return params.value >= 0 ? `+${params.value.toFixed(1)}%` : `${params.value.toFixed(1)}%`;
            }
          }
        }
      ]
    };
  };

  // 新增：平台指标环比雷达图配置
  const getPlatformRadarOption = () => {
    if (!data.platformComparison || Object.keys(data.platformComparison).length === 0) {
      return { title: { text: '平台指标环比分析' } };
    }
    
    // 准备雷达图数据
    const indicators = [
      { name: '销售额环比', max: Math.max(100, data.platformComparison.amount_change_rate * 1.2) },
      { name: '销量环比', max: Math.max(100, data.platformComparison.volume_change_rate * 1.2) },
      { name: '订单数环比', max: Math.max(100, data.platformComparison.orders_change_rate * 1.2) },
      { name: '毛利率环比', max: Math.max(20, data.platformComparison.profit_rate_change * 1.2) }
    ];
    
    const radarData = [
      {
        value: [
          data.platformComparison.amount_change_rate || 0,
          data.platformComparison.volume_change_rate || 0,
          data.platformComparison.orders_change_rate || 0,
          data.platformComparison.profit_rate_change || 0
        ],
        name: '环比变化率'
      }
    ];
    
    return {
      title: {
        text: '平台指标环比分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          let result = `${params.name}<br/>`;
          indicators.forEach((indicator, index) => {
            const value = params.value[index];
            result += `${indicator.name}: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%<br/>`;
          });
          return result;
        }
      },
      radar: {
        indicator: indicators,
        radius: '65%',
        center: ['50%', '50%'],
        splitNumber: 4,
        splitArea: {
          areaStyle: {
            color: ['rgba(255, 255, 255, 0.2)', 'rgba(200, 200, 200, 0.2)']
          }
        }
      },
      series: [
        {
          type: 'radar',
          data: radarData,
          areaStyle: {
            color: 'rgba(0, 136, 254, 0.4)'
          },
          lineStyle: {
            color: '#0088FE',
            width: 2
          },
          itemStyle: {
            color: '#0088FE'
          }
        }
      ]
    };
  };

  // 新增：平台销售渠道分析 (如果API返回了平台细分数据)
  const getPlatformChannelOption = () => {
    if (!data.platformDetail || data.platformDetail.length === 0) {
      return { title: { text: '销售渠道分析' } };
    }
    
    const platforms = data.platformDetail.map(item => item.platform);
    const currentValues = data.platformDetail.map(item => item.current_amount || 0);
    const previousValues = data.platformDetail.map(item => item.previous_amount || 0);
    const changeRates = data.platformDetail.map(item => item.change_rate || 0);
    
    return {
      title: {
        text: '销售渠道分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const index = params[0].dataIndex;
          return `${platforms[index]}<br/>
                  本期销售额: ${formatNumber(currentValues[index], true)}<br/>
                  上期销售额: ${formatNumber(previousValues[index], true)}<br/>
                  环比变化: ${changeRates[index] >= 0 ? '+' : ''}${changeRates[index].toFixed(2)}%`;
        }
      },
      legend: {
        data: ['本期销售额', '上期销售额', '环比变化'],
        bottom: 10
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: platforms,
        axisLabel: {
          interval: 0,
          rotate: 30
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '销售额',
          axisLabel: {
            formatter: function(value) {
              return '$' + (value / 1000).toFixed(0) + 'k';
            }
          }
        },
        {
          type: 'value',
          name: '变化率',
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: '本期销售额',
          type: 'bar',
          data: currentValues,
          barWidth: '20%',
          itemStyle: {
            color: '#0088FE'
          }
        },
        {
          name: '上期销售额',
          type: 'bar',
          data: previousValues,
          barWidth: '20%',
          itemStyle: {
            color: '#FFBB28'
          }
        },
        {
          name: '环比变化',
          type: 'line',
          yAxisIndex: 1,
          data: changeRates,
          lineStyle: {
            color: '#FF8042'
          },
          label: {
            show: true,
            position: 'top',
            formatter: function(params) {
              return params.value >= 0 ? 
                     `+${params.value.toFixed(1)}%` : 
                     `${params.value.toFixed(1)}%`;
            }
          }
        }
      ]
    };
  };

  // 销售人员雷达图配置
  const getSalespersonRadarOption = () => {
    if (!data.salespersonComparison || data.salespersonComparison.length === 0) {
      return { title: { text: '销售人员多维指标' } };
    }

    // 只显示前5名销售人员
    const topSalespeople = data.salespersonComparison.slice(0, 5);
    
    // 准备雷达图数据
    const indicator = [
      { name: '销售额', max: Math.max(...topSalespeople.map(p => p.sales_amount || 0)) * 1.2 },
      { name: '销量', max: Math.max(...topSalespeople.map(p => p.sales_volume || 0)) * 1.2 },
      { name: '订单数', max: Math.max(...topSalespeople.map(p => p.order_count || 0)) * 1.2 },
      { name: '客单价', max: Math.max(...topSalespeople.map(p => p.average_order || 0)) * 1.2 },
      { name: '环比增长', max: Math.max(20, Math.max(...topSalespeople.map(p => Math.max(p.change_rate || 0, 0)))) } 
    ];
    
    const seriesData = topSalespeople.map(person => {
      return {
        value: [
          person.sales_amount || 0,
          person.sales_volume || 0,
          person.order_count || 0,
          person.average_order || 0,
          Math.max(person.change_rate || 0, 0)  // 环比增长取正值，负值显示为0
        ],
        name: person.sales_person
      };
    });

    return {
      title: {
        text: '销售人员多维分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'item'
      },
      legend: {
        data: topSalespeople.map(p => p.sales_person),
        top: 30
      },
      radar: {
        indicator: indicator,
        shape: 'circle',
        splitNumber: 5,
        radius: '65%',
        name: {
          textStyle: {
            color: '#333',
            fontSize: 14
          }
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(255, 255, 255, 0.5)', 'rgba(240, 240, 240, 0.5)']
          }
        }
      },
      series: [{
        type: 'radar',
        data: seriesData,
        areaStyle: {
          opacity: 0.1
        },
         areaStyle: {
          opacity: 0.2
        },
        emphasis: {
          lineStyle: {
            width: 4
          },
          areaStyle: {
            opacity: 0.5
          }
        }
      }]
    };
  };

  // 平台详情图表配置
  const getPlatformDetailOption = () => {
    if (!data.platformDetail || data.platformDetail.length === 0) {
      return { title: { text: '平台销售详情' } };
    }

    const platforms = data.platformDetail.map(item => item.platform || '未知');
    const salesAmount = data.platformDetail.map(item => item.sales_amount || 0);
    const salesVolume = data.platformDetail.map(item => item.sales_volume || 0);
    const ordersCount = data.platformDetail.map(item => item.order_count || 0);

    return {
      title: {
        text: '各平台销售指标对比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['销售额', '销量', '订单数'],
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '20%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: platforms,
        axisLabel: {
          interval: 0,
          rotate: 30,
          fontSize: 10
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '销售额',
          position: 'left',
          axisLabel: {
            formatter: function(value) {
              return '$' + (value / 1000).toFixed(0) + 'k';
            }
          }
        },
        {
          type: 'value',
          name: '数量',
          position: 'right'
        }
      ],
      series: [
        {
          name: '销售额',
          type: 'bar',
          data: salesAmount,
          yAxisIndex: 0,
          itemStyle: {
            color: COLORS[0]
          },
          label: {
            show: true,
            position: 'top',
            formatter: function(params) {
              return '$' + (params.value / 1000).toFixed(1) + 'k';
            }
          }
        },
        {
          name: '销量',
          type: 'bar',
          data: salesVolume,
          yAxisIndex: 1,
          itemStyle: {
            color: COLORS[1]
          }
        },
        {
          name: '订单数',
          type: 'line',
          data: ordersCount,
          yAxisIndex: 1,
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: {
            color: COLORS[2]
          }
        }
      ]
    };
  };

  // 平台渠道占比饼图 - 修改为使用platformSalesDistribution
  const getPlatformPieOption = () => {
    if (!data.platformSalesDistribution || Object.keys(data.platformSalesDistribution).length === 0) {
      return { title: { text: '平台渠道占比' } };
    }

    // 准备饼图数据
    const pieData = Object.entries(data.platformSalesDistribution).map(([platform, value], index) => ({
      name: platform,
      value: value
    }));

    // 计算总销售额
    const totalSales = pieData.reduce((sum, item) => sum + item.value, 0);

    return {
      title: {
        text: '平台渠道销售占比',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: ' + formatNumber('{c}', true) + ' ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        data: pieData.map(item => item.name)
      },
      series: [
        {
          name: '平台占比',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: true,
          label: {
            show: true,
            formatter: '{b}: {d}%'
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          data: pieData,
          color: COLORS
        }
      ],
      graphic: {
        type: 'text',
        left: 'center',
        top: 'center',
        style: {
          text: `总额\n${formatNumber(totalSales, true)}`,
          fontSize: 14,
          fontWeight: 'bold',
          textAlign: 'center',
          fill: '#333'
        }
      }
    };
  };

  // 销售人员订单与销量对比
  const getSalespersonVolumeOption = () => {
    if (!data.salespersonComparison || data.salespersonComparison.length === 0) {
      return { title: { text: '销售人员订单与销量对比' } };
    }
    
    // 只显示前6名销售人员，便于显示
    const topSalespeople = data.salespersonComparison.slice(0, 6);
    
    const salespersons = topSalespeople.map(item => item.sales_person);
    const salesVolumes = topSalespeople.map(item => item.sales_volume || 0);
    const orderCounts = topSalespeople.map(item => item.order_count || 0);
    
    return {
      title: {
        text: '销售人员订单与销量对比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function(params) {
          const salesPersonIdx = params[0].dataIndex;
          const personName = salespersons[salesPersonIdx];
          let result = `${personName}<br/>`;
          params.forEach(param => {
            const color = param.color;
            const seriesName = param.seriesName;
            const value = formatNumber(param.value);
            result += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span> ${seriesName}: ${value}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['销量', '订单数'],
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '20%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: salespersons,
        axisLabel: {
          interval: 0,
          rotate: 30,
          fontSize: 10
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '销量',
          position: 'left'
        },
        {
          type: 'value',
          name: '订单数',
          position: 'right'
        }
      ],
      series: [
        {
          name: '销量',
          type: 'bar',
          data: salesVolumes,
          itemStyle: {
            color: COLORS[0]
          },
          label: {
            show: true,
            position: 'top'
          }
        },
        {
          name: '订单数',
          type: 'line',
          yAxisIndex: 1,
          data: orderCounts,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: COLORS[2]
          },
          label: {
            show: true,
            position: 'top'
          }
        }
      ]
    };
  };

  // 销量Top5表格列
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
      render: (val) => formatNumber(val),
      width: 100
    }
  ];

  // 销售额Top5表格列
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

  // 环比上升表格列
  const increasedColumns = [
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
      title: '本期销售额',
      dataIndex: 'current_value',
      key: 'current_value',
      render: (val) => formatNumber(val, true),
      width: 120
    },
    {
      title: '环比增长',
      dataIndex: 'change_rate',
      key: 'change_rate',
      render: (val) => (
        <span style={{ color: '#52c41a' }}>
          +{val.toFixed(2)}%
        </span>
      ),
      width: 100
    }
  ];

  // 环比下降表格列
  const decreasedColumns = [
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
      title: '本期销售额',
      dataIndex: 'current_value',
      key: 'current_value',
      render: (val) => formatNumber(val, true),
      width: 120
    },
    {
      title: '环比下降',
      dataIndex: 'change_rate',
      key: 'change_rate',
      render: (val) => (
        <span style={{ color: '#f5222d' }}>
          {val.toFixed(2)}%
        </span>
      ),
      width: 100
    }
  ];

  // 销售人员业绩表格列定义
  const salespersonColumns = [
    {
      title: '销售人员',
      dataIndex: 'sales_person',
      key: 'sales_person',
      width: 120
    },
    {
      title: '本期销售额',
      dataIndex: 'current_amount',
      key: 'current_amount',
      render: value => value !== undefined && value !== null ? `$${safeFormat(value)}` : 'N/A',
    },
    {
      title: '上期销售额',
      dataIndex: 'previous_amount',
      key: 'previous_amount',
      render: value => value !== undefined && value !== null ? `$${safeFormat(value)}` : 'N/A',
    },
    {
      title: '销售额环比',
      dataIndex: 'amount_change_rate',
      key: 'amount_change_rate',
      render: value => {
        if (value === undefined || value === null) return 'N/A';
        const formatted = safeFormat(value);
        if (formatted === 'N/A') return formatted;
        return (
          <span style={{ color: parseFloat(value) >= 0 ? '#3f8600' : '#cf1322' }}>
            {value >= 0 ? '+' : ''}{formatted}%
          </span>
        );
      }
    },
    {
      title: '本期销量',
      dataIndex: 'current_volume',
      key: 'current_volume',
      render: value => value !== undefined && value !== null ? safeFormat(value) : 'N/A'
    },
    {
      title: '销量环比',
      dataIndex: 'volume_change_rate',
      key: 'volume_change_rate',
      render: value => {
        if (value === undefined || value === null) return 'N/A';
        const formatted = safeFormat(value);
        if (formatted === 'N/A') return formatted;
        return (
          <span style={{ color: parseFloat(value) >= 0 ? '#3f8600' : '#cf1322' }}>
            {value >= 0 ? '+' : ''}{formatted}%
          </span>
        );
      }
    },
    {
      title: '毛利率',
      dataIndex: 'current_profit_rate',
      key: 'current_profit_rate',
      render: (val) => val !== undefined && val !== null ? `${val.toFixed(2)}%` : 'N/A',
    }
  ];

  // Also, update the safeFormat function to be more robust
const safeFormat = (value, decimals = 2) => {
  if (value === undefined || value === null) return 'N/A';
  try {
    return parseFloat(value).toFixed(decimals);
  } catch (error) {
    console.error('Error formatting value:', value, error);
    return 'N/A';
  }
};

  return (
    <div className="dashboard-container">
      {/* 页面标题和周选择器 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>销售数据看板</Title>
        <div>
          <span style={{ marginRight: 8 }}>周次筛选:</span>
          <Select
            value={weekFilter}
            onChange={value => setWeekFilter(value)}
            style={{ width: 120, marginRight: 16 }}
          >
            <Option value="all">所有周次</Option>
            <Option value="202401">2024年第1周</Option>
            <Option value="202402">2024年第2周</Option>
          </Select>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadAllData}
            loading={loading}
          >
            刷新数据
          </Button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="数据加载错误"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 加载状态 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '100px 0' }}>
          <Spin size="large" tip="数据加载中..." />
        </div>
      ) : (
        <>
          {/* 平台整体指标 */}
          <Card title="平台整体指标" className="dashboard-card" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="销售额"
                  value={data.platformComparison?.current_amount || 0}
                  precision={2}
                  valueStyle={{ color: '#3f8600' }}
                  prefix="$"  // 美元符号
                  suffix={
                    data.platformComparison?.amount_change_rate ? (
                      <Tag color={data.platformComparison.amount_change_rate >= 0 ? 'green' : 'red'}>
                        {data.platformComparison.amount_change_rate >= 0 ? '+' : ''}
                        {data.platformComparison.amount_change_rate.toFixed(2)}%
                      </Tag>
                    ) : null
                  }
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="销量"
                  value={data.platformComparison?.current_volume || 0}
                  valueStyle={{ color: '#3f8600' }}
                  suffix={
                    data.platformComparison?.volume_change_rate ? (
                      <Tag color={data.platformComparison.volume_change_rate >= 0 ? 'green' : 'red'}>
                        {data.platformComparison.volume_change_rate >= 0 ? '+' : ''}
                        {data.platformComparison.volume_change_rate.toFixed(2)}%
                      </Tag>
                    ) : null
                  }
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="订单数"
                  value={data.platformComparison?.current_orders || 0}
                  valueStyle={{ color: '#3f8600' }}
                  suffix={
                    data.platformComparison?.orders_change_rate ? (
                      <Tag color={data.platformComparison.orders_change_rate >= 0 ? 'green' : 'red'}>
                        {data.platformComparison.orders_change_rate >= 0 ? '+' : ''}
                        {data.platformComparison.orders_change_rate.toFixed(2)}%
                      </Tag>
                    ) : null
                  }
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="毛利率"
                  value={data.platformComparison?.current_profit_rate || 0}
                  precision={2}
                  valueStyle={{ color: '#3f8600' }}
                  suffix="%"
                  prefix={
                    data.platformComparison?.profit_rate_change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                  }
                />
              </Col>
            </Row>
          </Card>

          {/* 销售额和销量Top5 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card title="销售额Top5" className="dashboard-card">
                {data.topSalesAmount && data.topSalesAmount.length > 0 ? (
                  <>
                    <ReactECharts 
                      option={getTopSalesAmountOption()} 
                      style={{ height: 300 }}
                      notMerge={true}
                      lazyUpdate={true}
                    />
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
                  <Empty description="暂无销售额数据" />
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="销量Top5" className="dashboard-card">
                {data.topSalesVolume && data.topSalesVolume.length > 0 ? (
                  <>
                    <ReactECharts 
                      option={getTopSalesVolumeOption()} 
                      style={{ height: 300 }}
                      notMerge={true}
                      lazyUpdate={true}
                    />
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
                  <Empty description="暂无销量数据" />
                )}
              </Card>
            </Col>
          </Row>

          {/* 环比上升和下降Top5 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card title="环比上升Top5" className="dashboard-card">
                {data.topIncreased && data.topIncreased.length > 0 ? (
                  <ReactECharts 
                    option={getTopIncreasedOption()} 
                    style={{ height: 300 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无环比上升数据" />
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="环比下降Top5" className="dashboard-card">
                {data.topDecreased && data.topDecreased.length > 0 ? (
                  <ReactECharts 
                    option={getTopDecreasedOption()} 
                    style={{ height: 300 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无环比下降数据" />
                )}
              </Card>
            </Col>
          </Row>

          {/* 国家销售分布 */}
          <Row gutter={16}>
            <Col span={12}>
              <Card title="各国家销售分布" className="dashboard-card" style={{ marginBottom: 16 }}>
                {data.countryDistribution && data.countryDistribution.length > 0 ? (
                  <ReactECharts 
                    option={getCountryPieOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无国家分布数据" />
                )}
              </Card>
            </Col>

            {/* 国家销售环比 */}
            <Col span={12}>
              <Card title="各国家销售环比" className="dashboard-card" style={{ marginBottom: 16 }}>
                {data.countryDistribution && data.countryDistribution.length > 0 ? (
                  <ReactECharts 
                    option={getCountryGrowthOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无国家环比数据" />
                )}
              </Card>
            </Col>
          </Row>

          {/* 新增：平台指标环比分析 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card title="平台指标环比分析" className="dashboard-card">
                {data.platformComparison && Object.keys(data.platformComparison).length > 0 ? (
                  <ReactECharts 
                    option={getPlatformRadarOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无平台指标数据" />
                )}
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="平台销售渠道分析" className="dashboard-card">
                {data.platformDetail && data.platformDetail.length > 0 ? (
                  <ReactECharts 
                    option={getPlatformChannelOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无平台渠道数据" />
                )}
              </Card>
            </Col>
          </Row>
          
          {/* 平台销售详情 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card title="平台渠道占比" className="dashboard-card">
                {data.platformSalesDistribution && Object.keys(data.platformSalesDistribution).length > 0 ? (
                  <ReactECharts 
                    option={getPlatformPieOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无平台渠道数据" />
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="平台销售详情" className="dashboard-card">
                {data.platformDetail && data.platformDetail.length > 0 ? (
                  <ReactECharts 
                    option={getPlatformDetailOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无平台详情数据" />
                )}
              </Card>
            </Col>
          </Row>

          {/* 新增：销售人员多维指标分析 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card title="销售人员多维指标分析" className="dashboard-card">
                {data.salespersonComparison && data.salespersonComparison.length > 0 ? (
                  <ReactECharts 
                    option={getSalespersonRadarOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无销售人员多维指标数据" />
                )}
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="销售人员订单与销量对比" className="dashboard-card">
                {data.salespersonComparison && data.salespersonComparison.length > 0 ? (
                  <ReactECharts 
                    option={getSalespersonVolumeOption()} 
                    style={{ height: 400 }}
                    notMerge={true}
                    lazyUpdate={true}
                  />
                ) : (
                  <Empty description="暂无销售人员订单与销量数据" />
                )}
              </Card>
            </Col>
          </Row>

          {/* 销售人员业绩对比部分 */}
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title="销售人员业绩对比" className="dashboard-card" style={{ marginBottom: 16 }}>
                {data.salespersonComparison && data.salespersonComparison.length > 0 ? (
                  <>
                    <ReactECharts 
                      option={getSalespersonComparisonOption()} 
                      style={{ height: 400 }}
                      notMerge={true}
                      lazyUpdate={true}
                    />
                    <Divider orientation="left">销售人员详细数据</Divider>
                    <Table
                      dataSource={data.salespersonComparison}
                      columns={salespersonColumns}
                      pagination={false}
                      size="small"
                      rowKey={(record, index) => `salesperson-${index}`}
                      scroll={{ x: 800 }}
                    />
                  </>
                ) : (
                  <Empty description="暂无销售人员数据" />
                )}
              </Card>
            </Col>
          </Row>

          {/* AI分析部分 */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title="AI销售数据分析" className="dashboard-card">
                <AIAnalysis 
                  top_sales={data.topSalesAmount} 
                  top_increased={data.topIncreased}
                  top_decreased={data.topDecreased}
                  country_distribution={data.countryDistribution}
                  platform_comparison={data.platformComparison}
                  salesperson_comparison={data.salespersonComparison}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default Dashboard;