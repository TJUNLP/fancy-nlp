# -*- coding: utf-8 -*-

from keras.callbacks import Callback
from seqeval import metrics


class NERMetric(Callback):
    """
    callback for evaluating ner model
    """
    def __init__(self, preprocessor, valid_data, valid_labels):
        """
        Args:
            preprocessor: `NERPreprocessor` instance to help prepare input for ner model
            valid_data: list of tokenized texts (, like ``[['我', '是', '中', '国', '人']]``
            valid_labels: list of list of str, the corresponding label strings
        """
        self.preprocessor = preprocessor
        self.valid_data = valid_data
        self.valid_labels = valid_labels
        self.valid_features, self.valid_y = self.preprocessor.prepare_input(valid_data,
                                                                            valid_labels)
        super(NERMetric, self).__init__()

    def get_lengths(self, pred_probs):
        return [min(len(valid_label), pred_prob.shape[0])
                for valid_label, pred_prob in zip(self.valid_labels, pred_probs)]

    def on_epoch_end(self, epoch, logs=None):
        pred_probs = self.model.predict(self.valid_features)
        y_pred = self.preprocessor.label_decode(pred_probs, self.get_lengths(pred_probs))

        r = metrics.recall_score(self.valid_labels, y_pred)
        p = metrics.precision_score(self.valid_labels, y_pred)
        f1 = metrics.f1_score(self.valid_labels, y_pred)

        logs['val_r'] = r
        logs['val_p'] = p
        logs['val_f1'] = f1
        print('Epoch {}: val_r: {}, val_p: {}, val_f1: {}'.format(epoch, r, p, f1))
        print(metrics.classification_report(self.valid_labels, y_pred))
