import os

os.environ['OMP_NUM_THREADS'] = '8'# 通过os.environ将量子线路模拟器的线程数设置为8
from hybrid import HybridModel
from hybrid import project_path
import numpy as np
import mindspore as ms
import mindspore.context as context
import mindspore.dataset as ds
from mindspore import Model
from mindspore.train.callback import LossMonitor
from mindquantum import *

ms.context.set_context(mode=ms.context.PYNATIVE_MODE, device_target="CPU")


class Main(HybridModel):
    def __init__(self):
        super().__init__()
        self.dataset = self.build_dataset(self.origin_x, self.origin_y, 10)
        self.qnet = MQLayer(self.build_grad_ops())
        self.model = self.build_model()
        self.checkpoint_name = os.path.join(project_path, "model.ckpt")

    def build_dataset(self, x, y, batch=None):
        train = ds.NumpySlicesDataset(
            {
                "image": x.reshape((x.shape[0], -1)),
                "label": y.astype(np.int32)
            },
            shuffle=False)
        if batch is not None:
            train = train.batch(batch)
        return train

    def build_grad_ops(self):
        circ = Circuit()#初始化量子线路
        for i in range(8):
            circ += RY(f'p{i}').on(i)
        circ += UN(X, [1, 3, 5, 7], [0, 2, 4, 6])
        circ += UN(X, [2, 4, 6], [1, 3, 5])
        circ += UN(X, [1, 3, 5, 7], [0, 2, 4, 6])
        circ += UN(X, [2, 4, 6], [1, 3, 5])
        encoder = add_prefix(circ, 'e1') + add_prefix(circ, 'e2')
        ansatz = add_prefix(circ, 'a1')
        total_circ = encoder + ansatz
        ham = Hamiltonian(QubitOperator('Z0'))
        sim = Simulator('projectq', total_circ.n_qubits)
        grad_ops = sim.get_expectation_with_grad(
            ham,
            total_circ,
            encoder_params_name=encoder.params_name,
            ansatz_params_name=ansatz.params_name,
            parallel_worker=5)
        return grad_ops

    def build_model(self):
        self.loss = ms.nn.SoftmaxCrossEntropyWithLogits(sparse=True,reduction='mean')
        self.opti = ms.nn.Adam(self.qnet.trainable_params())
        self.model = Model(self.qnet, self.loss, self.opti)
        return self.model

    def train(self):
        self.model.train(1, self.dataset, callbacks=LossMonitor())

    def export_trained_parameters(self):
        qnet_weight = self.qnet.weight.asnumpy()
        ms.save_checkpoint(self.qnet, self.checkpoint_name)

    def load_trained_parameters(self):
        ms.load_param_into_net(self.qnet,
                               ms.load_checkpoint(self.checkpoint_name))

    def predict(self, origin_test_x) -> float:
        test_x = origin_test_x.reshape((origin_test_x.shape[0], -1))
        predict = self.model.predict(ms.Tensor(test_x))
        predict = predict.asnumpy().flatten() > 0
        return predict
