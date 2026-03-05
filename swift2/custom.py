# Copyright (c) Alibaba, Inc. and its affiliates.
from typing import Any, Dict, Optional, Tuple
import torch
from datasets import Dataset as HfDataset
from modelscope import AutoConfig, AutoModelForCausalLM, AutoTokenizer, MsDataset
from torch import dtype as Dtype
from transformers.utils.versions import require_version
from types import MethodType

from swift.llm import (LoRATM, Template, TemplateType, dataset_map, get_dataset, get_dataset_from_repo,
                       # get_model_tokenizer, 
                       get_template, print_example, register_dataset, register_model,
                       register_template)
from swift.utils import get_logger

logger = get_logger()

_default_phi3_system = ('You are a helpful digital assistant. '
                        'Please provide safe, ethical and accurate information to the user.')

class CustomModelType:
    tigerbot_7b = 'tigerbot-7b'
    tigerbot_13b = 'tigerbot-13b'
    tigerbot_13b_chat = 'tigerbot-13b-chat'

    orca2_7b = "orca-2-13b"
    openchat_35 = "openchat_3.5"
    fusechat_7b = "fusechat-7b-varm"
    mistral_7b_instruct_v3 = "mistral-7b-instruct-v0.3"
    neural_chat_7b = "neural-chat-7b-v3"
    solar_instruct_10_7b = "solar-10.7b-instruct"
    mixtral_moe_7b_instruct_gptq_int4 = "mixtral-8x7B-instruct-v0.1-gptq-int4"
    mixtral_moe_7b_instruct_awq = "mixtral-8x7B-instruct-v0.1-awq"
    gemma_2_9b_it = 'gemma-2-9b-it'
    merlinite_7b = 'merlinite-7b'
    c4ai_command_r_4bit = "c4ai-command-r-v01-4bit"
    llama_3_8b_instruct = "meta-llama-3-8B-instruct"
    llama_3_70b_instruct_gptq_int4 = "meta-llama3-70B-instruct-gptq-int4"
    llama_3_70b_instruct_awq = "meta-llama-3-70b-instruct-awq"

    phi_3_mini_4k_instruct = "phi-3-mini-4k-instruct"
    phi_3_small_8k_instruct = "phi-3-small-8k-instruct"
    phi_3_medium_4k_instruct = "phi-3-medium-4k-instruct"

class CustomTemplateType:
    tigerbot = 'tigerbot'

    orca2 = "orca-2"
    openchat_35 = "openchat_3.5"
    neural = "neural"
    solar = "solar"
    # mistral = "mistral"
    chatml = "_chatml" # 无system message的chatml
    llama = "_llama" # 无system message的llama
    merlinite = "merlinite"
    c4ai_command_r = "c4ai_command_r" # 用于RAG的Template
    llama3 = "_llama3"
    gemma = '_gemma'
    phi3 = '_phi3'


class CustomDatasetName:
    stsb_en = 'stsb-en'


@register_model(CustomModelType.tigerbot_7b, 'TigerResearch/tigerbot-7b-base-v3', LoRATM.llama2,
                TemplateType.default_generation)
@register_model(CustomModelType.tigerbot_13b, 'TigerResearch/tigerbot-13b-base-v2', LoRATM.llama2,
                TemplateType.default_generation)
@register_model(CustomModelType.tigerbot_13b_chat, 'TigerResearch/tigerbot-13b-chat-v4', LoRATM.llama2,
                CustomTemplateType.tigerbot)
def get_tigerbot_model_tokenizer(model_dir: str,
                                 torch_dtype: Dtype,
                                 model_kwargs: Dict[str, Any],
                                 load_model: bool = True,
                                 **kwargs):
    use_flash_attn = kwargs.pop('use_flash_attn', False)
    if use_flash_attn:
        require_version('transformers>=4.34')
        logger.info('Setting use_flash_attention_2: True')
        model_kwargs['use_flash_attention_2'] = True
    model_config = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
    model_config.pretraining_tp = 1
    model_config.torch_dtype = torch_dtype
    logger.info(f'model_config: {model_config}')
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    model = None
    if load_model:
        model = AutoModelForCausalLM.from_pretrained(
            model_dir, config=model_config, torch_dtype=torch_dtype, trust_remote_code=True, **model_kwargs)
    return model, tokenizer


