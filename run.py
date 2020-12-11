# -*-coding:utf-8-*-
from src import config, create_report, unzip_file
from src.index_judge import *
from src.create_file import *
from src.analyze_bugreport import *


def analyze_report(app_name, pkg_name, bugreport_file):
    # 解压bugreport
    bugreport_txt = unzip_file(os.path.join(config.FILE_PATH, bugreport_file), config.FILE_PATH)
    # 创建分析文件
    logger.info('----------创建分析文件----------')
    file_create = FileCreate(bugreport_txt)
    # 获取app相关信息
    logger.info('----------获取app相关信息----------')
    pkg_version = file_create.get_pkg_version(pkg_name)
    # 根据processes_path, 获取app_info
    app_info = file_create.create_app_info_appops(pkg_name)
    uid_list = file_create.uid_list
    if app_info is None:
        logger.error("App：%s，不存在后台耗电数据" % pkg_name)
        exit(0)
    else:
        logger.info("App：%s，pid: %s, 存在后台耗电数据" % (app_info.app_name, app_info.app_uid))
        app_uid = app_info.app_uid
        logger.info('----------开始耗电分析----------')
        # 创建AnalyzeDump对象
        analyze_dump_obj = AnalyzeDump(app_uid)
        # 获取耗电摘要
        battery_summary = analyze_dump_obj.get_battery_summary(uid_list)

        # 分析dump_list
        # wifi_scan，并保存到analyze_bugreport中的 wifi_scan_list
        # wake_lock_obj，并保存到analyze_bugreport中的 wakelock_list
        # wakeup_obj，并保存到analyze_bugreport中的 wakeup_obj_list
        # job_obj，并保存到analyze_bugreport中的 job_obj_list
        # sync_obj，并保存到analyze_bugreport中的 sync_obj_list
        analyze_dump_obj.analyze_dump_list()

        # 统计电量
        analyze_dump_obj.analyze_power_used()

        # 判断电池指标是否合格
        logger.info('----------判断电池指标是否合格----------')
        index_jubge_obj = IndexJubge(pkg_name, file_create, analyze_dump_obj, id)
        index_jubge_obj.wifi_scan_times_jubge()
        index_jubge_obj.wakeup_times_jubge()
        index_jubge_obj.wakelock_duration_jubge()
        index_jubge_obj.job_interval_jubge()
        index_jubge_obj.sync_interval_jubge()

        # 信息统计
        app_info = {
            'app_name': app_name,
            'uid': app_info.app_uid,
            'version': pkg_version,
            'pkg_name': pkg_name
        }
        battery_statistics = {
            'statistics': str(analyze_dump_obj.app_power_used_line).lower(),
            'battery_total': analyze_dump_obj.mobile_power_capacity,
            'battery_percent': analyze_dump_obj.app_power_used_Percent,
            'battery_count': analyze_dump_obj.app_power_used,
            'network_trffic': analyze_dump_obj.network_trffic,
            'wifi_scans_times': index_jubge_obj.wifi_scan_times,
            'wakeup_times': index_jubge_obj.wakeup_times,
            'wake_lock_times': index_jubge_obj.wakelock_times,
            'job_scheduler_times': index_jubge_obj.job_times,
            'sync_manager_times': index_jubge_obj.sync_times,
        }

        html_path = {
            'wifiScan': 'wifiScan.html',
            'wakeUp': 'wakeUp.html',
            'wakeLock': 'wakeLock.html',
            'jobScheduler': 'jobScheduler.html',
            'syncManager': 'syncManager.html',
            'batterySummary': 'batterySummary.html',
            'unqualifiedEvent': 'unqualifiedEvent.html'
        }

        report_context = {
            'app_info': app_info,
            'battery_statistics': battery_statistics,
            'battery_summary': battery_summary,
            'unqualified_event': index_jubge_obj.unqualified_event_str,
            'html_path': html_path
        }

        battery_summary_context = {
            'title': '耗电详情',
            'content': battery_summary
        }

        unqualified_event_context = {
            'title': '不合格事件',
            'content': index_jubge_obj.unqualified_event_str
        }

        # 生成unqualified_event html
        unqualified_event_html = os.path.join(config.REPORT_PATH, index_jubge_obj.time, "unqualifiedEvent.html")
        create_report(unqualified_event_html, unqualified_event_context, 'text.html')

        # 生成battery_summary html
        battery_summary_html = os.path.join(config.REPORT_PATH, index_jubge_obj.time, "batterySummary.html")
        create_report(battery_summary_html, battery_summary_context, 'text.html')

        # 生成报告
        report_html = os.path.join(config.REPORT_PATH, index_jubge_obj.time, "index.html")
        create_report(report_html, report_context, 'report.html')

        return app_info, battery_statistics, report_html


if __name__ == "__main__":
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
