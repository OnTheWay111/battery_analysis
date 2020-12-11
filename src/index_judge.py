# -*-coding:utf-8-*-
import csv
import os
import time
from src import config, csv2html, logger
from src.create_csv import *


class IndexJubge(object):
    def __init__(self, app_name, file_create, analyze_dump_obj, id):
        self.app_name = app_name
        self.bugreport_seconds = file_create.bugreport_seconds
        # 时间分片，以小时为单位
        self.counts = self.bugreport_seconds / 3600
        # 进一法，计算bugreport搜集的小时数
        self.bugreport_hours = int(self.counts) + 1
        self.analyze_dump_obj = analyze_dump_obj
        self.time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        self.outfile_path = os.path.join(config.REPORT_PATH, self.time)
        self.wifi_scan_times = 0
        self.wakeup_times = 0
        self.wakelock_times = 0
        self.job_times = 0
        self.sync_times = 0
        self.unqualified_event_str = ''
        if not os.path.exists(self.outfile_path):
            logger.info("生成文件夹: %s" % self.outfile_path)
            os.makedirs(self.outfile_path)

    def get_pid_battery_info(self, app_uid):
        # 将uid对应的电池统计信息，写入文件
        pid_battery_info_path = os.path.dirname(__file__) + '/files/pid_battery_info.txt'
        uid_battery_info = os.path.join(self.outfile_path, 'uid_battery_info.txt')
        f1 = open(uid_battery_info, 'w')
        is_write = False

        all_uid_info_f = open(pid_battery_info_path, 'r')
        while 1:
            str_line = str(all_uid_info_f.readline())
            if app_uid in str_line:
                is_write = True
            elif is_write and ("u0" in str_line or "was the duration of dumpsys batterystats" in str_line):
                break
            if is_write:
                f1.write(str_line)
        all_uid_info_f.close()
        f1.close()

            # 每小时事件发生次数不超过limit_time
    def times_decide_hour(self, occure_times, event_list, limit_time, bugreport_hours, tag):
        # occure_times: 总共发生次数
        # event_list: 事件list列表
        # limit_time: 限制次数
        # bugreport_hours: bugreport搜集的小时数,进一法
        # tag: 指标内容
        # 不合格次数
        un_qualified_times = 0
        # 如果发生次数大于限制次数
        if occure_times > limit_time:
            # 如果bugreport时间大于1小时
            if bugreport_hours > 1:
                for i in range(1, bugreport_hours):
                    start_time = (i - 1) * 3600
                    end_time = i * 3600
                    event_count_hour = 0
                    event_hour_list = []
                    for index in range(0, occure_times):
                        if (event_list[index].occur_seconds > start_time) and (event_list[index].occur_seconds <= end_time):
                            event_hour_list.append(event_list[index])
                            event_count_hour += 1
                    if event_count_hour > limit_time:
                        un_qualified_times += 1
                        for event_obj in event_hour_list:
                            logger.info(event_obj.dump_str)

    # 方法：事件间隔大于一定事件
    def time_interval_limit(self, event_times, event_list, seconds_limit, tag):
        unqualified_time = 0
        unqualified_event_list = []
        if event_times > 1:
            for index in range(0, event_times-1):
                job1_occure_time = event_list[index].occur_seconds
                job2_occure_time = event_list[index + 1].occur_seconds
                if (job2_occure_time - job1_occure_time) < seconds_limit:
                    unqualified_time += 1
                    logger.warning("（不合格）", tag, ", 两次事件 dump分别为：\n", event_list[index].start_dump_str, "\n", event_list[index + 1].start_dump_str)
                    self.unqualified_event_str = self.unqualified_event_str + "（不合格）" + tag + " 两次事件 dump分别为：\n" + event_list[index].start_dump_str, "\n" + event_list[index + 1].start_dump_str
                    unqualified_event_list.append(event_list[index].start_dump_str)
                    unqualified_event_list.append(event_list[index + 1].start_dump_str)


    # TODO: WiFi扫描次数是否一小时大于4次
    def wifi_scan_times_jubge(self):
        wifi_scan_obj_list = self.analyze_dump_obj.wifi_scan_obj_list

        # 生成csv文件
        file_name = os.path.join(self.outfile_path, "wifiScan.csv")
        html_name = os.path.join(self.outfile_path, "wifiScan.html")
        csv_head_list = ['occur_seconds', 'dump_str']
        create_csv(file_name, csv_head_list)
        # 将信息写入csv文件
        with open(file_name, 'a+') as f:
            csv_write = csv.writer(f)
            for wifi_scan_obj in wifi_scan_obj_list:
                data_row_list = [str(wifi_scan_obj.occur_seconds), wifi_scan_obj.dump_str]
                csv_write.writerow(data_row_list)
        csv2html(file_name, html_name)
        os.remove(file_name)

        self.wifi_scan_times = len(wifi_scan_obj_list)
        wifi_scan_tag = "后台wifi扫描次数/H"
        wifi_scan_limit_time = 4
        # 判断wifi scan是否一小时大于4次
        self.times_decide_hour(self.wifi_scan_times, wifi_scan_obj_list, wifi_scan_limit_time, self.bugreport_hours, wifi_scan_tag)

    # TODO: 判断是否有大于1小时的唤醒锁
    def wakelock_duration_jubge(self):
        wakelock_obj_list = self.analyze_dump_obj.wakelock_obj_list

        file_name = os.path.join(self.outfile_path, "wakeLock.csv")
        html_name = os.path.join(self.outfile_path, "wakeLock.html")
        csv_head_list = ['occur_seconds', 'name', 'duration_time(ms)', 'start_dump_str', 'end_dump_str', 'end_seconds']
        create_csv(file_name, csv_head_list)
        # 将信息写入csv文件
        with open(file_name, 'a+') as f:
            csv_write = csv.writer(f)
            for wakelock_obj in wakelock_obj_list:
                data_row_list = [
                    str(wakelock_obj.occur_seconds),
                    str(wakelock_obj.name),
                    str(wakelock_obj.duration_seconds),
                    str(wakelock_obj.start_dump_str),
                    str(wakelock_obj.end_dump_str),
                    str(wakelock_obj.end_seconds)
                ]
                csv_write.writerow(data_row_list)
        csv2html(file_name, html_name)
        os.remove(file_name)
        self.wakelock_times = len(wakelock_obj_list)
        if len(wakelock_obj_list) > 0:
            wakelock_1h_count = 0
            for wake_lock_obj in wakelock_obj_list:
                if wake_lock_obj.duration_seconds > 3600 * 1000:
                    wakelock_1h_count = +1

    # TODO： wakeup，唤醒次数/小时 是否大于10次
    def wakeup_times_jubge(self):
        wakeup_obj_list = self.analyze_dump_obj.wakeup_obj_list
        file_name = os.path.join(self.outfile_path, "wakeUp.csv")
        html_name = os.path.join(self.outfile_path, "wakeUp.html")
        csv_head_list = ['occur_seconds', 'wakeup_name', 'duration_time(ms)', 'start_dump_str', 'end_dump_str', 'end_seconds']
        create_csv(file_name, csv_head_list)
        # 将信息写入csv文件
        with open(file_name, 'a+') as f:
            csv_write = csv.writer(f)
            for wakeup_obj in wakeup_obj_list:
                data_row_list = [
                    str(wakeup_obj.occur_seconds),
                    str(wakeup_obj.wakeup_name),
                    str(wakeup_obj.duration_seconds),
                    str(wakeup_obj.dump_str),
                    str(wakeup_obj.end_dump_str),
                    str(wakeup_obj.end_seconds)
                ]
                csv_write.writerow(data_row_list)
        csv2html(file_name, html_name)
        os.remove(file_name)

        self.wakeup_times = len(wakeup_obj_list)
        wakeup_tag = "唤醒次数/H"
        wakeup_limit_time = 10
        # 判断wakeup是否一小时大于10次
        self.times_decide_hour(self.wakeup_times, wakeup_obj_list, wakeup_limit_time, self.bugreport_hours, wakeup_tag)

    # TODO: 判断作业间隔<=30s的次数，及不合格的dump str
    def job_interval_jubge(self):
        job_obj_list = self.analyze_dump_obj.job_obj_list
        file_name = os.path.join(self.outfile_path, "jobScheduler.csv")
        html_name = os.path.join(self.outfile_path, "jobScheduler.html")
        csv_head_list = ['occur_seconds', 'name', 'duration_time(ms)', 'start_dump_str', 'end_dump_str', 'end_seconds']
        create_csv(file_name, csv_head_list)
        # 将信息写入csv文件
        with open(file_name, 'a+') as f:
            csv_write = csv.writer(f)
            for job_obj in job_obj_list:
                data_row_list = [
                    str(job_obj.occur_seconds),
                    str(job_obj.name),
                    str(job_obj.duration_seconds),
                    str(job_obj.start_dump_str),
                    str(job_obj.end_dump_str),
                    str(job_obj.end_seconds)
                ]
                csv_write.writerow(data_row_list)
        csv2html(file_name, html_name)
        os.remove(file_name)

        self.job_times = len(job_obj_list)
        job_seconds_limit = 30
        job_tag = "作业间隔<=30s"
        self.time_interval_limit(self.job_times, job_obj_list, job_seconds_limit, job_tag)

    # TODO: 判断 调度同步时间间隔<30s的次数，及不合格的dump str SyncManager
    def sync_interval_jubge(self):
        sync_obj_list = self.analyze_dump_obj.sync_obj_list

        file_name = os.path.join(self.outfile_path, "syncManager.csv")
        html_name = os.path.join(self.outfile_path, "syncManager.html")
        csv_head_list = ['occur_seconds', 'name', 'duration_time(ms)', 'start_dump_str', 'end_dump_str', 'end_seconds']
        create_csv(file_name, csv_head_list)
        # 将信息写入csv文件
        with open(file_name, 'a+') as f:
            csv_write = csv.writer(f)
            for sync_obj in sync_obj_list:
                data_row_list = [
                    str(sync_obj.occur_seconds),
                    str(sync_obj.name),
                    str(sync_obj.duration_seconds),
                    str(sync_obj.start_dump_str),
                    str(sync_obj.end_dump_str),
                    str(sync_obj.end_seconds)
                ]
                csv_write.writerow(data_row_list)
        csv2html(file_name, html_name)
        os.remove(file_name)

        self.sync_times = len(sync_obj_list)
        sync_seconds_limit = 30
        sync_tag = "调度同步时间间隔<30s"
        self.time_interval_limit(self.sync_times, sync_obj_list, sync_seconds_limit, sync_tag)