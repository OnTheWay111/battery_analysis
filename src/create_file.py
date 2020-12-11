# -*-coding:utf-8-*-
import os
import re

from src import AppInfo, config, logger


class FileCreate(object):
    def __init__(self, bugreport_name):
        self.path = config.FILE_PATH
        self.bugreport_name = bugreport_name
        self.bugreport_time_str = ''
        self.bugreport_path = os.path.join(self.path, self.bugreport_name)
        self.dump_of_batterystats_path = os.path.join(self.path, 'dump_of_batterystats.txt')
        self.processes_path = os.path.join(self.path, 'processes.txt')
        self.wakeup_reasons_path = os.path.join(self.path, 'wakeup_reasons.txt')
        self.power_used_path = os.path.join(self.path, 'power_used.txt')
        self.dump_of_service_appops_path = os.path.join(self.path, 'dump_of_service_appops.txt')
        self.pid_battery_info_path = os.path.join(self.path, 'pid_battery_info.txt')
        self.pkg_info_file = os.path.join(self.path, 'pkg_info.txt')
        self.bugreport_seconds = 0
        self.current_list = []
        self.current_wakeup_list = []
        self.dump_of_batterystats_list = []
        self.uid_list = list()  # uid列表
        self.get_all_list()  # bugreport列表化
        self.write_dump_of_batterystats()  # 创建batterystats文件
        self.write_processes()  # 创建app进程信息文件
        self.write_wakeup_reasons()  # 创建wakeup reson文件
        self.write_power_used()  # 创建耗电统计
        self.write_dump_of_service_appops()  # service信息
        self.get_bugreport_time()  # 获取bugreport 时间
        self.write_pid_battery_info()  # 获取pid battery info
        self.write_pkg_info()  # 获取pkg info

    # 将bugreport.txt中的所有行放到链表self.current_link_list中
    def get_all_list(self):
        with open(self.bugreport_path, 'rb') as f1:
            list1 = f1.readlines()
            self.current_list = list1
        return self.current_list

    # 根据文件路径，获取list
    @staticmethod
    def get_list(file_path):
        with open(file_path, 'r') as f1:
            file_list = f1.readlines()
        return file_list

    # 获取bugreport采样时间
    def get_bugreport_time(self):
        # 获取bugreport中的DUMP OF SERVICE batterystats
        self.dump_of_batterystats_list = self.get_list(self.dump_of_batterystats_path)
        self.dump_of_batterystats_list = [ line for line in self.dump_of_batterystats_list if line.strip()]
        time_pattern_str = '\++(.*?)\s+\(+'
        time_pattern = re.compile(time_pattern_str)
        key = -1
        while True and len(self.dump_of_batterystats_list) > 0:
            last_line = self.dump_of_batterystats_list[key]
            # 获取wake_lock开始时间戳
            self.bugreport_time_str = "".join(time_pattern.findall(last_line))
            # 将时间戳转换为秒
            self.bugreport_seconds = self.seconds_value_of(last_line)
            if self.bugreport_seconds:
                break
            else:
                key = key - 1
        logger.info("本次bugreport持续时长：" + str(self.bugreport_time_str) + "换算为秒：" + str(self.bugreport_seconds))

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

    #
    def write_dump_of_service_appops(self):
        f = open(self.dump_of_service_appops_path, 'w')
        f.truncate()
        str1 = "DUMP OF SERVICE appops"
        str2 = "DUMP OF SERVICE appwidget"
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8","ignore")
            if str1 in str_line:
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line)>2:
                f.write(str_line)
        f.close()

    # batterystats文件创建
    def write_dump_of_batterystats(self):
        f = open(self.dump_of_batterystats_path, 'w')
        f.truncate()
        str1 = "DUMP OF SERVICE batterystats"
        str2 = "Per-PID Stats"
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8","ignore")
            if str1 in str_line:
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line)>2 and '+' in str_line:
                f.write(str_line)
        f.close()

    # 耗电统计
    def write_power_used(self):
        f = open(self.power_used_path, 'w')
        f.truncate()
        str1 = "Estimated power use"
        str2 = "All kernel wake locks"
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8","ignore")
            if str1 in str_line:
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line)>2:
                f.write(str_line)
        f.close()

    # app进程信息
    def write_processes(self):
        f = open(self.processes_path, 'w')
        f.truncate()
        str1 = "PROCESSES AND THREADS"
        # str1 = "------ BLOCKED PROCESS WAIT-CHANNELS ------"
        str2 = "PROCESSES (SELINUX LABELS)"
        # str2 = "------ PROCESS TIMES (pid cmd user system iowait+percentage) ------"
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8", "ignore")
            if str1 in str_line:
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line)>2:
                f.write(str_line)
        f.close()

    # wakeup reason
    def write_wakeup_reasons(self):
        f = open(self.wakeup_reasons_path, 'w')
        f.truncate()
        str1 = "All wakeup reasons"
        str2 = "Wi-Fi network"
        is_print = False
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8", "ignore")
            if str1 in str_line:
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line)>2:
                if "Wakeup reason Abort" in str_line:
                    f.write(str_line)
                    if "times" in str_line:
                        pattern = re.compile('Wakeup reason Abort:(.*:?):')
                        child_action_text = pattern.findall(str_line)
                    else:
                        pattern = re.compile('Wakeup reason Abort:(.*:?):*realtime')
                        child_action_text = pattern.findall(str_line)
                    child_action_text = str(child_action_text).replace('[', '').replace(']', '').replace('\'', '').strip()
                    self.current_wakeup_list.append(child_action_text)
        f.close()

    # 根据self.processes_path文件，创建app_info
    def create_app_info(self, app_name):
        app_start_bool = False
        with open(self.processes_path, 'r') as f1:
            list1 = f1.readlines()
        for str_line in list1:
            if app_name in str_line:
                app_start_bool = True
                str_line_list = str_line.split()
                app_uid = str_line_list[0].replace('_', '')
                app_pid = str_line_list[1]
                app_info = AppInfo(app_name, app_uid)
                return app_info
        if not app_start_bool:
            return None

    # 根据self.dump_of_service_appops_path 创建app_info
    def create_app_info_appops(self, app_name):
        app_info = None
        with open(self.dump_of_service_appops_path, 'r') as f1:
            list1 = f1.readlines()
        for index in range(0, len(list1)-1):
            uid_str = list1[index]
            if ("Uid" in uid_str):
                app_uid_pattern_str = 'Uid\s(.*):'
                app_uid_pattern = re.compile(app_uid_pattern_str)
                app_uid = ("".join(app_uid_pattern.findall(uid_str)))
                if 'u' in app_uid:
                    self.uid_list.append(app_uid)
                for i in range(1,5):
                    pkg_str = list1[index+i]
                    if ("Package" in pkg_str) and (app_name+":" in pkg_str):
                        app_info = AppInfo(app_name, app_uid)
        return app_info

    def write_pid_battery_info(self):
        f = open(self.pid_battery_info_path, 'w')
        f.truncate()
        str0 = "0:"
        str1 = "CPU freqs"
        str2 = "UMP OF SERVICE bluetooth_manager"
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8", "ignore")
            if str1 in str_line or str0 == str_line.strip():
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line) > 2:
                f.write(str_line)

        f.close()

    def write_pkg_info(self):
        f = open(self.pkg_info_file, 'w')
        f.truncate()
        str1 = "Key Set Manager:"
        str2 = "Shared users:"
        is_print = False
        for line in self.current_list:
            str_line = line.decode("utf8", "ignore")
            if str1 in str_line:
                is_print = True
            elif str2 in str_line:
                break
            if is_print and len(str_line) > 2:
                f.write(str_line)

        f.close()

    # 获取app version
    def get_pkg_version(self, pkg_name):
        pkg_info = "Package [%s]" % pkg_name
        version_str = "versionName="
        flag = False
        with open(self.pkg_info_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if pkg_info in line:
                    flag = True
                if flag:
                    if version_str in line:
                        version_name = line.strip().replace(version_str, "")
                        return version_name
