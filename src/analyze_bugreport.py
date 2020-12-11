# -*-coding:utf-8-*-
import re
import os

from loguru import logger

from src import config


class AnalyzeDump(object):
    def __init__(self, app_uid):
        self.app_uid = app_uid
        # 电量相关参数
        self.mobile_power_capacity = None
        self.app_power_used = None
        self.app_power_used_Percent = None
        self.app_power_used_line = None
        self.network_trffic = None
        self.battery_summary = ''
        # 文件路径
        self.path = config.FILE_PATH
        self.dump_of_batterystats_path = os.path.join(self.path, 'dump_of_batterystats.txt')
        self.wakeup_reasons_path = os.path.join(self.path, 'wakeup_reasons.txt')
        self.power_used_path = os.path.join(self.path, 'power_used.txt')
        self.pid_battery_info_path = os.path.join(self.path, 'pid_battery_info.txt')
        # dump、wakeup list
        self.current_wakeup_list = self.get_list(self.wakeup_reasons_path)
        self.current_dump_list = self.get_list(self.dump_of_batterystats_path)
        self.power_used_list = self.get_list(self.power_used_path)
        # 需要匹配的字符串
        self.start_wifi_scan = "+wifi_scan"
        self.end_wifi_scan = "-wifi_scan"
        self.wifi_scan_str = '+wifi_scan'
        self.start_wake_lock_str1 = '+wake_lock_in=' + self.app_uid
        self.end_wake_lock_str1 = '-wake_lock_in=' + self.app_uid
        self.start_wake_lock_str2 = '+wake_lock=' + self.app_uid
        self.end_wake_lock_str2 = '-wake_lock'

        self.wakeup_str1 = 'walarm'
        self.start_wakeup_str = '+alarm=' + self.app_uid
        self.end_wakeup_str = '-alarm=' + self.app_uid
        self.start_job_str = '+job=' + self.app_uid
        self.end_job_str = '-job=' + self.app_uid
        self.start_sync_str = '+sync=' + self.app_uid
        self.end_sync_str = '-sync=' + self.app_uid

        # 处理后生成的各指标list
        self.wifi_scan_obj_list = []
        self.wakeup_obj_list = []
        self.wakelock_obj_list = []
        self.job_obj_list = []
        self.job_obj_temp_list = list()
        self.sync_obj_list = []

        # 保存指标名称的list
        self.wakeup_name_list = []
        self.wakelock_name_list = []
        self.job_name_list = []
        self.sync_name_list = []

    # 分析dump_of_batterystats.txt文件
    def analyze_dump_list(self):
        # 临时变量
        wake_lock_obj = None
        wake_up_obj = None
        job_obj = None
        sync_obj = None
        new_wakelock = False
        new_wakeup = False
        new_job_bool = False
        new_sync_bool = False
        wifi_scan_bool = False
        wifi_scan_add_bool1 = False
        wifi_scan_add_bool2 = False
        wifi_scan_count = 0
        add_wakelock_count = 0
        minus_wakelock_count = 0
        minus_wakeup_count = 0
        add_job_count = 0
        minus_job_count = 0
        add_sync_count = 0
        minus_sync_count = 0
        for str in self.current_dump_list:
            dump_str = str.strip()

            # 根据dump_str，创建wifi scan对象，并放到wifi_scan_list中
            if self.wifi_scan_str in dump_str:
                wifi_scan_add_bool = True
                self.create_wifi_scan_obj(dump_str)

            # 补充wake_lock_obj
            if new_wakelock and (self.end_wake_lock_str1 in dump_str or self.end_wake_lock_str2 in dump_str):
                minus_wakelock_count += 1
                self.complete_wake_lock_obj(wake_lock_obj, dump_str)
                new_wakelock = False
                wake_lock_obj = None
                wifi_scan_add_bool = True

            # 创建wake lock对象
            if self.start_wake_lock_str1 in dump_str or self.start_wake_lock_str2 in dump_str:
                add_wakelock_count += 1
                wake_lock_obj = self.create_wake_lock_obj(dump_str)
                new_wakelock = True

            # 补充wake up 对象
            if new_wakeup and self.wakeup_str1 in dump_str and self.end_wakeup_str in dump_str:
                minus_wakeup_count += 1
                self.complete_wake_up_obj(wake_up_obj, dump_str)
                new_wakeup = False
                wake_up_obj = None
                wifi_scan_add_bool = True

            # 创建wake up对象
            if self.wakeup_str1 in dump_str and self.start_wakeup_str in dump_str:
                wake_up_obj = self.create_wakeup_obj(dump_str)
                new_wakeup = True

            # 补充job_obj
            if self.end_job_str in dump_str:
                minus_job_count += 1
                job_obj = self.complete_job_obj(job_obj, dump_str)
                new_job_bool = False
                job_obj = None
                wifi_scan_add_bool = True

            # 创建job对象
            if self.start_job_str in dump_str:
                add_job_count += 1
                job_obj = self.create_job_obj(dump_str)
                new_job_bool = True

            # 补充sync_obj
            if new_sync_bool and self.end_sync_str in dump_str:
                minus_sync_count += 1
                self.complete_sync_obj(sync_obj, dump_str)
                new_sync_bool = False
                sync_obj = None
                wifi_scan_add_bool = True

            # 创建sync对象
            if self.start_sync_str in dump_str:
                add_sync_count += 1
                sync_obj = self.create_sync_obj(dump_str)
                new_sync_bool = True

            # 计算wifi扫描
            if self.start_wifi_scan in dump_str:
                wifi_scan_bool = True

            if "+" in dump_str and self.app_uid in dump_str and wifi_scan_bool:
                wifi_scan_add_bool1 = True

            if "-" in dump_str and self.app_uid in dump_str and wifi_scan_add_bool1:
                wifi_scan_add_bool2 = True

            if wifi_scan_bool and self.end_wifi_scan in dump_str:
                if wifi_scan_add_bool1 and wifi_scan_add_bool2:
                    wifi_scan_count = wifi_scan_count + 1
                wifi_scan_add_bool1 = False
                wifi_scan_add_bool2 = False
                wifi_scan_bool = False

    def analyze_power_used(self):
        pattern_count = 0
        for line_power_used in self.power_used_list:
            if "Capacity" in line_power_used:
                capacity_pattern_str = 'Capacity:(.*),\sComputed'
                capacity_pattern = re.compile(capacity_pattern_str)
                # 获取Capacity的值
                capacity_str = "".join(capacity_pattern.findall(line_power_used))
                # 手机电池容量
                self.mobile_power_capacity = float(capacity_str)
                pattern_count += 1
            if self.app_uid in line_power_used:
                app_power_used_pattern_str = self.app_uid+':\s(.*)\s\('
                app_power_used_pattern = re.compile(app_power_used_pattern_str)
                # 获取app使用的电量
                app_power_used_str = "".join(app_power_used_pattern.findall(line_power_used))
                # app使用电量
                app_power_used_str = app_power_used_str.split()
                if len(app_power_used_str) > 0:
                    self.app_power_used = float(app_power_used_str[0])

                self.app_power_used_line = line_power_used.strip()
                pattern_count += 1
            if pattern_count == 2:
                break
        try:
            app_power_used_Percent1 = (self.app_power_used / self.mobile_power_capacity) *100
            app_power_used_Percent2 = str(round(app_power_used_Percent1, 2)) + '%'
            self.app_power_used_Percent = app_power_used_Percent2

            statistics_obj = re.match(r'.*\((.*)\)', self.app_power_used_line)
            self.app_power_used_line = statistics_obj.groups()[0]
        except:
            self.app_power_used_Percent = None
        # logger.info("耗电百分比：", self.app_power_used_Percent, "; app耗电量：", self.app_power_used, ", 手机电池容量：", self.mobile_power_capacity)
        # logger.info("耗电详情：", self.app_power_used_line)

    # 获取耗电摘要
    def get_battery_summary(self, uid_list):
        switch = False
        for line in open(self.pid_battery_info_path):
            if self.app_uid in line:
                switch = True
                continue
            if switch and line:
                if line.strip().replace(':', '') in uid_list:
                    break
                else:
                    self.battery_summary = self.battery_summary + '\n' + line
                    if self.network_trffic is None and 'network' in line and 'received' in line and 'sent' in line:
                        self.network_trffic = re.match(r'.*network:(.*)\(', line).groups()[0].strip()

        return self.battery_summary

    # 根据dump_str，创建wifi scan对象，并放到wifi_scan_list中
    def create_wifi_scan_obj(self, dump_str):
        # 获取wifi扫描次数
        if self.wifi_scan_str in dump_str and self.app_uid in dump_str:
            # 获取时间戳，并转换为秒
            occur_seconds = self.seconds_value_of(dump_str)
            wifi_scan_obj = WifiScanClass(occur_seconds, dump_str)
            self.wifi_scan_obj_list.append(wifi_scan_obj)

    # 根据dump_str,生成wakeup obj
    def create_wakeup_obj(self, dump_str):
        wakeup_name_pattern_str = '\*walarm\*:(.*)\"'
        wakeup_name_pattern = re.compile(wakeup_name_pattern_str)
        wakeup_name = ("".join(wakeup_name_pattern.findall(dump_str)))
        wakeup_name = wakeup_name.replace('\'', '').strip()
        wakeup_occur_seconds = self.seconds_value_of(dump_str)
        wake_up_obj = WakeupClass(wakeup_name, wakeup_occur_seconds, dump_str)
        self.wakeup_name_list.append(wakeup_name)

        return wake_up_obj

    def complete_wake_up_obj(self, wake_up_obj, dump_str):
        wakeup_end_name_pattern_str = '\*walarm\*:(.*)\"'
        wakeup_end_name_pattern = re.compile(wakeup_end_name_pattern_str)
        wakeup_end_name = ("".join(wakeup_end_name_pattern.findall(dump_str)))
        wakeup_end_name = wakeup_end_name.replace('\'', '').strip()

        # 比较+wake_lock_name 和 -wake_lock_name
        if wakeup_end_name in self.wakeup_name_list:
            # 获取wake_lock结束时间戳，并转换为秒
            wake_up_end_time_str = self.seconds_value_of(dump_str)
            wake_up_obj.end_seconds = wake_up_end_time_str
            wake_up_obj.end_dump_str = dump_str
            wake_up_obj.duration_seconds = (wake_up_obj.end_seconds - wake_up_obj.occur_seconds)*1000
            self.wakeup_obj_list.append(wake_up_obj)
            self.wakeup_name_list.remove(wakeup_end_name)
        else:
            logger.warning(wakeup_end_name, "不在wakelock_name_list中")
        return wake_up_obj

    # 根据dump_str, 创建wake lock对象
    def create_wake_lock_obj(self, dump_str):
        # 获取时间戳，并转换为秒
        start_occur_seconds = self.seconds_value_of(dump_str)
        wakelock_name_pattern_str = '\+(wake_lock_in=.*)"'
        wakelock_name_pattern = re.compile(wakelock_name_pattern_str)
        wakelock_name = "".join(wakelock_name_pattern.findall(dump_str))
        wake_lock_obj = WakeLockClass(wakelock_name, start_occur_seconds, dump_str)
        self.wakelock_name_list.append(wakelock_name)
        return wake_lock_obj

    # 根据dump_str, 补充wake lock对象
    def complete_wake_lock_obj(self, wake_lock_obj, dump_str):
        # 获取-wake_lock
        wake_lock_end_name_pattern_str = '\-(wake_lock_in=.*)"'
        wake_lock_name_pattern = re.compile(wake_lock_end_name_pattern_str)
        wake_lock_end_name = "".join(wake_lock_name_pattern.findall(dump_str))
        # 比较+wake_lock_name 和 -wake_lock_name
        if wake_lock_end_name in self.wakelock_name_list:
            # 获取wake_lock结束时间戳，并转换为秒
            wake_lock_end_time_str = self.seconds_value_of(dump_str)
            wake_lock_obj.end_seconds = wake_lock_end_time_str
            wake_lock_obj.end_dump_str = dump_str
            wake_lock_obj.duration_seconds = (wake_lock_obj.end_seconds - wake_lock_obj.occur_seconds)*1000
            self.wakelock_obj_list.append(wake_lock_obj)
            self.wakelock_name_list.remove(wake_lock_end_name)
        else:
            logger.info(wake_lock_end_name, "不在wakelock_name_list中")
        return wake_lock_obj

    # 根据dump_str, 创建job对象
    def create_job_obj(self, dump_str):
        # 获取时间戳，并转换为秒
        job_start_seconds = self.seconds_value_of(dump_str)
        job_name_pattern_str = '\+job=.*:"(.*)"'
        job_name_pattern = re.compile(job_name_pattern_str)
        job_name = "".join(job_name_pattern.findall(dump_str))
        job_obj = ScheduledJobClass(job_name, job_start_seconds, dump_str)
        self.job_obj_list.append(job_obj)

        return job_obj

    # 根据dump_str, 补充job对象
    def complete_job_obj(self, job_obj, dump_str):
        # 获取job_end_name
        job_end_name_pattern_str = '\-job=.*:"(.*)"'
        job_end_name_pattern = re.compile(job_end_name_pattern_str)
        job_end_name = "".join(job_end_name_pattern.findall(dump_str))
        for job_obj in self.job_obj_list:
            if (job_end_name in job_obj.name) and (job_obj.duration_seconds is None):
                # 获取job结束时间戳，并转换为秒
                job_end_seconds = self.seconds_value_of(dump_str)
                job_obj.end_seconds = job_end_seconds
                job_obj.end_dump_str = dump_str
                job_obj.duration_seconds = (job_obj.end_seconds - job_obj.occur_seconds)*1000
                break
        return job_obj

    # 根据dump_str, 创建Sync对象
    def create_sync_obj(self, dump_str):
        # 获取时间戳，并转换为秒
        sync_start_seconds = self.seconds_value_of(dump_str)
        # 获取sync name
        sync_name_pattern_str = '\+sync=.*:"(.*)"'
        sync_name_pattern = re.compile(sync_name_pattern_str)
        sync_name = "".join(sync_name_pattern.findall(dump_str))
        # 创建SyncManager_Class对象
        sync_obj = SyncManagerClass(sync_name, sync_start_seconds, dump_str)
        self.sync_name_list.append(sync_name)
        return sync_obj

    # 根据dump_str, 补充sync对象
    def complete_sync_obj(self, sync_obj, dump_str):
        # 获取-wake_lock
        sync_end_name_pattern_str = '\-sync=.*:"(.*)"'
        sync_end_name_pattern = re.compile(sync_end_name_pattern_str)
        sync_end_name = "".join(sync_end_name_pattern.findall(dump_str))
        # 比较+sync_end_name 和 -sync_start_name
        if sync_end_name in self.sync_name_list:
            # 获取sync结束时间戳，并转换为秒
            sync_end_seconds = self.seconds_value_of(dump_str)
            sync_obj.end_seconds = sync_end_seconds
            sync_obj.end_dump_str = dump_str
            sync_obj.duration_seconds = (sync_obj.end_seconds - sync_obj.occur_seconds)*1000
            self.sync_obj_list.append(sync_obj)
            self.sync_name_list.remove(sync_end_name)
        else:
            logger.warning(sync_end_name, "不在sync_name_list中")
        return sync_obj

    # 时间戳转换为时间
    @staticmethod
    def seconds_value_of(dump_str):
        time_pattern_str = '\++(.*?)\s+\(+'
        time_pattern = re.compile(time_pattern_str)
        # 获取wake_lock开始时间戳
        time_str = "".join(time_pattern.findall(dump_str))
        # 将时间戳转换为秒
        time_list = re.findall(r"\d+\.?\d*", time_str)
        count = len(time_list)
        seconds_time = None
        if count == 1:
            seconds_time = int(time_list[-1]) / 1000.000
        elif count == 2:
            seconds = int(time_list[-2])
            ms = int(time_list[-1])
            seconds_time = seconds + ms / 1000.000
        elif count == 3:
            minutes = int(time_list[-3])
            seconds = int(time_list[-2])
            ms = int(time_list[-1])
            seconds_time = minutes * 60 + seconds + ms / 1000.000
        elif count == 4:
            hours = int(time_list[0])
            minutes = int(time_list[-3])
            seconds = int(time_list[-2])
            ms = int(time_list[-1])
            seconds_time = hours * 60 * 60 + minutes * 60 + seconds + ms / 1000.000
        elif count == 5:
            days = int(time_list[0])
            hours = int(time_list[-4])
            minutes = int(time_list[-3])
            seconds = int(time_list[-2])
            ms = int(time_list[-1])
            seconds_time = days * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60 + seconds + ms / 1000.000
        else:
            logger.info("===========时间戳格式有错", time_str, "===============")

        return seconds_time

    # 根据文件路径，获取list
    @staticmethod
    def get_list(file_path):
        with open(file_path, 'r') as f1:
            file_list = f1.readlines()
        return file_list


