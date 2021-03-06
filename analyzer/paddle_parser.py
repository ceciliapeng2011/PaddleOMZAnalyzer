import paddle
paddle.enable_static()
import paddle.fluid as fluid
import paddle.fluid.core as core
from pathlib import Path

import os
import argparse

def append_fetch_ops(program, fetch_target_names, fetch_holder_name='fetch'):
    """
    In this palce, we will add the fetch op
    """
    global_block = program.global_block()
    fetch_var = global_block.create_var(
        name=fetch_holder_name,
        type=core.VarDesc.VarType.FETCH_LIST,
        persistable=True)
    print("the len of fetch_target_names:%d" % (len(fetch_target_names)))
    for i, name in enumerate(fetch_target_names):

        global_block.append_op(
            type='fetch',
            inputs={'X': [name]},
            outputs={'Out': [fetch_var]},
            attrs={'col': i})

def insert_fetch(program, fetchs, fetch_holder_name="fetch"):
    global_block = program.global_block()
    need_to_remove_op_index = list()
    for i, op in enumerate(global_block.ops):
        if op.type == 'fetch':
            need_to_remove_op_index.append(i)
    for index in need_to_remove_op_index[::-1]:
        global_block._remove_op(index)
    program.desc.flush()
    append_fetch_ops(program, fetchs, fetch_holder_name)


def get_ops(paddelmodel_dir):
    p = Path(paddelmodel_dir)

    pdmodel = p.glob('**/*.pdmodel')
    scattered = p.glob('__model__')

    models = []
    for path in pdmodel:
        models.append(path)
        # print(path)
    for path in scattered:
        models.append(path)
        # print(path)

    if len(models) != 1:
        return 'ERROR'

    pdmodel_path = Path(models[0])

    # 加载模型
    exe = fluid.Executor(fluid.CPUPlace())
    if pdmodel_path.suffix=='.pdmodel':
        pdmodel_prefix = os.path.join(pdmodel_path.parent, pdmodel_path.stem)
        [prog, feed, fetchs] = paddle.static.load_inference_model(
                            pdmodel_prefix,
                            exe)
    else:
        [prog, feed, fetchs] = paddle.static.load_inference_model(
                    str(pdmodel_path.parent),
                    exe, model_filename='__model__', params_filename='__params__')

    # print(len(prog.blocks))

    def get_tensor_shape(tensor_name):
        for block in prog.blocks:
            if tensor_name in block.vars:
                var = block.vars[tensor_name]
                if var.type.name in {'LOD_TENSOR', 'LOD_TENSOR_ARRAY'}: # others: STEP_SCOPES, FEED_MINIBATCH, FETCH_LIST, etc.
                    return var.name, var.type, var.shape
                return var.name, var.type, None
        return None, None, None    

    operator_set = set(())
    
    for k in range(len(prog.blocks)):
        # 输出计算图所有结点信息
        for i, op in enumerate(prog.blocks[k].ops):
            # print("########", i, op.type)

            if op.type in { 'fetch', 'feed' }:
                continue
            
            #
            operator_set.add(op.type)

            # debug
            # if op.type in {'pad3d'}:
            #     mode = op.attr('mode')
            #     if mode == 'circular': # circular
            #         print('{} has {} pad3d'.format(pdmodel_path, mode))

            # if op.type in {'write_to_array'}:
            #     ta_name, ta_type, ta_shape = get_tensor_shape(op.output('Out')[0])
            #     print('block {} has {} on tensorarray {} with shape {}'.format(k, op.type, ta_name, ta_shape))
        
            for ta in op.input_arg_names:
                ta_name, ta_type, ta_shape = get_tensor_shape(ta)
                if ta_type.name == 'LOD_TENSOR_ARRAY':
                    print('block {} has {} on tensorarray input {} with shape {}'.format(k, op.type, ta_name, ta_shape))

            for ta in op.output_arg_names:
                ta_name, ta_type, ta_shape = get_tensor_shape(ta)
                if ta_type.name == 'LOD_TENSOR_ARRAY':
                    print('block {} has {} on tensorarray output {} with shape {}'.format(k, op.type, ta_name, ta_shape))

    return sorted(operator_set)


__dir__ = os.path.dirname(os.path.abspath(__file__))
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", type=str, default='', help="model dir")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    if os.path.isdir(args.model_dir):
        operator_set = get_ops(args.model_dir)

        # print(operator_set, len(operator_set))
    else:
        #*.pdmodel
        test_model = os.path.abspath(os.path.join(__dir__, '../exporter/paddleclas/MobileNetV3_large_x1_0'))
        operator_set = get_ops(test_model)

        print(operator_set, len(operator_set))

        # __model__
        test_model = os.path.abspath(os.path.join(__dir__, '../exporter/paddledet/blazeface_keypoint'))
        operator_set = get_ops(test_model)

        print(operator_set, len(operator_set))
