# -*- coding: utf-8 -*-

import os

from absl import logging
from keras.models import model_from_json
from keras.utils import get_file

from fancy_nlp.preprocessors import NERPreprocessor
from fancy_nlp.models.ner import *
from fancy_nlp.trainers import NERTrainer
from fancy_nlp.predictors import NERPredictor
from fancy_nlp.utils import get_custom_objects


class NER(object):
    """NER application"""

    def __init__(self):
        self.preprocessor = None
        self.model = None
        self.trainer = None
        self.predictor = None

        self.load_pretrained_model()

    def fit(self,
            train_data,
            train_labels,
            valid_data=None,
            valid_labels=None,
            ner_model_type='bilstm_cnn',
            use_char=True,
            char_embed_type='word2vec',
            char_embed_dim=300,
            char_embed_trainable=True,
            use_bert=False,
            bert_vocab_file=None,
            bert_config_file=None,
            bert_checkpoint_file=None,
            bert_trainable=False,
            use_word=False,
            external_word_dict=None,
            word_embed_type='word2vec',
            word_embed_dim=300,
            word_embed_trainable=True,
            max_len=None,
            use_crf=True,
            optimizer='adam',
            batch_size=32,
            epochs=50,
            callback_list=None,
            checkpoint_dir=None,
            model_name=None,
            load_swa_model=False,
            **kwargs):
        """Train ner model using provided data

        Args:
            train_data: list of tokenized (in char level) texts for training,
                        like ``[['我', '是', '中', '国', '人']]``
            train_labels: labels string of train_data
            valid_data: list of tokenized (in char level) texts for evaluation
            valid_labels: labels string of valid data
            ner_model_type: str, which ner model to use
            use_char: boolean, whether to use char embedding as input
            char_embed_type: str, can be a pre-trained embedding filename or pre-trained embedding
                             methods (word2vec, fasttext)
            char_embed_dim: int, dimensionality of char embedding
            char_embed_trainable: boolean, whether to update char embedding during training
            use_bert: boolean, whether to use bert embedding as input
            bert_vocab_file: str, path to bert's vocabulary file
            bert_config_file: str, path to bert's configuration file
            bert_checkpoint_file: str, path to bert's checkpoint file
            bert_trainable: boolean, whether to update bert during training
            use_word: boolean, whether to use word as additional input
            external_word_dict: list of words, external word dictionary
            word_embed_dim: similar as 'char_embed_dim'
            word_embed_type: similar as 'char_embed_type'
            word_embed_trainable: similar as 'char_embed_trainable'
            max_len: int, max sequence len. If None, we dynamically use the max length of one batch
                     as max_len. However, max_len must be provided when using bert as input.
            use_crf: boolean, whether to use crf layer
            optimizer: str, optimizer to use during training
            batch_size: num of samples per gradient update
            epochs: num of epochs to train the model
            callback_list: list of str, each item indicates the callback to apply during training
                           Currently, we support using 'modelcheckpoint' for `ModelCheckpoint`
                           callback, 'earlystopping` for 'Earlystopping` callback, 'swa' for
                           'SWA' callback. We will automatically add `NERMetric` callback when
                           valid_data and valid_labels are both provided.
            checkpoint_dir: str, directory to save ner model, must be provided when using
                            `ModelCheckpoint` or `SWA` callback.
            model_name: str, prefix of ner model's weights filem must be provided when using
                        `ModelCheckpoint` or `SWA` callback.
                        For example, if checkpoint_dir is 'ckpt' and model_name is 'model', the
                        weights of ner model saved by `ModelCheckpoint` callback will be
                        'ckpt/model.hdf5' and by `SWA` callback will be 'ckpt/model_swa.hdf5'
            load_swa_model: boolean, whether to load swa model, only apply when using SWA Callback.
            **kwargs: other argument for building ner model, such as "rnn_units", "fc_dim" etc.
        """
        self.preprocessor = NERPreprocessor(train_data=train_data,
                                            train_labels=train_labels,
                                            use_char=use_char,
                                            use_bert=use_bert,
                                            use_word=use_word,
                                            external_word_dict=external_word_dict,
                                            bert_vocab_file=bert_vocab_file,
                                            char_embed_type=char_embed_type,
                                            char_embed_dim=char_embed_dim,
                                            word_embed_type=word_embed_type,
                                            word_embed_dim=word_embed_dim,
                                            max_len=max_len)

        self.model = self.get_ner_model(ner_model_type=ner_model_type,
                                        num_class=self.preprocessor.num_class,
                                        use_char=use_char,
                                        char_embeddings=self.preprocessor.char_embeddings,
                                        char_vocab_size=self.preprocessor.char_vocab_size,
                                        char_embed_dim=self.preprocessor.char_embed_dim,
                                        char_embed_trainable=char_embed_trainable,
                                        use_bert=use_bert,
                                        bert_config_file=bert_config_file,
                                        bert_checkpoint_file=bert_checkpoint_file,
                                        bert_trainable=bert_trainable,
                                        use_word=use_word,
                                        word_embeddings=self.preprocessor.word_embeddings,
                                        word_vocab_size=self.preprocessor.word_vocab_size,
                                        word_embed_dim=self.preprocessor.word_embed_dim,
                                        word_embed_trainable=word_embed_trainable,
                                        max_len=self.preprocessor.max_len,
                                        use_crf=use_crf,
                                        optimizer=optimizer,
                                        **kwargs)

        if 'swa' in callback_list:
            swa_model = self.get_ner_model(ner_model_type=ner_model_type,
                                           num_class=self.preprocessor.num_class,
                                           use_char=use_char,
                                           char_embeddings=self.preprocessor.char_embeddings,
                                           char_vocab_size=self.preprocessor.char_vocab_size,
                                           char_embed_dim=self.preprocessor.char_embed_dim,
                                           char_embed_trainable=char_embed_trainable,
                                           use_bert=use_bert,
                                           bert_config_file=bert_config_file,
                                           bert_checkpoint_file=bert_checkpoint_file,
                                           bert_trainable=bert_trainable,
                                           use_word=use_word,
                                           word_embeddings=self.preprocessor.word_embeddings,
                                           word_vocab_size=self.preprocessor.word_vocab_size,
                                           word_embed_dim=self.preprocessor.word_embed_dim,
                                           word_embed_trainable=word_embed_trainable,
                                           max_len=self.preprocessor.max_len,
                                           use_crf=use_crf,
                                           optimizer=optimizer,
                                           **kwargs)
        else:
            swa_model = None

        self.trainer = NERTrainer(self.model, self.preprocessor)
        self.trainer.train_generator(train_data, train_labels, valid_data, valid_labels,
                                     batch_size, epochs, callback_list, checkpoint_dir, model_name,
                                     swa_model, load_swa_model)

        self.predictor = NERPredictor(self.model, self.preprocessor)

        if valid_data is not None and valid_labels is not None:
            logging.info('Evaluating on validation data...')
            self.score(valid_data, valid_labels)

    def score(self, valid_data, valid_labels):
        """Return the f1 score of the model over validation data

        Args:
            valid_data: list of tokenized texts
            valid_labels: list of label strings

        Returns:

        """
        if self.trainer:
            return self.trainer.evaluate(valid_data, valid_labels)
        else:
            logging.fatal('Trainer is None! Call fit() or load() to get trainer.')

    def predict(self, test_text):
        """Return prediction of the model for test data

        Args:
            test_text: untokenized text or tokenized (in char level) text

        Returns:

        """
        if self.predictor:
            return self.predictor.tag(test_text)
        else:
            logging.fatal('Predictor is None! Call fit() or load() to get predictor.')

    def predict_batch(self, test_texts):
        """Return predictions of the model for test data

        Args:
            test_texts: list of untokenized texts or tokenized (in char level) texts

        Returns:

        """
        if self.predictor:
            return self.predictor.tag_batch(test_texts)
        else:
            logging.fatal('Predictor is None! Call fit() or load() to get predictor.')

    def analyze(self, text):
        """Analyze text and return pretty format.

        Args:
            text: untokenized text or tokenized (in char level) text
        Returns:

        """
        if self.predictor:
            return self.predictor.pretty_tag(text)
        else:
            logging.fatal('Predictor is None! Call fit() or load() to get predictor.')

    def analyze_batch(self, texts):
        """Analyze batch of texts and return pretty format.

        Args:
            texts: untokenized texts or tokenized (in char level) texts
        Returns:

        """
        if self.predictor:
            return self.predictor.pretty_tag_batch(texts)
        else:
            logging.fatal('Predictor is None! Call fit() or load() to get predictor.')

    def restrict_analyze(self, text, threshold=0.85):
        if self.predictor:
            return self.predictor.restrict_tag(text, threshold)
        else:
            logging.fatal('Predictor is None! Call fit() or load() to get predictor.')

    def restrict_analyze_batch(self, texts, threshold=0.85):
        if self.predictor:
            return self.predictor.restrict_tag_batch(texts, threshold)
        else:
            logging.fatal('Predictor is None! Call fit() or load() to get predictor.')

    def save(self, preprocessor_file, json_file, weights_file=None):
        """save ner application
        
        Args:
            preprocessor_file: path to save preprocessor
            json_file: path to save model architecture
            weights_file: path to save model weights, can be None. When we use `ModelCheckpoint` 
                          or `SWA` callback, model's weights will be saved to disk after training.
                          In that case, we don't need to save it again. We usually set weights_file
                          to be None.
        """
        self.preprocessor.save(preprocessor_file)
        logging.info('Save preprocessor to {}'.format(preprocessor_file))

        model_json = self.model.to_json()
        with open(json_file, 'w') as writer:
            writer.write(model_json)
        logging.info('Save model architecture to {}'.format(json_file))

        if weights_file:
            self.model.save_weights(weights_file)
            logging.info('Save model weights to {}'.format(weights_file))

    def load(self, preprocessor_file, json_file, weights_file, custom_objects=None):
        """load ner application

        Args:
            preprocessor_file: path to load preprocessor
            json_file: path to load model architecture
            weights_file: path to load model weights
            custom_objects: Optional dictionary mapping names (strings) to custom classes or
                            functions to be considered during deserialization. Must provided when
                            using custom layer.

        """
        self.preprocessor = NERPreprocessor.load(preprocessor_file)
        logging.info('Load preprocessor from {}'.format(preprocessor_file))

        custom_objects = custom_objects or {}
        custom_objects.update(get_custom_objects())
        with open(json_file, 'r') as reader:
            self.model = model_from_json(reader.read(), custom_objects=custom_objects)
        logging.info('Load model architecture from {}'.format(json_file))

        self.model.load_weights(weights_file)
        logging.info('Load model weight from {}'.format(weights_file))

        self.trainer = NERTrainer(self.model, self.preprocessor)
        self.predictor = NERPredictor(self.model, self.preprocessor)

    @staticmethod
    def get_ner_model(ner_model_type, num_class, use_char, char_embeddings, char_vocab_size,
                      char_embed_dim, char_embed_trainable, use_bert, bert_config_file,
                      bert_checkpoint_file, bert_trainable, use_word, word_embeddings,
                      word_vocab_size, word_embed_dim, word_embed_trainable, max_len,
                      use_crf, optimizer, **kwargs):
        if ner_model_type == 'bilstm':
            ner_model = BiLSTMNER(
                num_class=num_class,
                use_char=use_char,
                char_embeddings=char_embeddings,
                char_vocab_size=char_vocab_size,
                char_embed_dim=char_embed_dim,
                char_embed_trainable=char_embed_trainable,
                use_bert=use_bert,
                bert_config_file=bert_config_file,
                bert_checkpoint_file=bert_checkpoint_file,
                bert_trainable=bert_trainable,
                use_word=use_word,
                word_embeddings=word_embeddings,
                word_vocab_size=word_vocab_size,
                word_embed_dim=word_embed_dim,
                word_embed_trainable=word_embed_trainable,
                max_len=max_len,
                use_crf=use_crf,
                optimizer=optimizer,
                **kwargs
            )
        elif ner_model_type == 'bilstm_cnn':
            ner_model = BiLSTMCNNNER(
                num_class=num_class,
                use_char=use_char,
                char_embeddings=char_embeddings,
                char_vocab_size=char_vocab_size,
                char_embed_dim=char_embed_dim,
                char_embed_trainable=char_embed_trainable,
                use_bert=use_bert,
                bert_config_file=bert_config_file,
                bert_checkpoint_file=bert_checkpoint_file,
                bert_trainable=bert_trainable,
                use_word=use_word,
                word_embeddings=word_embeddings,
                word_vocab_size=word_vocab_size,
                word_embed_dim=word_embed_dim,
                word_embed_trainable=word_embed_trainable,
                max_len=max_len,
                use_crf=use_crf,
                optimizer=optimizer,
                **kwargs
            )
        elif ner_model_type == 'bigru':
            ner_model = BiGRUNER(
                num_class=num_class,
                use_char=use_char,
                char_embeddings=char_embeddings,
                char_vocab_size=char_vocab_size,
                char_embed_dim=char_embed_dim,
                char_embed_trainable=char_embed_trainable,
                use_bert=use_bert,
                bert_config_file=bert_config_file,
                bert_checkpoint_file=bert_checkpoint_file,
                bert_trainable=bert_trainable,
                use_word=use_word,
                word_embeddings=word_embeddings,
                word_vocab_size=word_vocab_size,
                word_embed_dim=word_embed_dim,
                word_embed_trainable=word_embed_trainable,
                max_len=max_len,
                use_crf=use_crf,
                optimizer=optimizer,
                **kwargs
            )
        elif ner_model_type == 'bigru_cnn':
            ner_model = BiGRUCNNNER(
                num_class=num_class,
                use_char=use_char,
                char_embeddings=char_embeddings,
                char_vocab_size=char_vocab_size,
                char_embed_dim=char_embed_dim,
                char_embed_trainable=char_embed_trainable,
                use_bert=use_bert,
                bert_config_file=bert_config_file,
                bert_checkpoint_file=bert_checkpoint_file,
                bert_trainable=bert_trainable,
                use_word=use_word,
                word_embeddings=word_embeddings,
                word_vocab_size=word_vocab_size,
                word_embed_dim=word_embed_dim,
                word_embed_trainable=word_embed_trainable,
                max_len=max_len,
                use_crf=use_crf,
                optimizer=optimizer,
                **kwargs
            )
        elif ner_model_type == 'bert':
            ner_model = BertNER(
                num_class=num_class,
                bert_config_file=bert_config_file,
                bert_checkpoint_file=bert_checkpoint_file,
                bert_trainable=bert_trainable,
                max_len=max_len,
                use_crf=use_crf,
                optimizer=optimizer,
                **kwargs
            )
        else:
            raise ValueError('`ner_model_type` not understood: {}'.format(ner_model_type))

        return ner_model.build_model()

    def load_pretrained_model(self):
        cache_subdir = 'pretrained_models'

        prefix = 'https://fancy-nlp-1253403094.cos.ap-shanghai.myqcloud.com/pretrained_models/'

        preprocessor_file = get_file(fname='msra_ner_bilstm_cnn_crf_preprocessor.pkl',
                                     origin=prefix+'msra_ner_bilstm_cnn_crf_preprocessor.pkl',
                                     cache_subdir=cache_subdir)
        json_file = get_file(fname='msra_ner_bilstm_cnn_crf.json',
                             origin=prefix+'msra_ner_bilstm_cnn_crf.json',
                             cache_subdir=cache_subdir)
        weights_file = get_file(fname='msra_ner_bilstm_cnn_crf.hdf5',
                                origin=prefix+'msra_ner_bilstm_cnn_crf.hdf5',
                                cache_subdir=cache_subdir)

        self.load(preprocessor_file, json_file, weights_file)