class WifiScanClass(object):
    def __init__(self, occur_seconds, dump_str):
        self.occur_seconds = occur_seconds
        self.dump_str = dump_str


class WakeupClass(object):
    def __init__(self, wakeup_name, occur_seconds, start_dump_str):
        self.wakeup_name = wakeup_name
        self.occur_seconds = occur_seconds
        self.end_seconds = None
        self.dump_str = start_dump_str
        self.end_dump_str = None
        self.duration_seconds = None


class WakeLockClass(object):
    def __init__(self, name, occur_seconds, start_dump_str):
        self.name = name
        self.occur_seconds = occur_seconds
        self.end_seconds = None
        self.start_dump_str = start_dump_str
        self.end_dump_str = None
        self.duration_seconds = None


class ScheduledJobClass(object):
    def __init__(self, name, occur_seconds, start_dump_str):
        self.name = name
        self.occur_seconds = occur_seconds
        self.end_seconds = None
        self.start_dump_str = start_dump_str
        self.end_dump_str = None
        self.duration_seconds = None


class SyncManagerClass(object):
    def __init__(self, name, occur_seconds, start_dump_str):
        self.name = name
        self.occur_seconds = occur_seconds
        self.end_seconds = None
        self.start_dump_str = start_dump_str
        self.end_dump_str = None
        self.duration_seconds = None

class PowerUsedClass(object):
    def __init__(self, power_used_Percent, power_used, dump_str):
        self.power_used_Percent = power_used_Percent
        self.power_used = power_used
        self.dump_str = dump_str