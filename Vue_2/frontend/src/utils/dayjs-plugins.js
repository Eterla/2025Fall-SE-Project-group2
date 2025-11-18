/* eslint-disable */
import dayjs from './dayjs.min.js'
export default dayjs // 不加载任何插件
// // 1. 注册 UTC 插件（处理服务器返回的 UTC 时间）
const utcPlugin = (option, dayjsClass) => {
  const oldParse = dayjsClass.parse
  dayjsClass.parse = function (cfg) {
    if (cfg.utc) {
      cfg.date = new Date(cfg.date).toUTCString()
    }
    return oldParse.call(this, cfg)
  }
  dayjsClass.prototype.utc = function () {
    return this.clone().local(false)
  }
  dayjsClass.utc = function (date, format, strict) {
    return dayjsClass(date, format, strict).utc()
  }
}

// 2. 注册时区转换插件（UTC → 北京时间 UTC+8）
const timezonePlugin = (option, dayjsClass) => {
  dayjsClass.prototype.tz = function (timezone) {
    if (timezone === 'Asia/Shanghai') {
      const utcTime = this.utc().valueOf() // 获取 UTC 时间戳
      const beijingTime = utcTime + 8 * 60 * 60 * 1000 // 加 8 小时 = 北京时间
      return dayjsClass(beijingTime)
    }
    return this
  }
}

// 3. 启用插件
dayjs.extend(utcPlugin)
dayjs.extend(timezonePlugin)

