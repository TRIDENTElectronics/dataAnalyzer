import math
import sys
import os
import numpy as np
#import pandas as pd
import threading
from threading import Thread
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from scipy import signal
#
from recvfrom_rawfiles import recvfrom_rawdatafiles as rr
import functions as fc


Nmin = 7#两个过零点之间的最小点数
n_wasted_whenfilter=10
n_wasted_afterfilter=50
class Unlinear_fit(Thread):
    def __init__(self, frequency, dc=0xFFFF):#输入MHz,直流成分mV,输出ns
        Thread.__init__(self)
        self.frequency=frequency
        self.dc=dc

    def run(self):
        rr1=rr()
        rr1.run()
        rr1.conclude()

        print("选择直流标定参数文件")
        file_path = fc.select_file("npy")
        rr1.linearpara_load(file_path)

        allchns_cells_difftime=[]
        print("正在交流标定")
        ps1=fc.process(31)
        for n_chn in range(31):
            raw_groups, stop_posi=rr1.drs_onechn(n_chn)
            matrix_K=[]
            for n_group in range(len(raw_groups)):
                one_group=fc.linear_correct(raw_groups[n_group],fc.cellorder_to_timeorder(rr1.linear_para[n_chn],stop_posi[n_group]))
                filtered_group = np.array(signal.lfilter(fc.FIR_filter, 1.0, np.array(one_group)[n_wasted_whenfilter:]))[n_wasted_afterfilter:]
                #print(f"filtered_group{len(filtered_group)}")
                not0_pointN = Nmin
                if self.dc==0xFFFF:
                    ave=sum(filtered_group) / len(filtered_group)
                else:
                    ave=self.dc      
                #print(f"ave:{ave}")       # 
                #if n_group==100:
                    #fc.Graph_group_data(filtered_group)      
                #//////////////////////////////////////////////////////////////////////////////////////////
                point2ram=[[0,0,-1],[0,0,-1]]#(x1,k1,0/1/2(坏/？/好点))
                for i_timepoint in range(20,900):#///////////////////////////////可变
                    y1 = filtered_group[i_timepoint]-ave
                    y2 = filtered_group[i_timepoint+1]-ave
                    delta = y2 - y1
                    x=(i_timepoint+n_wasted_whenfilter+n_wasted_afterfilter+stop_posi[n_group]+1)%1024
                    k=abs(y1/delta)
                    if(y1 * y2 < 0 or y1 == 0):
                        point2ram[0]=point2ram[1]
                        if(not0_pointN<Nmin):
                            point2ram[1]=[x,k,0]
                        else:
                            point2ram[1]=[x,k,1]
                        not0_pointN = 0
                    else:
                        not0_pointN +=1
                        if not0_pointN==Nmin:
                            point2ram[1][2]+=1
                            if point2ram[0][2]==2 and point2ram[1][2]==2:
                                x1=point2ram[0][0]
                                x2=point2ram[1][0]
                                k1=point2ram[0][1]
                                k2=point2ram[1][1]
                                onerow = [0]*1024
                                onerow[x1] = 1 - k1
                                onerow[x2] = k2
                                if(x1 < x2):
                                    for i_x in range(x1+1, x2):
                                        onerow[i_x] = 1
                                else:
                                    if(x1<1023):
                                        for i_x in range(x1+1,1024):
                                            onerow[i_x] = 1
                                    if(x2>0):
                                        for i_x in range(0,x2):
                                            onerow[i_x] = 1
                                matrix_K.append(onerow)
            #//////////////////////////////////////////////////////////////////////////////////////////
            matrix_Kn = np.array(matrix_K)
            print(matrix_Kn.shape)

            if matrix_Kn.ndim!=1:
                matrix_B = np.array([1000./2/self.frequency] * len(matrix_Kn)).reshape(-1,1)#半周期，这样最后结果单位为ns
                xT = np.linalg.lstsq(matrix_Kn, matrix_B, rcond=None)[0]
                cell_difftime = xT.flatten()
                #print(np.array(cell_difftime)[:10])
                allchns_cells_difftime.append(cell_difftime)
            else:
                print(f"chn{n_chn} has no effective points.")#
                allchns_cells_difftime.append([1]*1024)
                
            ps1.rest=30-n_chn
            ps1.layout()
        allchns_cells_difftime.append([1]*1024)
        fc.Data_save_csv(allchns_cells_difftime, new_name="unlinear_fit_para.csv")

if __name__=='__main__':
    ulf1 = Unlinear_fit(24.576)
    ulf1.run()
