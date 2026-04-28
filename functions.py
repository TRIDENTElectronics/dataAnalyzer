#此处存放各种小功能以便调用
import tkinter as tk
from tkinter import filedialog
import os
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from threading import Thread
from scipy.signal import firwin, freqz, lfilter

#输出当前时刻（字符串
def timestr():
    t = time.localtime()
    timestring= str(t.tm_year).zfill(4)+str(t.tm_mon).zfill(2)+str(t.tm_mday).zfill(2)+str(t.tm_hour).zfill(2)+str(t.tm_min).zfill(2)+str(t.tm_sec).zfill(2)
    return timestring

#/////////////////文件存取相关///////////////
#文件路径
#current_path = os.path.dirname(os.path.abspath(__file__))
#建文件夹
#filefold_path = os.path.join(current_path, filefoldname)
#if not os.path.exists(filefold_path):
#    os.makedirs(filefold_path)
#选数个文件
def select_files():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_paths = filedialog.askopenfilenames(title="选择.data文件,请选择同一目录下的文件", initialdir=current_path, filetypes=[("Data files", "*.data"), ("All files", "*.*")])
    if not file_paths:
        print("未选择文件")
        exit()
    filenum = len(file_paths)
    print(f"选择了 {filenum} 个文件")
    print(file_paths)
    return file_paths
#选一个文件
def select_file(ext="data"):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_path = filedialog.askopenfilename(title=f"选择.{ext}文件,请选择同一目录下的文件", initialdir=current_path, filetypes=[("Data files", "*."+ ext), ("All files", "*.*")])
    if not file_path:
        print("未选择文件")
        exit()
    print(f"选择了文件{file_path}")
    return file_path
#csv存储
def save_csv(data, filepath):
    df=pd.DataFrame(data)
    df.to_csv(filepath, index=False)
#csv高级存储
def Data_save_csv(data_to_save, 
                new_name:str = "", #强制确定文件名
                file_path_name:str = "", 
                prefix:str = "", 
                fmt='%f'):
    if new_name:
        new_filename = new_name
    else:
        base_name = os.path.basename(file_path_name)
        name_withoutext, ext =os.path.splitext(base_name)
        new_filename = f"{prefix}{name_withoutext}.csv"
    directory = os.path.dirname(file_path_name)
    if directory:
        new_filepath = os.path.join(directory, new_filename)
    else:
        new_filepath = new_filename
    np.savetxt(new_filepath, np.array(data_to_save), delimiter = ',',fmt = fmt)
    print(f"生成文件{new_filename}：存储到{directory}")
#csv读取
def read_csv(filepath):
    data = pd.read_csv(filepath)
    return data
#数组npy保存
def save_npy(data, filename):
    np.save(filename, data)
    print(f"数据已保存到 {filename}")
#数组npy读取
def read_npy(filename):
    data = np.load(filename)
    return data

#//////////////////绘图相关///////////////////
#画32通道波形大图
def graphs32(ylists, xlist = range(1024)):
    fig, axes = plt.subplots(nrows=4, ncols=8, figsize=(40, 20))
    for i in range(4):  #行
        for j in range(8):  #列
            ax = axes[i, j]
            ax.plot(xlist, ylists[i*8+j], color='blue', linewidth=1)
            ax.set_title(f'            chn{i*8+j}')
            ax.set_xlabel('ns')
            ax.set_ylabel('mV')
    plt.tight_layout()
    plt.show()
    plt.close("all")
#画单个波形
def Graph_group_data(thelist:list):
    print(f"正在绘图")
    plt.figure(figsize=(10,7))
    plt.plot(range(len(thelist)), 
                np.array(thelist), 
                marker='o', 
                color='blue', 
                linewidth=1, 
                label='one_group_data')
    plt.legend()
    plt.show()
#32直方图
def graphs32_histogram(tlist,bins=10):
    fig, axes = plt.subplots(nrows=4, ncols=8, figsize=(40, 20))
    for i in range(4):  #行
        for j in range(8):  #列
            if i*8+j<len(tlist):
                xlist=tlist[i*8+j]
            else:
                xlist=[1]*1024
            counts, bin_edges = np.histogram(np.array(xlist), bins=bins)
            bins_center = (bin_edges[:-1] + bin_edges[1:]) / 2

            ax = axes[i, j]
            ax.plot(bins_center, counts, color='blue', linewidth=1)
            ax.set_title(f'            chn{i*8+j}')
            ax.set_xlabel('ns')
            ax.set_ylabel('counts')
    plt.tight_layout()
    plt.show()
