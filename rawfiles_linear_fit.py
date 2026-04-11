import math
import sys
import os
import numpy as np
#import pandas as pd
import threading
from threading import Thread
import tkinter as tk
from tkinter import filedialog
import glob
import gc
#import pyqtgraph 
import matplotlib.pyplot as plt
from recvfrom_rawfiles import recvfrom_rawdatafiles as rr
import functions as fc


class Rawfiles_Linear_fit(Thread):#输入文件名及路径，读取数据，解包，拟合
    def __init__(self, 
                 deltaposi = 0,
                 linear_fit_ylist = (-300,300)):
        Thread.__init__(self)
        self.deltaposi = deltaposi
        self.linear_fit_ylist = linear_fit_ylist

    def run(self):
        rr1=rr()
        rr1.run()
        rr1.conclude()
        rr2=rr()
        rr2.run()
        rr2.conclude()

        chns_cells_fit_para=[]
        print(f"正在进行线性拟合")

        for n_chn in range(31):
            xlist=[]
            groups_onechn1,stopposi1=fc.pure_groups(n_chn, rr1.DRSdata)
            groups_onechn2,stopposi2=fc.pure_groups(n_chn, rr2.DRSdata)
            groups_onechn1[:,:5]=0xFFFF
            groups_onechn1[:,1019:]=0xFFFF
            groups_onechn2[:,:5]=0xFFFF
            groups_onechn2[:,1019:]=0xFFFF
            for n_group in range(len(groups_onechn1)):
                groups_onechn1[n_group]=fc.timeorder_to_cellorder(groups_onechn1[n_group],stopposi1[n_group])
            for n_group in range(len(groups_onechn2)):
                groups_onechn2[n_group]=fc.timeorder_to_cellorder(groups_onechn2[n_group],stopposi2[n_group])
            for i_cell in range(1024):#筛选
                usefuldata_onecell=[]
                for i in range(len(groups_onechn1)):
                    data=groups_onechn1[i][i_cell]
                    if data!=0xFFFF:
                        usefuldata_onecell.append(data)
                x1=np.mean(np.array(usefuldata_onecell))
                usefuldata_onecell=[]
                for i in range(len(groups_onechn2)):
                    data=groups_onechn2[i][i_cell]
                    if data!=0xFFFF:
                        usefuldata_onecell.append(data)
                x2=np.mean(np.array(usefuldata_onecell))
                xlist.append((x1,x2))
            chns_cells_fit_para.append(fc.linear_fit(xlist, self.linear_fit_ylist))
            if(n_chn==30):
                chns_cells_fit_para.append(fc.linear_fit(xlist, self.linear_fit_ylist))
        if(len(self.linear_fit_ylist)==2):
            fc.save_npy(np.array(chns_cells_fit_para), "linear_fit_para_31chn.npy")#这里改用numpy存储了
        else:
            print(f"请输入形如（y1，y2）")

    #老函数
    def Data_allfiles_cells_mean(self):#对每个cell筛选数据，同时求筛选后的平均
        self.all_files_cells_DC_mean = []
        self.all_files_cells_useful_data = []
        self.all_files_cells_useful_data_diff = []
        for i_file in range(len(self.file_paths)):
            print(f"正在筛选第{i_file+1}/{len(self.file_paths)}个文件的数据")
            all_cell_DC_mean = []#各cell的平均输出数值（有筛选）
            all_cell_useful_data = []#各cell的输出数值（有筛选）
            all_cell_useful_data_diff = []#各cell的输出数值残差情况（有筛选）
            for i_cell in range(1024):
                counts, bin_edges = np.histogram(np.array(self.all_reshaped_data_cellorder0[i_file])[:,i_cell], bins=10)#做直方图找大概位置，多筛一轮数据////舍弃了

                most_count_bin_index = counts.argmax()  
                bins_center = (bin_edges[:-1] + bin_edges[1:]) / 2 #每个bin的中心点
                one_cell_DC_mean_reference = bins_center[most_count_bin_index] 
                #一轮筛选，求均值
                one_cell_useful_data = []
                for i_group in range(len(self.group_head_posi[i_file])):
                    posi_diff = int(abs(int(self.all_files_groups_begin_posi[i_file][i_group])-i_cell+1)%1024)#!!!!!!!!!!!!!!!!!!!!!!!!!
                    the_data = self.all_reshaped_data_cellorder0[i_file][i_group][i_cell]
                    data_diff = abs(the_data-one_cell_DC_mean_reference)##cell的位置和group开头的位置是否过近则舍弃///读出数值与总均值误差过大则舍弃
                    if(posi_diff>21 and posi_diff<1003 and data_diff<500):#
                        one_cell_useful_data.append(the_data)
                one_cell_DC_mean = np.array(one_cell_useful_data).mean()#??????????????????????
                #二轮筛选，求均值
                one_cell_useful_data_2 = []
                for i_group in range(len(self.group_head_posi[i_file])):
                    posi_diff = int(abs(int(self.all_files_groups_begin_posi[i_file][i_group])-i_cell+1)%1024)#cell的位置和group开头的位置是否过近则舍弃////////此逻辑可能有问题！！！！！！！！！！！
                    the_data = self.all_reshaped_data_cellorder0[i_file][i_group][i_cell]
                    data_diff = abs(the_data-one_cell_DC_mean)#读出数值与总均值误差过大则舍弃
                    if(posi_diff>21 and posi_diff<1003 and data_diff<100):#
                        one_cell_useful_data_2.append(the_data)
                one_cell_DC_mean_2 = np.array(one_cell_useful_data_2).mean()
                all_cell_DC_mean.append(one_cell_DC_mean_2)#
                all_cell_useful_data.append(one_cell_useful_data)#二维数组：每个cell*每个有效数据
                all_cell_useful_data_diff.append(one_cell_useful_data - one_cell_DC_mean_2)#二维数组：每个cell*每个有效数据的残差//????????????????????

            self.all_files_cells_DC_mean.append(all_cell_DC_mean)#//////////////////二维数组：每个文件*每个cell筛选后的平均输出值
            self.all_files_cells_useful_data.append(all_cell_useful_data)#//////////三维数组：每个文件*每个cell*每个有效数据
            self.all_files_cells_useful_data_diff.append(all_cell_useful_data_diff)#三维数组：每个文件*每个cell*每个有效数据的残差
     
    def Graph_onecell(self, i_file, i_cell):#画图：频数图
        counts, bin_edges = np.histogram(np.array(self.all_files_cells_useful_data[i_file][i_cell]), bins=10)
        bins_center = (bin_edges[:-1] + bin_edges[1:]) / 2
        plt.figure(figsize=(10,7))
        plt.plot(bins_center, 
                 counts, 
                 marker='o', 
                 color='blue', 
                 linewidth=1, 
                 label=f"第{i_cell+1}个cell的数据")
        plt.legend()
        plt.show()

if __name__ == '__main__':#////////单独运行时先手动选择文件再运行
    DCdata_read = Rawfiles_Linear_fit(deltaposi = 0,
                               linear_fit_ylist = (-126,-326))
    
    DCdata_read.run()
