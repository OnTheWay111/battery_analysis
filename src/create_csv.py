# -*-coding:utf-8-*-
import csv


def create_csv(filename, csv_head_list):
    with open(filename,'w', newline="") as fwd:
        fwdcsv = csv.DictWriter(fwd, fieldnames=csv_head_list)
        fwdcsv.writeheader()


def write_csv(file_name, data_row_list):
    with open(file_name,'a+') as f:
        csv_write = csv.writer(f)
        csv_write.writerow(data_row_list)