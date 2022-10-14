# Ensembling of Large Sequence Taggers for Text Correction

## 环境配置

1. 安装pytorch

   ```
   conda create -n gector_env python=3.7.6 -y
   conda activate gector_env
   conda install pytorch=1.10.1 cudatoolkit -c pytorch
   ```

2. 安装NVIDIA-Apex

   ```bash
   git clone https://github.com/NVIDIA/apex
   cd apex
   pip install -v --disable-pip-version-check --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" ./
   ```

3. 安装其他依赖

   ```bash
   cd gector-large
   pip install -r requirements.txt
   python -m spacy download zh_core_web_sm
   ```

## 复现步骤

### 数据预处理

1. 将训练集、验证集字符按空格分开，每句一行。

   其中，官方提供的训练集文件lang8.train.ccl22.para的所在路径，yaclc_dev.para是验证集的.para文件所在位置(CCL2022-CLTC-main/datasets/track3/dev/yaclc_dev.para)，src_path和tgt_path都是处理后文件存放的位置，默认和.para文件在同一文件夹下

   ```bash
   python utils/preprocess_para -s src_path -t tgt_path -f lang8.train.ccl22.para
   python utils/preprocess_dev_para -s src_path -t tgt_path -f yaclc_dev.para
   ```

2. 生成编辑序列

   其中，src_path、tgt_path是上一步预处理后的文件位置，output_edit_file是生成的编辑序列路径，放在CCL2022-CLTC-main/baselines/track3/下

   ```bash
   cd CCL2022-CLTC-main/baselines/track3/seq2edit
   python utils/preprocess_data.py -s src_path -t tgt_path -o output_edit_file
   ```

### 模型训练

- 下载huggingface大规模预训练模型到文件夹[CCL2022-CLTC-main](https://github.com/Anddyyyyy/CCL2022_TRACK3/tree/add-license-1/CCL2022-CLTC/CCL2022-CLTC-main)/[baselines](https://github.com/Anddyyyyy/CCL2022_TRACK3/tree/add-license-1/CCL2022-CLTC/CCL2022-CLTC-main/baselines)/[track3](https://github.com/Anddyyyyy/CCL2022_TRACK3/tree/add-license-1/CCL2022-CLTC/CCL2022-CLTC-main/baselines/track3)/pretrain_model下，下面是

  [chinese-roberta-wwm-ext](https://huggingface.co/hfl/chinese-roberta-wwm-ext)的下载链接(以这个为例)

- 编辑deepspeed_config.json. 需要注意的是，lr和batch_size会被args参数覆盖。然后编辑train.sh，并运行

  ```bash
  cd CCL2022-CLTC-main/baselines/track3/seq2edit
  bash train.sh
  ```

### 模型预测

- 编辑deepspeed_config.json，然后编辑predict.sh，并运行

  ```bash
  cd CCL2022-CLTC-main/baselines/track3/seq2edit
  bash predict.sh
  ```

### 模型集成

- 用初始目录utils文件夹中的preprocess_test_para.py，将test.src文件和test.preds文件合并成集成需要用的.para文件格式

  ```bash
  python utils/preprocess_test_para.py -s test.src -t test.preds -f test.para
  ```

  

- ```bash
  cd gector-large/ensemble_result
  ```

​		运行process_ensemble.ipynb，完成模型集成