@register_model(CustomModelType.orca2_7b,
                '/home/css/models/Orca-2-13b', LoRATM.llama2,
                CustomTemplateType.orca2)
def get_orca2_model_tokenizer(model_dir: str,
                                 torch_dtype: Dtype,
                                 model_kwargs: Dict[str, Any],
                                 load_model: bool = True,
                                 **kwargs):
    model_config = AutoConfig.from_pretrained(model_dir)
    # model_config.pretraining_tp = 1
    model_config.torch_dtype = torch_dtype
    logger.info(f'model_config: {model_config}')
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    model = None
    if load_model:
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            config=model_config,
            torch_dtype=torch_dtype,
            **model_kwargs)
    return model, tokenizer

@register_model(CustomModelType.openchat_35,
                '/home/css/models/openchat-3.5-0106', LoRATM.llama2,
                CustomTemplateType.openchat_35)
@register_model(CustomModelType.fusechat_7b,
                '/home/css/models/FuseChat-7B-VaRM', LoRATM.llama2,
                CustomTemplateType.openchat_35)
@register_model(CustomModelType.mistral_7b_instruct_v3,
                '/home/css/models/Mistral-7B-Instruct-v0.3', LoRATM.llama2,
                CustomTemplateType.llama)
@register_model(CustomModelType.neural_chat_7b,
                '/home/css/models/neural-chat-7b-v3-3', LoRATM.llama2,
                CustomTemplateType.neural)
@register_model(CustomModelType.solar_instruct_10_7b,
                '/home/css/models/SOLAR-10.7B-Instruct-v1.0', LoRATM.llama2,
                CustomTemplateType.solar)
@register_model(CustomModelType.mixtral_moe_7b_instruct_gptq_int4,
                '/home/css/models/Mixtral-8x7B-Instruct-v0.1-GPTQ-int4', LoRATM.llama2,
                CustomTemplateType.llama,
                torch_dtype=torch.float16,
                function_kwargs={'gptq_bits': 4})
@register_model(CustomModelType.mixtral_moe_7b_instruct_awq,
                '/home/css/models/Mixtral-8x7B-Instruct-v0.1-AWQ', LoRATM.llama2,
                CustomTemplateType.llama,
                requires=['autoawq'],
                torch_dtype=torch.float16,
                function_kwargs={'is_awq': True})
@register_model(CustomModelType.gemma_2_9b_it,
                '/home/css/models/gemma-2-9b-it', LoRATM.llama2,
                CustomTemplateType.gemma)
@register_model(CustomModelType.merlinite_7b,
                '/home/css/models/merlinite-7b', LoRATM.llama2,
                CustomTemplateType.merlinite)
@register_model(
    CustomModelType.phi_3_mini_4k_instruct,
    '/home/css/models/Phi-3-mini-4k-instruct',
    LoRATM.phi3,
    CustomTemplateType.phi3,
    requires=['transformers>=4.36'],
    support_flash_attn=True,
    support_vllm=False,
    tags=['general'])
@register_model(
    CustomModelType.phi_3_medium_4k_instruct,
    '/home/css/models/Phi-3-medium-4k-instruct',
    LoRATM.phi3,
    CustomTemplateType.phi3,
    requires=['transformers>=4.36'],
    support_flash_attn=True,
    support_vllm=True,
    tags=['general'])
def get_model_tokenizer(
    model_dir: str,
    torch_dtype: Dtype, 
    model_kwargs: Dict[str, Any], 
    load_model: bool = True,
    model_config=None,
    **kwargs
):
    is_awq = kwargs.pop('is_awq', False)
    is_aqlm = kwargs.pop('is_aqlm', False)
    gptq_bits = kwargs.pop('gptq_bits', 0)

    if model_config is None:
        model_config = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
    model_config.torch_dtype = torch_dtype
    use_flash_attn = kwargs.pop('use_flash_attn', False)
    if use_flash_attn:
        model_config._attn_implementation = 'flash_attention_2'
    
    if "gemma-2" in model_dir:
        model_config._attn_implementation = 'eager'
    logger.info(f'model_config: {model_config}')
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    model = None
    if load_model:
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            config=model_config,
            torch_dtype=torch_dtype,
            trust_remote_code=True,
            **model_kwargs)
        if load_model and is_awq:
            model.is_awq = is_awq
        if load_model and gptq_bits > 0:
            model.gptq_bits = gptq_bits
    return model, tokenizer

