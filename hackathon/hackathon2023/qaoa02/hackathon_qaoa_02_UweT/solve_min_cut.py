import os
os.environ['OMP_NUM_THREADS'] = '2'
from itertools import count
import numpy as np
import time
import copy
import sys
import random
import matplotlib.pyplot as plt
import pickle
import numpy as np
from utils import *


'''
本赛题旨在引领选手探索，在NISQ时代规模有限的量子计算机上，求解真实场景中的大规模图分割问题。
min-cut: 使得ZiZj项的和最大，而不是最大割里使其最小化
Hamiltonian: 最小化
    -Sum_{ij in g.edges} ZiZj + penalty * (Sum Zi)^2
    ~ -Sum_{ij in g.edges} ZiZj + penalty * (Sum_{i,j in N} ZiZj)
'''

import resource
soft, hard = resource.getrlimit(resource.RLIMIT_AS)
resource.setrlimit(resource.RLIMIT_AS, (1024*1024*4000, hard)) #4G
N_sub=15 # 量子比特的规模限制

filelist=['./graphs/regular_d3_n40_cut54_0.txt', './graphs/regular_d3_n80_cut108_0.txt',
          './graphs/weight_p0.2_cut406.txt', './graphs/partition_n80_cut257_2.txt',
          './graphs/partition_n80_cut226_0.txt', './graphs/partition_n80_cut231_1.txt'
          ]


def build_sub_qubo(solution,N_sub,J,h=None,C=0.0):
    '''
    自定义函数选取subqubo子问题。
    例如可简单选择对cost影响最大的前N_sub个变量组合成为subqubo子问题。
    【注】本函数非必须，仅供参考
    
    返回
    subqubo问题变量的指标，和对应的J，h，C。
    '''
    delta_L=[]
    for j in range(len(solution)):
        copy_x=copy.deepcopy(solution)
        #copy_x[j]=-copy_x[j]
        if copy_x[j] == 1:
            copy_x[j] = 0
        else:
            copy_x[j] = 1
        x_flip=copy_x
        sol_qubo=calc_qubo_x(J,solution,h=h,C=C)
        x_flip_qubo=calc_qubo_x(J,x_flip,h=h,C=C)
        delta=x_flip_qubo-sol_qubo
        delta_L.append(delta)
    delta_L=np.array(delta_L)
    
    sub_index = np.argpartition(delta_L, -N_sub)[-N_sub:] # subqubo子问题的变量们
    #print(delta_L)
    #print(sub_index)
    J_sub,h_sub,C_sub = calc_subqubo(sub_index, solution, J, h=h,C=C )
    return sub_index,J_sub,h_sub,C_sub

def solve(sol,G_mincut, G):
    '''
    自定义求解函数。
    例如可简单通过不断抽取20个变量组成subqubo问题并对子问题进行求解，最终收敛到一个固定值。
    或者可采取其他方法...
    
    【注】可任意改变求解过程，但不可使用经典算法如模拟退火，禁忌搜索等提升解质量。请保持输入输出一致。
    
    输入：
    sol （numpy.array）：初始随机0/1比特串，从左到右分别对应从第1到第N个问题变量。
    G （matrix): QUBO问题矩阵
    
    输出：
    sol （numpy.array）：求解结果的0/1比特串
    cut_temp （float）：最终结果的cut值
    '''
    i=0
    cut_temp = 9999
    while(i<12):
#        print(f'---{i}---')
        sub_index,J_sub,h_sub,C_sub=build_sub_qubo(sol,N_sub,G_mincut,h=None,C=0)
        qubo_t=calc_qubo_x(G_mincut, sol)
        plus_num=np.sum(sol==1)
        minus_num=np.sum(sol==0)
        unbalance=abs(plus_num-minus_num)/2
        #print('before subqubo:',qubo_t,sol,'unb:',unbalance)
        sol=solve_QAOA(J_sub,h_sub,C_sub,sub_index,sol,depth=4,tol=1e-6)
        qubo_temp=calc_qubo_x(G_mincut, sol)
        #cut_temp =calc_cut_x(G, sol)
        cut_temp =min(calc_cut_x(G, sol),cut_temp)
#        print('after subqubo:',qubo_temp,'|cut:',cut_temp)
        plus_num=np.sum(sol==1)
        minus_num=np.sum(sol==0)
        unbalance=abs(plus_num-minus_num)/2
        #print('solution:',sol)
        #print('unbalance:', unbalance)
        i+=1
    return sol, cut_temp, unbalance


def build_mincut_G(G, penalty=1.):
    '''
    Hamiltonian (minimize)
    ~ -Sum_{ij in g.edges} ZiZj + penalty * (Sum Zi)^2
    ~ -Sum_{ij in g.edges} ZiZj + penalty * (Sum_{i,j in N} ZiZj)
    '''
    n,_=G.shape
    G_mincut=G.copy()
    for i in range(n):
        for j in range(n):
            if j>i:
                G_mincut[i,j]+=penalty/2
                G_mincut[j,i]+=penalty/2
    #print(G_mincut[0,:])
    return -G_mincut

def run():
    """
    Main run function, for each graph need to run for 20 times to get the mean result.
    Please do not change this function, we use this function to score your algorithm. 
    """           
    cut_list=[]
    unb_list=[]
    for filename in filelist[:]:
        print(f'--------- File: {filename}--------')
        g,G=read_graph(filename)
        G_mincut= build_mincut_G(G, penalty=0.3) # 得到整体的Ising问题的矩阵，penlaty是哈密顿量中惩罚项前的系数
        n=len(g.nodes) # 图整体规模
        cuts=[]
        unbs=[]
        for turn in range(20):
            #print(f'------turn {turn}------')
            sol=init_solution(n) # 随机初始化解 
            qubo_start = calc_qubo_x(G_mincut, sol)
            cut_start =calc_cut_x(G, sol)  
            #print('qubo start:',qubo_start,'cut start:',cut_start)
            solution, cut, unbalance = solve(sol, G_mincut,G) 
            cuts.append(cut)
            unbs.append(unbalance)
        cut_list.append(cuts)
        unb_list.append(unbs)
    return np.array(cut_list), np.array(unb_list) 
        
        

if __name__== "__main__":   
    #计算分数
    cut_list, unb_list=run()
    print(cut_list,unb_list)
    edge_arr=np.array([60,120,604,370,324,331])
    size_arr=np.array([40,80,80,80,80,80])
    score=(1-(np.mean(cut_list,axis=1)+4*np.mean(unb_list,axis=1))/edge_arr)*size_arr
    print('score:',np.sum(score))
 