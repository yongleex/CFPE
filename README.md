# Cross-frequency Phase Extraction (CFPE) 


[![preprint](https://img.shields.io/static/v1?label=Journal&message=Submitted_OLEN&color=B31B1B)](https://www.journals.elsevier.com/optics-and-lasers-in-engineering)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


This repository contains code for the submitted paper *[A fast cross-frequency phase extraction for phase shifting profilometry](https://doi.org/)*. 
In this work, we formulate the phase extraction problem with high-order harmonic as a maximum likelihood estimation (MLE), and our CFPE is an efficient optimization method by introducing a latent phase map and incorporating the expectation-maximization (EM) framework.
Compared to the only high-order baseline (LLS), our CFPE method only needs **~5 percent execution time ** to achieve high-order accuracy.
### Motivation 
![movie](https://github.com/yongleex/CFPE/blob/main/data/Fig2.png)

As a special curve fitting problem, our CFPE utilizes more data points (cross-frequency images) to solve a high-order harmonic model. That says, $\theta^* =\arg\min \Sigma_i\Sigma_j (I_{i,j}-h_{i,j})^2 $. 

Our CFPE reports an efficient iterative solution to this problem $\phi_1^{new}=update(\phi_1^{old})$. More info is referred to the paper.


## Install dependencies
```
conda install numpy matplotlib opencv seaborn
conda install -c anaconda pathlib
```


## The experiments
* [Exp1.ipynb](https://github.com/yongleex/CFPE/blob/main/Exp1_synthesis.ipynb): Test on several synthetic PSP images;
* [Exp2.ipynb](https://github.com/yongleex/CFPE/blob/main/Exp2_real.ipynb): Test on 4 real PSP cases;


### BibTeX

```
@article{lee2022cfpe,
  author={Lee, Yong and Mao, Ya and Chen, Zuobing},  
  journal={Submitted to Optics and Lasers in Engineering},  
  title={A fast cross-frequency phase extraction for phase shifting profilometry},  
  year={2022},
  volume={},
  number={},
  pages={1-1},
  doi={}}
```

### Questions?
For any questions regarding this work, please email me at [yongli.cv@gmail.com](mailto:yongli.cv@gmail.com), [yonglee@whut.edu.cn](mailto:yonglee@whut.edu.cn).

#### Acknowledgements
These works are contributed to our CFPE project,

* [LLS](https://doi.org/10.1364/OE.384155)
* [Industrial Camera from hikrobotics](https://www.hikrobotics.com/cn/machinevision/visionproduct?typeId=27&id=259)
* [XGIMI Home projector](https://www.xgimi.com/)
