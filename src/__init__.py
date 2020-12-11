import os
import platform
import webbrowser
import zipfile
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from src import config


class AppInfo(object):
    def __init__(self, app_name, app_uid):
        self.app_name = app_name
        self.app_uid = app_uid


def create_report(fname, context, template):
    """
    生成html报告
    :param fname: 要生成的html文件
    :param context: 输入参数
    :param template: 模版文件
    :return:
    """
    TEMPLATE_ENVIRONMENT = Environment(
        autoescape=False,
        loader=FileSystemLoader(config.TEMPLATES_PATH),
        trim_blocks=False)
    # reload(sys)  # reload 才能调用 setdefaultencoding 方法
    # sys.setdefaultencoding('utf-8')  # 设置 'utf-8'
    with open(fname, 'w') as f:
        html = TEMPLATE_ENVIRONMENT.get_template(template).render(context)
        f.write(html)
    if 'index.html' in fname:
        if 'windows' in platform.system().lower() or 'linux' in platform.system().lower():
            webbrowser.open_new_tab(fname)
        else:
            webbrowser.open_new_tab('file://' + fname)


def unzip_file(zip_src, dst_dir):
    """
    解压.zip，并输出bugreport.txt
    :param zip_src: zip文件全路径
    :param dst_dir: 解压后存放路径
    :return:
    """
    r = zipfile.is_zipfile(zip_src)
    if r:
        logger.info('解压zip文件: %s' % zip_src)
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
        bugreport_txt = os.path.basename(zip_src).replace('.zip', '.txt')
    else:
        bugreport_txt = os.path.basename(zip_src)
    return bugreport_txt


def csv2html(csv_file, html_file):
    from csvtotable import convert
    content = convert.convert(csv_file, delimiter=",", quotechar='"', display_length=-1, overwrite=False, serve=False,
                              pagination=True, virtual_scroll=1000, no_header=False, export=True,
                              export_options=["copy", "csv", "json", "print"])
    convert.save(html_file, content)


logger:logger