@register_model(CustomModelType.llama_3_8b_instruct,
                '/home/css/models/Meta-Llama-3-8B-Instruct', LoRATM.llama2,
                CustomTemplateType.llama3)
@register_model(CustomModelType.llama_3_70b_instruct_gptq_int4,
                '/home/css/models/Meta-Llama-3-70B-Instruct-GPTQ-Int4', LoRATM.llama2,
                CustomTemplateType.llama3,
                function_kwargs={'gptq_bits': 4})
@register_model(CustomModelType.llama_3_70b_instruct_awq,
                '/home/css/models/llama-3-70b-instruct-awq', LoRATM.llama2,
                CustomTemplateType.llama3,
                requires=['autoawq'],
                # torch_dtype=torch.float16,
                function_kwargs={'is_awq': True})
def get_model_tokenizer_llama(
    model_dir: str,
    torch_dtype: Dtype,
    model_kwargs: Dict[str, Any],
    load_model: bool = True,
    **kwargs
):
    model_config = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
    model_config.pretraining_tp = 1
    return get_model_tokenizer(
        model_dir, torch_dtype, model_kwargs, load_model, model_config=model_config, **kwargs)

@register_model(
    CustomModelType.phi_3_small_8k_instruct,
    '/home/css/models/Phi-3-small-8k-instruct',
    LoRATM.phi3_small,
    CustomTemplateType.phi3,
    requires=['transformers>=4.36'],
    support_flash_attn=True,
    support_vllm=True,
    support_gradient_checkpointing=False,
    tags=['general'])
def get_model_tokenizer_phi_3_small(model_dir: str,
                                   torch_dtype: Dtype,
                                   model_kwargs: Dict[str, Any],
                                   load_model: bool = True,
                                   model_config=None,
                                   **kwargs):
 
    model, tokenizer = get_model_tokenizer(
        model_dir, torch_dtype, model_kwargs, load_model, model_config=model_config, **kwargs)

    def rotary_emb(self, query_states, key_states, **kwargs):
        q_type = query_states.dtype
        k_type = key_states.dtype
        query_states, key_states = self.rotory_emb_origin(query_states, key_states, **kwargs)
        query_states = query_states.to(q_type)
        key_states = key_states.to(k_type)
        return query_states, key_states

    for i in range(32):
        re = model.model.layers[i].self_attn.rotary_emb
        re.rotory_emb_origin = re.forward
        re.forward = MethodType(rotary_emb, re)
    return model, tokenizer

# Ref: https://github.com/TigerResearch/TigerBot/blob/main/infer.py
register_template(
    CustomTemplateType.tigerbot,
    Template(['{{SYSTEM}}'], ['\n\n### Instruction:\n{{QUERY}}\n\n### Response:\n'], [], [['eos_token_id']]))

register_template(
    CustomTemplateType.openchat_35,
    Template(
        [],
        ['GPT4 Correct User: {{QUERY}}<|end_of_turn|>GPT4 Correct Assistant:'],
        ['<|end_of_turn|>'], ['<|end_of_turn|>'], None, ['{{SYSTEM}}<|end_of_turn|>']))

# 不支持多轮对话
register_template(
    CustomTemplateType.orca2,
    Template(
        [], ['<|im_start|>user\n{{QUERY}}<|im_end|>\n<|im_start|>assistant\n'],
        ['<|im_end|>\n'], ['<|im_end|>'], None,
        ['<|im_start|>system\n{{SYSTEM}}<|im_end|>\n']))

register_template(
    CustomTemplateType.neural,
    Template( 
        [],
        ['### User:\n{{QUERY}}\n### Assistant:\n'],
        ['\n'], ['</s>'], None, ['### System:\n{{SYSTEM}}\n']))

register_template(
    CustomTemplateType.solar,
    Template(
        [],
        ['### User:\n{{QUERY}}\n\n### Assistant:\n'],
        ['\n\n'], ['</s>'], None, ['### System:\n{{SYSTEM}}\n\n']))

