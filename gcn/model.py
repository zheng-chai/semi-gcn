from gcn.inits import masked_accuracy
from gcn.layers import GraphConvolution
from gcn.loss import masked_softmax_cross_entropy_loss, masked_softmax_backward
from gcn.utils import l2_loss

import tensorflow as tf
import numpy as np

flags = tf.app.flags
FLAGS = flags.FLAGS


class Model(object):
    """model """

    def __init__(self):
        """init feathers, labels, input_dim"""
        # vars and placeholders
        self.vars = {}
        self.placeholders = {}

        # layers
        self.layers = []
        # activations
        self.activations = []

        # special input and output
        self.inputs = None
        self.outputs = None

        self.loss = 0
        self.accuracy = 0

    def _loss(self):
        """return loss, grad"""
        return NotImplementedError

    def _accuracy(self):
        """return accuracy"""
        return NotImplementedError

    def _backgrad(self):
        """back grad"""
        return NotImplementedError

    def _build(self):
        """add layers"""
        return NotImplementedError


class GCN(Model):
    def __init__(self, placeholders, input_dim):
        super(GCN, self).__init__()
        self.inputs = placeholders['features']
        self.input_dim = input_dim  # can easily get by self.inputs
        self.output_dim = placeholders['labels'].shape[1]
        self.placeholders = placeholders
        self._build()
        self.activations = [self.inputs] * (len(self.layers) + 1)

    def _build(self):
        # input_dim, output_dim, placeholders, act, dropput, sparse_inputs
        # attention! there are something else:
        self.layers.append(GraphConvolution(input_dim=self.input_dim,
                                            output_dim=FLAGS.hidden1,
                                            placeholders=self.placeholders,
                                            act=lambda x: np.maximum(x, 0),
                                            back_act=lambda x: np.where(x <= 0, 0, 1),
                                            dropout=True,
                                            sparse_inputs=False))
        self.layers.append(GraphConvolution(input_dim=FLAGS.hidden1,
                                            output_dim=self.output_dim,
                                            placeholders=self.placeholders,
                                            act=lambda x: x,
                                            back_act=lambda x: np.where(x == np.inf, 0, 1),
                                            dropout=True,
                                            sparse_inputs=False))

    def one_train(self):
        self._forward()
        self._loss()
        self._accuracy()
        self._backgrad()
        return self.loss, self.accuracy

    def _forward(self):
        for i, layer in enumerate(self.layers):
            hidden = layer.call(self.activations[i])
            self.activations[i + 1] = hidden

        self.outputs = self.activations[-1]

    def _loss(self):
        """require outputs"""
        # Weight decay loss
        # for var in self.layers[0].vars.values():
        #     self.loss += FLAGS.weight_decay * l2_loss(var)

        # print("weight decay loss", self.loss)
        # Cross entropy loss
        self.loss = masked_softmax_cross_entropy_loss(self.outputs,
                                                       self.placeholders['labels'],
                                                       self.placeholders['labels_mask'])
        return self.loss

    def _accuracy(self):
        self.accuracy = masked_accuracy(self.outputs, self.placeholders['labels'],
                                        self.placeholders['labels_mask'])

    def _backgrad(self):
        # update the gradient
        grad_pre_layer = masked_softmax_backward(self.outputs,
                                                 self.placeholders['labels'],
                                                 self.placeholders['labels_mask'])
        print("grad_pre_layer", grad_pre_layer.shape, grad_pre_layer)

        m, n = self.outputs.shape
        print("m: {}, n: {}".format(m, n))
        h = 1e-8
        grad_weights = np.zeros(self.outputs.shape)
        for i in range(m):
            for j in range(n):
                self.outputs[i, j] += h
                loss1 = self._loss()
                self.outputs[i, j] -= 2 * h
                loss2 = self._loss()
                grad_weights[i, j] = (loss1 - loss2) / (2 * h)
                self.outputs[i, j] += h

        print("grad_weights", grad_weights)

        # update every layer
        for i, layer in enumerate(reversed(self.layers)):
            grad_weight, grad_pre_layer = layer.back(grad_pre_layer)  # weight
            print("grad_weight", grad_weight)
            print("check_grad", self.check_grad(self.layers[-(i+1)].vars['weight']))
            layer.vars['weight'] -= 0.01 * grad_weight
            # layer.vars['weight'] = layer.adam.minimize(grad_weight)  # adam

    def check_grad(self, weights):
        # check grad is true
        h = 1e-8
        grad_weights = np.zeros(weights.shape)
        for i in range(weights.shape[0]):
            for j in range(weights.shape[1]):
                weights[i, j] += h
                loss1 = self._loss()
                weights[i, j] -= 2*h
                loss2 = self._loss()
                grad_weights[i, j] = (loss1 - loss2) / (2*h)
                weights[i, j] += h

        print("check grad", grad_weights)


    def evaluate(self, y_val, val_mask):  # change
        self.placeholders['labels'] = y_val
        self.placeholders['labels_mask'] = val_mask
        self._loss()
        self._accuracy()
        return self.loss, self.accuracy

