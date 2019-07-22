import tensorflow as tf

from atlas.models.graphs.tensorflow import Network
from atlas.models.graphs.tensorflow.configs import Parameters


class GGNN(Network):
    """The original assembly of propagators and output computation as described in
    https://github.com/microsoft/gated-graph-neural-network-samples/blob/master/chem_tensorflow_sparse.py"""
    def __init__(self,
                 propagator,
                 classifier,
                 optimizer,
                 params: Parameters):

        super().__init__()
        self.propagator = propagator
        self.classifier = classifier
        self.optimizer = optimizer

        self.params = params

    def build(self):
        self.propagator.build()
        self.classifier.build(node_embeddings=self.propagator.ops['final_node_embeddings'])
        self.optimizer.build(loss=self.classifier.ops['loss'])

