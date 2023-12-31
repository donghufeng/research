# 激发态能求解的浅层线路设计

Variational Quantum Eigensolver (VQE) 算法是一种用于计算分子基态能量的量子化学模拟方法，它可以结合经典计算机，利用当前含噪的量子计算机解决一些化学问题。而在基态能量求解方法的基础上，又衍生出了用VQE计算激发态的一些方案，如正交约束VQE [1]、子空间VQE [2] 等。现有常用的线路设计和优化方法通常难以平衡计算效率和计算精度的问题，本赛题旨在让参赛者通过设计线路或改良优化方法，用最短的时间优化得到对应分子的符合化学精度的激发态能量。

## 赛题要求：

（1）对于不同的测试分子案例，选择基矢为sto-3g。根据给出的分子体系设计量子线路并尝试进行各种优化，使计算的第一激发态能量尽可能达到化学精度(0.0016Ha)。
（2）程序要求基于 MindSpore Quantum 或 Qupack。

## 测试数据：
分子：H2O，比特数：14，键长点：1.0


## 评分标准：

（1）与FCI方法计算结果进行比较，各个分子的计算结果均需达到化学精度；在所有分子达到化学精度的前提下，成绩以总运行时间为准，程序运行时间越短，成绩越好。

（2）若实在无法达到化学精度，则越接近FCI结果，成绩越好；成绩记为 50000 + abs(计算结果 - FCI能量)。

（3）判题系统验证时间超过3小时则判为100000。

## 提交说明：

- 将所有代码归档到`src`文件夹内。
- 开发的程序可以基于`main.py`文件，或自行定义并将其类名命名为`Main`，放置于`main.py`文件内。最终结果需要经过`eval.py`的测试。
- 作品打成压缩包`hackathon_vqe_02_姓名_联系电话.zip`提交。
- 文件请按照项目结构要求保存所有项目源代码。
- 举办方会替换并调用`eval.py`文件来对开发的模型进行验证，请参考`eval.py`代码保证开发的模型能够被顺利验证。

## 项目结构

```bash
.   				<--根目录，提交时将整个项目打包成`hackathon_vqe_02_姓名_联系电话.zip`
├── eval.py			<--举办方用来测试选手的模型的脚本,可以作为个人测试使用
├── README.md		<--说明文档
├── help		    <--帮助文件夹，里面提供了一些实用的python程序
├── molecule_files	<--存储了赛题要求的分子文件
├── src				<--源代码目录，选手的所有开发源代码都应该放入该文件夹内
│   └── main.py		<--`eval.py`调用程序。该文件为参考代码，无有意义结果

```

## 相关文献

[1] Higgott, O., Wang, D., & Brierley, S. (2019). Variational quantum computation of excited states. Quantum, 3, 156.

[2] Nakanishi, K. M., Mitarai, K., & Fujii, K. (2019). Subspace-search variational quantum eigensolver for excited states. Physical Review Research, 1(3), 033062.

## 参考资料

https://gitee.com/mindspore/mindquantum/tree/research/ansatz_zoo