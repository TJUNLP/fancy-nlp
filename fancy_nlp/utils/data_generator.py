# -*- coding: utf-8 -*-

import math

import numpy as np
from keras.utils import Sequence


class NERGenerator(Sequence):
    """Data Generator for NER
    """
    def __init__(self, preprocessor, data, labels=None, batch_size=32, shuffle=True):
        """
        Args:
            preprocessor: `NERPreprocessor` instance to help prepare input for ner model
            data: list of tokenized texts (, like ``[['我', '是', '中', '国', '人']]``
            labels: list of list of str, the corresponding label strings
            batch_size: how many samples to train on in one iteration
            shuffle: whether to shuffle data after each epoch of training
        """
        self.preprocessor = preprocessor
        self.data = data
        self.labels = labels
        self.data_size = len(self.data)
        self.batch_size = batch_size
        self.indices = np.arange(self.data_size)
        self.steps = int(math.ceil(self.data_size / self.batch_size))
        self.shuffle = shuffle

    def __len__(self):
        return self.steps

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)

    def __getitem__(self, index):
        batch_index = self.indices[index * self.batch_size: (index + 1) * self.batch_size]
        if self.labels is not None:
            batch_data, batch_labels = zip(*[(self.data[i], self.labels[i]) for i in batch_index])
        else:
            batch_data = [self.data[i] for i in batch_index]
            batch_labels = None
        return self.preprocessor.prepare_input(batch_data, batch_labels)
