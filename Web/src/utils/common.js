// 通用工具函数 - 提取重复的逻辑到此文件

/**
 * 格式化时间
 * @param {string|Date} time - 时间字符串或Date对象
 * @param {string} locale - 地区设置，默认为'zh-CN'
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(time, locale = 'zh-CN') {
  if (!time) return '未知'
  
  try {
    const date = new Date(time)
    if (isNaN(date.getTime())) return '未知'
    
    return date.toLocaleString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    console.error('格式化时间失败:', error)
    return '未知'
  }
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期字符串或Date对象
 * @param {string} locale - 地区设置，默认为'zh-CN'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, locale = 'zh-CN') {
  if (!date) return '未知'
  
  try {
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) return '未知'
    
    return dateObj.toLocaleDateString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  } catch (error) {
    console.error('格式化日期失败:', error)
    return '未知'
  }
}

/**
 * 计算使用百分比
 * @param {number} total - 总数
 * @param {number} used - 已使用数
 * @returns {number} 剩余百分比
 */
export function getUsagePercentage(total, used) {
  if (total === -1 || total === 0) return 0
  const remaining = Math.max(0, total - used)
  const percentage = Math.round((remaining / total) * 100)
  return Math.max(0, Math.min(100, percentage))
}

/**
 * 根据使用情况获取进度条颜色
 * @param {number} total - 总数
 * @param {number} used - 已使用数
 * @returns {string} 颜色值
 */
export function getProgressColor(total, used) {
  if (total === -1 || total === 0) return '#67c23a'
  const remaining = Math.max(0, total - used)
  const percentage = remaining / total
  
  if (percentage > 0.6) return '#67c23a'
  if (percentage > 0.3) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 获取操作类型对应的Element Plus标签类型
 * @param {string} className - 操作类型
 * @returns {string} Element Plus标签类型
 */
export function getOperationType(className) {
  switch (className) {
    case '图片识别':
    case '1':
    case 1:
      return 'primary'
    case '批量处理':
    case '2':
    case 2:
      return 'success'
    case '实时检测':
    case '实时识别':
    case '3':
    case 3:
      return 'warning'
    default:
      return 'info'
  }
}

/**
 * 获取操作名称
 * @param {string|number} className - 操作类型标识
 * @returns {string} 操作名称
 */
export function getOperationName(className) {
  const classStr = String(className)
  
  switch (classStr) {
    case '1':
      return '图片识别'
    case '2':
      return '批量处理'
    case '3':
      return '实时识别'
    case '图片识别':
    case '批量处理':
    case '实时检测':
    case '实时识别':
      return className
    default:
      return className || '未知操作'
  }
}

/**
 * 获取日志操作类型
 * @param {string} logText - 日志文本
 * @returns {string} Element Plus标签类型
 */
export function getLogType(logText) {
  if (!logText || typeof logText !== 'string') return 'info'
  if (logText.includes('创建') || logText.includes('添加')) return 'success'
  if (logText.includes('删除') || logText.includes('封禁')) return 'danger'
  if (logText.includes('修改') || logText.includes('更新')) return 'warning'
  return 'info'
}

/**
 * 获取日志操作动作
 * @param {string} logText - 日志文本
 * @returns {string} 操作动作名称
 */
export function getLogAction(logText) {
  if (!logText || typeof logText !== 'string') return '操作'
  if (logText.includes('创建')) return '创建'
  if (logText.includes('删除')) return '删除'
  if (logText.includes('修改')) return '修改'
  if (logText.includes('封禁')) return '封禁'
  if (logText.includes('解封')) return '解封'
  if (logText.includes('登录')) return '登录'
  return '操作'
}

/**
 * 获取排名样式类
 * @param {number} index - 排名索引（从0开始）
 * @returns {string} CSS类名
 */
export function getRankClass(index) {
  switch (index) {
    case 0: return 'rank-first'
    case 1: return 'rank-second'
    case 2: return 'rank-third'
    default: return 'rank-other'
  }
}

/**
 * 生成CSV内容
 * @param {Array} data - 数据数组
 * @param {Array} headers - 表头数组
 * @param {Function} rowMapper - 行数据映射函数
 * @returns {string} CSV内容
 */
export function generateCSV(data, headers, rowMapper) {
  if (!data || !Array.isArray(data) || !headers || !Array.isArray(headers)) {
    throw new Error('Invalid data or headers for CSV generation')
  }
  
  const headerRow = headers.join(',') + '\n'
  const rows = data.map(item => {
    const row = rowMapper ? rowMapper(item) : Object.values(item)
    return row.map(value => `"${String(value).replace(/"/g, '""')}"`).join(',')
  }).join('\n')
  
  return '\uFEFF' + headerRow + rows // 添加BOM以支持中文
}

/**
 * 下载文件
 * @param {string} content - 文件内容
 * @param {string} filename - 文件名
 * @param {string} type - MIME类型
 */
export function downloadFile(content, filename, type = 'text/plain') {
  try {
    const blob = new Blob([content], { type: `${type};charset=utf-8;` })
    const link = document.createElement('a')
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', filename)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      return true
    }
    return false
  } catch (error) {
    console.error('下载文件失败:', error)
    return false
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
  let inThrottle
  return function executedFunction(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 深拷贝对象
 * @param {any} obj - 要拷贝的对象
 * @returns {any} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (typeof obj === 'object') {
    const clonedObj = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
  return obj
}

/**
 * 安全的JSON解析
 * @param {string} jsonString - JSON字符串
 * @param {any} defaultValue - 解析失败时的默认值
 * @returns {any} 解析结果或默认值
 */
export function safeJsonParse(jsonString, defaultValue = null) {
  try {
    return JSON.parse(jsonString)
  } catch (error) {
    console.warn('JSON解析失败:', error)
    return defaultValue
  }
}

/**
 * 存储到localStorage（带错误处理）
 * @param {string} key - 键名
 * @param {any} value - 值
 * @returns {boolean} 是否成功
 */
export function setStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch (error) {
    console.error('存储到localStorage失败:', error)
    return false
  }
}

/**
 * 从localStorage获取（带错误处理）
 * @param {string} key - 键名
 * @param {any} defaultValue - 默认值
 * @returns {any} 获取的值或默认值
 */
export function getStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.error('从localStorage获取失败:', error)
    return defaultValue
  }
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