# register_template(
#     CustomTemplateType.mistral,
#     Template(
#         ['<s>[INST] '], ['{{QUERY}} [/INST]'], ['</s><s>[INST] '], 
#         ['</s>'], None,
#         ['<s>[INST] {{SYSTEM}}\n']))

register_template(
    CustomTemplateType.chatml,
    Template(
        [], ['<|im_start|>user\n{{QUERY}}<|im_end|>\n<|im_start|>assistant\n'],
        ['<|im_end|>\n'], ['<|im_end|>'], None,
        ['<|im_start|>system\n{{SYSTEM}}<|im_end|>\n']))

# default system: "You are an AI language model developed by IBM Research. You are a cautious assistant. You carefully follow instructions. You are helpful and harmless and you follow ethical guidelines and promote positive behavior."
register_template(
    CustomTemplateType.merlinite,
    Template(
        [], ['<|user|>\n{{QUERY}}\n<|assistant|>\n'],
        ['<|endoftext|>\n'], ['<|endoftext|>'], None,
        ['<|system|>\n{{SYSTEM}}\n']))

register_template(
    CustomTemplateType.c4ai_command_r,
    Template(
        [], ['<|user|>\n{{QUERY}}\n<|assistant|>\n'],
        ['<|endoftext|>\n'], ['<|endoftext|>'], None,
        ['<|system|>\n{{SYSTEM}}\n']))

register_template(
    CustomTemplateType.llama,
    Template(
        ['<s>[INST] '], ['{{QUERY}} [/INST]'], ['</s><s>[INST] '],
        ['</s>'], None,
        ['<s>[INST] <<SYS>>\n{{SYSTEM}}\n<</SYS>>\n\n'])
)

register_template(
    CustomTemplateType.llama3,
    Template(['<|begin_of_text|>'], [
        '<|start_header_id|>user<|end_header_id|>\n\n{{QUERY}}<|eot_id|>'
        '<|start_header_id|>assistant<|end_header_id|>\n\n'
    ], ['<|eot_id|>'], ['<|eot_id|>'], None, 
    ['<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{{SYSTEM}}<|eot_id|>']))

register_template(
    CustomTemplateType.gemma, Template(
    ['<bos>'],
    ['<start_of_turn>user\n{{QUERY}}<end_of_turn>\n<start_of_turn>model\n'],
    ['<end_of_turn>\n'], ['<end_of_turn>'], None,
    ['<bos><start_of_turn>system\n{{SYSTEM}}<end_of_turn>\n']))

register_template(
    CustomTemplateType.phi3,
    Template(['<s>'], ['<|user|>\n{{QUERY}}<|end|>\n<|assistant|>\n'], ['<|end|>\n'], ['<|end|>'], _default_phi3_system,
             ['<s><|system|>\n{{SYSTEM}}<|end|>\n']))

def _preprocess_stsb(dataset: HfDataset) -> HfDataset:
    prompt = """Task: Based on the given two sentences, provide a similarity score between 0.0 and 5.0.
Sentence 1: {text1}
Sentence 2: {text2}
Similarity score: """
    query = []
    response = []
    for d in dataset:
        query.append(prompt.format(text1=d['text1'], text2=d['text2']))
        response.append(f"{d['label']:.1f}")
    return HfDataset.from_dict({'query': query, 'response': response})


register_dataset(CustomDatasetName.stsb_en, 'swift/stsb', None, _preprocess_stsb, get_dataset_from_repo)

if __name__ == '__main__':
    # The Shell script can view `examples/pytorch/llm/scripts/custom`.
    # test dataset
    train_dataset, val_dataset = get_dataset([CustomDatasetName.stsb_en], check_dataset_strategy='warning')
    print(f'train_dataset: {train_dataset}')
    print(f'val_dataset: {val_dataset}')
    # test model base
    model, tokenizer = get_model_tokenizer(CustomModelType.tigerbot_13b, use_flash_attn=False)
    # test model chat
    model, tokenizer = get_model_tokenizer(CustomModelType.tigerbot_13b_chat, use_flash_attn=False)
    # test template
    template = get_template(CustomTemplateType.tigerbot, tokenizer)
    train_dataset = dataset_map(train_dataset, template.encode)
    print_example(train_dataset[0], tokenizer)