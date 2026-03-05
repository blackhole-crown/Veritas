# 修改checkpoint路径
import argparse
parser = argparse.ArgumentParser(description='manual to this script')
parser.add_argument("--ckpt_dir", type=str)
args = parser.parse_args()
ckpt_dir = args.ckpt_dir

import os
import sys
import json
# os.environ['CUDA_VISIBLE_DEVICES'] = '0'

dirs = [".."]
for _dir in dirs:
    if _dir not in sys.path:
        sys.path.append(_dir)

from swift.llm import (
    get_model_tokenizer, get_template, inference
)
from swift.tuners import Swift
from custom import CustomModelType, CustomTemplateType
import evaluation

with open(f"{ckpt_dir}/sft_args.json", "r") as f:
    sft_args = json.load(f)

def get_model_template():
    model_type, template_type = sft_args["model_type"], sft_args["template_type"]
    model, tokenizer = get_model_tokenizer(
        model_type, model_kwargs={'device_map': 'auto'},
        model_dir=sft_args["model_cache_dir"]
    )
    model = Swift.from_pretrained(model, ckpt_dir, inference_mode=True)
    if sft_args["sft_type"] == 'adalora':
        model = model.to(model.dtype)
    model.generation_config.max_new_tokens = 512
    model.generation_config.do_sample = False

    template = get_template(template_type, tokenizer)

    return model, template

evaluation.cal_metric_single_llm(get_model_template, inference, sft_args, save=True, use_tqdm=True)
