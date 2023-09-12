# 使用量子组合优化算法求解Min-Cut问题

## 背景
经过了数万年的漫长漂泊，地球终于来到了4.22光年外的半人马座，为了让人类和平地生存下去，联合国决定将适合生存的行星们均等地分配给C国与A国，然而由于不同行星上的资源不同，需要使用飞船往返特定行星传送资源。在A国C国内部行星间的飞船传送自费，而行星间的传输由联合国出资。假设你作为联合国财政部顾问，为了节省联合国经费，需要考虑如何分配这些行星，使得C国行星们与A国行星们之间的传送最少。

如果使用图的观点，将不同的行星看做图中节点，而有边连接的特定行星间需要进行资源传输。你需要让图分成均等的两部分，同时让两部分之间的连线最少。

## 平衡最小割问题

![](graphs/min-cut.png) 

平衡最小割问题不仅需要让两部分间连线最少，同时要保持两部分节点数量相同，因此这里使用了惩罚项，当优化Cost最小的过程中，会使得Zi的求和为0，也就是两部分的节点数量相等。

$Cost= -\sum_{<i,j>\in edges} (1 - Z_i Z_j)/2\   + penalty\times(\sum_{i}Z_i)^2$

同样考虑用一台15比特的量子设备求解Min-cut问题，要求设计合适的方案，对分解后的子问题限制使用QAOA算法进行求解，同时量子线路的比特数限制在15比特及以内。（使用模拟器求解，不考虑量子设备硬件拓扑）

## 实现

请任意设计修改solve_min_cut.py中的solve函数以实现求解。请确保使用硬件规模N_sub不大于15，同时utils中的工具函数无需修改。


## 分数
- 评分规则为:

$Mean[\sum_{G} (1 - \frac{cut+4*unb}{\#edges})\times N]$

- 其中unb是不平衡系数，是两组实际分配数量差值的一半，#edges是图的边数。
- 相同分数按照运行时间排名。

### 数据集
12张图，存在graph文件夹中txt文件里，每张图的存储方式如下：

节点数n  边数m

第一条边所连接的第一个顶点   所连接的第二个顶点

第二条边所连接的第一个顶点   所连接的第二个顶点

......


## 样例代码
无论是最大割或者最小割问题，优化目标函数均为QUBO（Quadratic unconstrained binary optimization）形式，即求解QUBO问题。在样例代码中，我们会循环调用QAOA求解器求解subQUBO问题，具体步骤如下：
1. 首先，随机初始化解。
2. 按照变量对目标函数的影响大小进行排序，将影响最大的15个变量抽取出来而其他的变量维持固定。
3. 对这15个变量形成的子问题（subQUBO问题）利用QAOA求解器高效求解。
4. 回到第2步反复迭代直至收敛。


## 判题程序
请按照指定的数据格式进行输出，判题系统会使用同样的判题程序score.py


## 要求
1. 仅允许在分解选取子问题过程中使用经典算法，不可使用经典算法进行subQUBO问题的求解。
2. 子问题仅可使用QAOA求解。
3. 程序总运行时间在30min内。（需调用qupack中的QAOA模拟器进行子问题求解）
4. 所使用库可通过pip或者conda安装，不使用收费库。
5. 每个参与者或每组不可重复提交。