#直方图
def graph_histogram(tlist,bins=10):
    counts, bin_edges = np.histogram(np.array(tlist), bins=bins)
    bins_center = (bin_edges[:-1] + bin_edges[1:]) / 2
    plt.figure(figsize=(10,7))
    plt.plot(bins_center, 
                counts, 
                marker='o', 
                color='blue', 
                linewidth=1, 
                label="")
    plt.legend()
    plt.show()

#主动进度条，回车看进度
class process_show(Thread):
    def __init__(self, length):
        Thread.__init__(self)
        self.length=length
        self.rest=length
        self.stopflag=False

    def run(self):
        while not(self.stopflag):
            input()
            print(f"进度{(1-self.rest/1./self.length)*100}%")
#自动进度条
class process():
    def __init__(self, length):
        self.length=length
        self.rest=length
        self.process=0

    def layout(self):
        nowpc = (1-self.rest/1./self.length)*100
        if nowpc>=self.process:
            print(f"进度{self.process}%")
            self.process+=10

#//////////////////数据变换工具//////////////////
#线性拟合
def linear_fit(x:list, y:list):
    if(len(y) != 2 or len(x[0]) != 2):
        print(f"线性拟合时x/y数量不为2")
    linear_fit_para=[]
    for i_cell in range(1024):
        k = (y[1] - y[0])/(x[i_cell][1] - x[i_cell][0])
        b = y[1] - k * x[i_cell][1]
        linear_fit_para.append((k,b))#二维数组：每个cell*（斜率， 截距）
    #print(np.array(self.all_cells_linear_fit_para)[:5])
    return linear_fit_para
#用拟合结果进行线性校正
def linear_correct(data_to_linearcorrect:list, linear_fit_list:list):
    data_linearcorrected = []
    for i in range(len(data_to_linearcorrect)):
        data_linearcorrected.append(linear_fit_list[i][0]*data_to_linearcorrect[i] + linear_fit_list[i][1])
    return data_linearcorrected
#毛刺消除
def fitted_debur(fitted_data:list,wasted_num=16,signal_width=10,signal_direction=-1,bur_direction=-1):
    data1=np.array(fitted_data)[wasted_num:-wasted_num]
    data1_indices=np.argsort(data1)
    data2=data1[data1_indices]
    if signal_direction<0:
        data3=data2[signal_width:-signal_width*31]
    else:
        data3=data2[signal_width*31:-signal_width]
    len3=len(data3)
    if bur_direction<0:
        mean_baseline=np.mean(data3[len3//32:])
        mean_bur=np.mean(data3[:len3//32])
        mean_bur_relative=mean_bur-mean_baseline
        if signal_direction<0:
            firstburposi=(data1_indices[signal_width+len3//32//2]+wasted_num)%32#首个毛刺位置
        else:
            firstburposi=(data1_indices[signal_width*31+len3//32//2]+wasted_num)%32#首个毛刺位置
    else:
        mean_baseline=np.mean(data3[:-len3//32])
        mean_bur=np.mean(data3[-len3//32:])
        mean_bur_relative=mean_bur-mean_baseline
        if signal_direction<0:
            firstburposi=(data1_indices[signal_width+len3-1]+wasted_num)%32#首个毛刺位置
        else:
            firstburposi=(data1_indices[signal_width*31+len3-1]+wasted_num)%32#首个毛刺位置
    for posi in range(firstburposi,1024,32):
        fitted_data[posi]-=mean_bur_relative
    return fitted_data
#时序转空间序
def timeorder_to_cellorder(onegroup_timeorder_data, posi:int):
    onegroup_cellorder_data = np.concatenate([
                onegroup_timeorder_data[1023-posi:],
                onegroup_timeorder_data[:1023-posi]])
    return onegroup_cellorder_data
#空间序转时序
def cellorder_to_timeorder(onegroup_cellorder_data, posi:int):
    onegroup_timeorder_data = np.concatenate([
                onegroup_cellorder_data[posi+1:],
                onegroup_cellorder_data[:posi+1]])
    return onegroup_timeorder_data
#滤波窗函数
numtaps=45
cutoff=14*10**7
FIR_filter = firwin(numtaps=numtaps, 
                        cutoff=cutoff, 
                        pass_zero=True, 
                        fs = 10**9)
#滤波函数
#from scipy import signal
#signal.lfilter(FIR_filter, 1.0, onegroup_timeorder_data_linearcorrected)


