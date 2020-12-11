# 安卓后台耗电分析
**通过分析bugreport文件，统计后台耗电各项指标，以及指标是否合格。**

* 支持系统: 
    * windows
    * Linux
    * Mac

* 需要环境: 
    * python3.5+

* 使用指南：
```python
# 1.将bugreport报告放到files目录下
# 2. 执行run.py
# <= android 6
# bugreport_file = "bugreport_SM9.txt"
# >= android 7
bugreport_file = "bugreport-2020-12-10-15-08-27.zip"
app_name = "wechat"
pkg_name = "com.tencent.mm"
app_info, battery_statistics, report_html = analyze_report(app_name, pkg_name, bugreport_file)

logger.success(app_info)
logger.success(battery_statistics)
logger.success("后台耗电报告: %s" % report_html)

```

* 输出html报告：
![image](https://s3.ax1x.com/2020/12/11/rAnsCd.png)

* 代码结构说明
    * files: bugreport文件存放地址
    * report：生成的报告存放地址
    * src: 核心逻辑
    * templates: 报告模版文件
    * run.py: 生成报告执行文件


