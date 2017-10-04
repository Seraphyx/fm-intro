'''
Attentional Factorization Machines
https://arxiv.org/pdf/1708.04617.pdf

Format: https://github.com/aicodes/tf-bestpractice

Methods represented
1) Inference
	- Initialize Graph
2) Loss
3) Optimizer
'''

import math
import os
import argparse
from time import time

import numpy as np
import tensorflow as tf
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import mean_squared_error, accuracy_score
from tensorflow.contrib.layers.python.layers import batch_norm as batch_norm


#################### Arguments ####################
def parse_args():
	parser = argparse.ArgumentParser(description="Run DeepFM.")
	parser.add_argument('--process', nargs='?', default='train',
						help='Process type: train, evaluate.')
	parser.add_argument('--mla', type=int, default=0,
						help='Set the experiment mode to be Micro Level Analysis or not: 0-disable, 1-enable.')
	parser.add_argument('--path', nargs='?', default='../data/',
						help='Input data path.')
	parser.add_argument('--dataset', nargs='?', default='ml-tag',
						help='Choose a dataset.')
	parser.add_argument('--valid_dimen', type=int, default=3,
						help='Valid dimension of the dataset. (e.g. frappe=10, ml-tag=3)')
	parser.add_argument('--epoch', type=int, default=20,
						help='Number of epochs.')
	parser.add_argument('--pretrain', type=int, default=-1,
						help='flag for pretrain. 1: initialize from pretrain; 0: randomly initialize; -1: save to pretrain file; 2: initialize from pretrain and save to pretrain file')
	parser.add_argument('--batch_size', type=int, default=4096,
						help='Batch size.')
	parser.add_argument('--attention', type=int, default=1,
						help='flag for attention. 1: use attention; 0: no attention')
	parser.add_argument('--factor_k', nargs='?', default='[16,16]',
						help='Number of hidden factors.')
	parser.add_argument('--lamda_attention', type=float, default=1e+2,
						help='Regularizer for attention part.')
<<<<<<< HEAD
	parser.add_argument('--keep', nargs='+', type=float, default=[1.0, 0.5],
=======
	parser.add_argument('--keep', nargs='?', default='[1.0,0.5]',
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
						help='Keep probility (1-dropout) of each layer. 1: no dropout. The first index is for the attention-aware pairwise interaction layer.')
	parser.add_argument('--lr', type=float, default=0.1,
						help='Learning rate.')
	parser.add_argument('--freeze_fm', type=int, default=0,
						help='Freese all params of fm and learn attention params only.')
	parser.add_argument('--optimizer', nargs='?', default='AdagradOptimizer',
						help='Specify an optimizer type (AdamOptimizer, AdagradOptimizer, GradientDescentOptimizer, MomentumOptimizer).')
	parser.add_argument('--verbose', type=int, default=1,
						help='Whether to show the performance of each epoch (0 or 1)')
	parser.add_argument('--batch_norm', type=int, default=0,
					help='Whether to perform batch normaization (0 or 1)')
	parser.add_argument('--decay', type=float, default=0.999,
					help='Decay value for batch norm')
	parser.add_argument('--activation', nargs='?', default='relu',
					help='Which activation function to use for deep layers: relu, sigmoid, tanh, identity')

	return parser.parse_args()

class AFM(BaseEstimator, TransformerMixin):
<<<<<<< HEAD
	def __init__(self, features_p, pretrain_flag, save_file, attention, hidden_factor_1, hidden_factor_2, valid_dimension, activation_function,
				 freeze_fm, epoch, batch_size, learning_rate, lamda_attention, keep_1, keep_2, optimizer_type, batch_norm, decay, verbose, micro_level_analysis, random_seed=2016):
=======
	def __init__(self, features_p, pretrain_flag, save_file, attention, factor_k, valid_dimension, activation_function,
				 freeze_fm, epoch, batch_size, learning_rate, lamda_attention, keep, optimizer_type, batch_norm, decay, verbose, micro_level_analysis, random_seed=2016):
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
		# bind params to class
		self.batch_size = batch_size
		self.learning_rate = learning_rate
		self.attention = attention
<<<<<<< HEAD
		self.factor_k = [hidden_factor_1, hidden_factor_2]
=======
		self.factor_k = factor_k
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
		self.valid_dimension = valid_dimension
		self.activation_function = activation_function
		self.save_file = save_file
		self.pretrain_flag = pretrain_flag
		self.features_p = features_p
		self.lamda_attention = lamda_attention
<<<<<<< HEAD
		self.keep = [keep_1, keep_2]
=======
		self.keep = keep
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
		self.freeze_fm = freeze_fm
		self.epoch = epoch
		self.random_seed = random_seed
		self.optimizer_type = optimizer_type
		self.batch_norm = batch_norm
		self.decay = decay
		self.verbose = verbose
		self.micro_level_analysis = micro_level_analysis
		# performance of each epoch
		self.train_rmse, self.valid_rmse, self.test_rmse = [], [], []

		# init all variables in a tensorflow graph
		self._init_graph()

	def _init_graph(self):
		'''
		Init a tensorflow Graph containing: input data, variables, model, loss, optimizer
		'''
		self.graph = tf.Graph()
		with self.graph.as_default():  # , tf.device('/cpu:0'):
			# Set graph level random seed
			tf.set_random_seed(self.random_seed)
			# Input data.
			self.train_features = tf.placeholder(tf.int32, shape=[None, None], name="train_features_afm")  # None * features_p
			self.train_labels = tf.placeholder(tf.float32, shape=[None, 1], name="train_labels_afm")  # None * 1
			self.dropout_keep = tf.placeholder(tf.float32, shape=[None], name="dropout_keep_afm")
			self.train_phase = tf.placeholder(tf.bool, name="train_phase_afm")

			# Variables.
			self.weights = self._initialize_weights()

			# Model.
			self.nonzero_embeddings = tf.nn.embedding_lookup(self.weights['feature_embeddings'], self.train_features) # None * M' * K
			
			element_wise_product_list = []
			count = 0
			for i in range(0, self.valid_dimension):
				for j in range(i+1, self.valid_dimension):
					element_wise_product_list.append(tf.multiply(self.nonzero_embeddings[:,i,:], self.nonzero_embeddings[:,j,:]))
					count += 1
			self.element_wise_product = tf.stack(element_wise_product_list) # (M'*(M'-1)) * None * K
			self.element_wise_product = tf.transpose(self.element_wise_product, perm=[1,0,2], name="element_wise_product") # None * (M'*(M'-1)) * K
			self.interactions = tf.reduce_sum(self.element_wise_product, 2, name="interactions")
			# _________ MLP Layer / attention part _____________
			num_interactions = self.valid_dimension*(self.valid_dimension-1)/2
			if self.attention:
				self.attention_mul = tf.reshape(tf.matmul(tf.reshape(self.element_wise_product, shape=[-1, self.factor_k[1]]), \
<<<<<<< HEAD
					self.weights['attention_W']), shape=[-1, tf.to_int32(num_interactions), tf.to_int32(self.factor_k[0])])
=======
					self.weights['attention_W']), shape=[-1, num_interactions, self.factor_k[0]])
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
				self.attention_exp = tf.exp(tf.reduce_sum(tf.multiply(self.weights['attention_p'], tf.nn.relu(self.attention_mul + \
					self.weights['attention_b'])), 2, keep_dims=True)) # None * (M'*(M'-1)) * 1
				self.attention_sum = tf.reduce_sum(self.attention_exp, 1, keep_dims=True) # None * 1 * 1
				self.attention_out = tf.div(self.attention_exp, self.attention_sum, name="attention_out") # None * (M'*(M'-1)) * 1
				self.attention_out = tf.nn.dropout(self.attention_out, self.dropout_keep[0]) # dropout
			
			# _________ Attention-aware Pairwise Interaction Layer _____________
			if self.attention:
				self.AFM = tf.reduce_sum(tf.multiply(self.attention_out, self.element_wise_product), 1, name="afm") # None * K
			else:
				self.AFM = tf.reduce_sum(self.element_wise_product, 1, name="afm") # None * K
			self.AFM_FM = tf.reduce_sum(self.element_wise_product, 1, name="afm_fm") # None * K
			self.AFM_FM = self.AFM_FM / num_interactions
			self.AFM = tf.nn.dropout(self.AFM, self.dropout_keep[1]) # dropout

			# _________ out _____________
			if self.micro_level_analysis:
				self.out = tf.reduce_sum(self.AFM, 1, keep_dims=True, name="out_afm")
				self.out_fm = tf.reduce_sum(self.AFM_FM, 1, keep_dims=True, name="out_fm")
			else:
				self.prediction = tf.matmul(self.AFM, self.weights['prediction']) # None * 1
				Bilinear = tf.reduce_sum(self.prediction, 1, keep_dims=True)  # None * 1
				self.Feature_bias = tf.reduce_sum(tf.nn.embedding_lookup(self.weights['feature_bias'], self.train_features) , 1)  # None * 1
				Bias = self.weights['bias'] * tf.ones_like(self.train_labels)  # None * 1
				self.out = tf.add_n([Bilinear, self.Feature_bias, Bias], name="out_afm")  # None * 1

			# Compute the loss.
			if self.attention and self.lamda_attention > 0:
				self.loss = tf.nn.l2_loss(tf.subtract(self.train_labels, self.out)) + tf.contrib.layers.l2_regularizer(self.lamda_attention)(self.weights['attention_W'])  # regulizer
			else:
				self.loss = tf.nn.l2_loss(tf.subtract(self.train_labels, self.out))

<<<<<<< HEAD
			# Set the summary snapshot loss
			self.summary_train = tf.summary.scalar('loss_train', self.loss)
			self.summary_valid = tf.summary.scalar('loss_valid', self.loss)

			# Optimizer.
			if self.optimizer_type == 'AdamOptimizer':
				optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate, beta1=0.9, beta2=0.999, epsilon=1e-8)
			elif self.optimizer_type == 'AdagradOptimizer':
				optimizer = tf.train.AdagradOptimizer(learning_rate=self.learning_rate, initial_accumulator_value=1e-8)
			elif self.optimizer_type == 'GradientDescentOptimizer':
				optimizer = tf.train.GradientDescentOptimizer(learning_rate=self.learning_rate)
			elif self.optimizer_type == 'MomentumOptimizer':
				optimizer = tf.train.MomentumOptimizer(learning_rate=self.learning_rate, momentum=0.95)

			# Create a variable to track steps
			global_step = tf.Variable(0, name='global_step', trainable=False)

			# Minimize
			self.optimizer = optimizer.minimize(self.loss, global_step=global_step)
=======
			# Optimizer.
			if self.optimizer_type == 'AdamOptimizer':
				self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate, beta1=0.9, beta2=0.999, epsilon=1e-8).minimize(self.loss)
			elif self.optimizer_type == 'AdagradOptimizer':
				self.optimizer = tf.train.AdagradOptimizer(learning_rate=self.learning_rate, initial_accumulator_value=1e-8).minimize(self.loss)
			elif self.optimizer_type == 'GradientDescentOptimizer':
				self.optimizer = tf.train.GradientDescentOptimizer(learning_rate=self.learning_rate).minimize(self.loss)
			elif self.optimizer_type == 'MomentumOptimizer':
				self.optimizer = tf.train.MomentumOptimizer(learning_rate=self.learning_rate, momentum=0.95).minimize(self.loss)
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282

			# init
			self.saver = tf.train.Saver()
			init = tf.global_variables_initializer()
			self.sess = self._init_session()
			self.sess.run(init)

<<<<<<< HEAD
			#=== Summary
			# Instantiate a SummaryWriter to output summaries and the Graph.
			self.summary_writer = tf.summary.FileWriter(self.save_file, self.sess.graph)

=======
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
			# number of params
			total_parameters = 0
			for variable in self.weights.values():
				shape = variable.get_shape() # shape is an array of tf.Dimension
				variable_parameters = 1
				for dim in shape:
					variable_parameters *= dim.value
				total_parameters += variable_parameters
			if self.verbose > 0:
<<<<<<< HEAD
				print("#params: %d" %total_parameters )
=======
				print "#params: %d" %total_parameters 
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
	
	def _init_session(self):
		# adaptively growing video memory
		config = tf.ConfigProto()
		config.gpu_options.allow_growth = True
		return tf.Session(config=config)

	def _initialize_weights(self):
		all_weights = dict()
		# if freeze_fm, set all other params untrainable
		trainable = self.freeze_fm == 0
		if self.pretrain_flag > 0 or self.micro_level_analysis:
			from_file = self.save_file
			if self.micro_level_analysis:
				from_file = self.save_file.replace('afm', 'fm')
			weight_saver = tf.train.import_meta_graph(from_file + '.meta')
			pretrain_graph = tf.get_default_graph()
			feature_embeddings = pretrain_graph.get_tensor_by_name('feature_embeddings:0')
			feature_bias = pretrain_graph.get_tensor_by_name('feature_bias:0')
			bias = pretrain_graph.get_tensor_by_name('bias:0')
			with self._init_session() as sess:
				weight_saver.restore(sess, from_file)
				fe, fb, b = sess.run([feature_embeddings, feature_bias, bias])
			# all_weights['feature_embeddings'] = tf.Variable(fe, dtype=tf.float32, name='feature_embeddings')
			all_weights['feature_embeddings'] = tf.Variable(fe, dtype=tf.float32, name='feature_embeddings', trainable=trainable)
			all_weights['feature_bias'] = tf.Variable(fb, dtype=tf.float32, name='feature_bias', trainable=trainable)
			all_weights['bias'] = tf.Variable(b, dtype=tf.float32, name='bias', trainable=trainable)
		else:
			all_weights['feature_embeddings'] = tf.Variable(
				tf.random_normal([self.features_p, self.factor_k[1]], 0.0, 0.01),
				name='feature_embeddings', trainable=trainable)  # features_p * K
			all_weights['feature_bias'] = tf.Variable(
				tf.random_uniform([self.features_p, 1], 0.0, 0.0), name='feature_bias', trainable=trainable)  # features_p * 1
			all_weights['bias'] = tf.Variable(tf.constant(0.0), name='bias', trainable=trainable)  # 1 * 1

		# attention
		if self.attention:
			glorot = np.sqrt(2.0 / (self.factor_k[0]+self.factor_k[1]))
			all_weights['attention_W'] = tf.Variable(
				np.random.normal(loc=0, scale=glorot, size=(self.factor_k[1], self.factor_k[0])), dtype=np.float32, name="attention_W")  # K * AK
			all_weights['attention_b'] = tf.Variable(
				np.random.normal(loc=0, scale=glorot, size=(1, self.factor_k[0])), dtype=np.float32, name="attention_b")  # 1 * AK
			all_weights['attention_p'] = tf.Variable(
				np.random.normal(loc=0, scale=1, size=(self.factor_k[0])), dtype=np.float32, name="attention_p") # AK

		# prediction layer
		all_weights['prediction'] = tf.Variable(np.ones((self.factor_k[1], 1), dtype=np.float32))  # factor_k * 1

		return all_weights

	def batch_norm_layer(self, x, train_phase, scope_bn):
		bn_train = batch_norm(x, decay=self.decay, center=True, scale=True, updates_collections=None,
			is_training=True, reuse=None, trainable=True, scope=scope_bn)
		bn_inference = batch_norm(x, decay=self.decay, center=True, scale=True, updates_collections=None,
			is_training=False, reuse=True, trainable=True, scope=scope_bn)
		z = tf.cond(train_phase, lambda: bn_train, lambda: bn_inference)
		return z

	def partial_fit(self, data):  # fit a batch
		feed_dict = {self.train_features: data['X'], self.train_labels: data['Y'], self.dropout_keep: self.keep, self.train_phase: True}
		loss, opt = self.sess.run((self.loss, self.optimizer), feed_dict=feed_dict)
		return loss

	def get_random_block_from_data(self, data, batch_size):  # generate a random block of training data
		start_index = np.random.randint(0, len(data['Y']) - batch_size)
		X , Y = [], []
		# forward get sample
		i = start_index
		while len(X) < batch_size and i < len(data['X']):
			if len(data['X'][i]) == len(data['X'][start_index]):
				Y.append([data['Y'][i]])
				X.append(data['X'][i])
				i = i + 1
			else:
				break
		# backward get sample
		i = start_index
		while len(X) < batch_size and i >= 0:
			if len(data['X'][i]) == len(data['X'][start_index]):
				Y.append([data['Y'][i]])
				X.append(data['X'][i])
				i = i - 1
			else:
				break
		return {'X': X, 'Y': Y}
	
	def get_ordered_block_from_data(self, data, batch_size, index):  # generate a ordered block of data
		start_index = index*batch_size
		X , Y = [], []
		# get sample
		i = start_index
		while len(X) < batch_size and i < len(data['X']):
			if len(data['X'][i]) == len(data['X'][start_index]):
				Y.append(data['Y'][i])
				X.append(data['X'][i])
				i = i + 1
			else:
				break
		return {'X': X, 'Y': Y}

	def shuffle_in_unison_scary(self, a, b): # shuffle two lists simutaneously
		rng_state = np.random.get_state()
		np.random.shuffle(a)
		np.random.set_state(rng_state)
		np.random.shuffle(b)

	def train(self, Train_data, Validation_data, Test_data):  # fit a dataset
		# Check Init performance
		if self.verbose > 0:
			t2 = time()
<<<<<<< HEAD
			init_train = self.evaluate(Train_data, data_type='train')
			init_valid = self.evaluate(Validation_data, data_type='valid')
			print("Init: \t train=%.4f, validation=%.4f [%.1f s]" %(init_train, init_valid, time()-t2))

		for epoch in range(self.epoch):
			t1 = time()
			self.shuffle_in_unison_scary(Train_data['X'], Train_data['Y'])
			total_batch = int(len(Train_data['Y']) / self.batch_size)
			for i in range(total_batch):
=======
			init_train = self.evaluate(Train_data)
			init_valid = self.evaluate(Validation_data)
			print("Init: \t train=%.4f, validation=%.4f [%.1f s]" %(init_train, init_valid, time()-t2))

		for epoch in xrange(self.epoch):
			t1 = time()
			self.shuffle_in_unison_scary(Train_data['X'], Train_data['Y'])
			total_batch = int(len(Train_data['Y']) / self.batch_size)
			for i in xrange(total_batch):
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
				# generate a batch
				batch_xs = self.get_random_block_from_data(Train_data, self.batch_size)
				# Fit training
				self.partial_fit(batch_xs)
			t2 = time()

			# evaluate training and validation datasets
<<<<<<< HEAD
			train_result = self.evaluate(Train_data, epoch, data_type='train')
			valid_result = self.evaluate(Validation_data, epoch, data_type='valid')
=======
			train_result = self.evaluate(Train_data)
			valid_result = self.evaluate(Validation_data)
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
			self.train_rmse.append(train_result)
			self.valid_rmse.append(valid_result)
			if self.verbose > 0 and epoch%self.verbose == 0:
				print("Epoch %d [%.1f s]\ttrain=%.4f, validation=%.4f [%.1f s]"
					  %(epoch+1, t2-t1, train_result, valid_result, time()-t2))

			# test_result = self.evaluate(Test_data)
			# print("Epoch %d [%.1f s]\ttest=%.4f [%.1f s]"
			#       %(epoch+1, t2-t1, test_result, time()-t2))
			if self.eva_termination(self.valid_rmse):
				break

		if self.pretrain_flag < 0 or self.pretrain_flag == 2:
<<<<<<< HEAD
			print("Save model to file as pretrain.")
=======
			print "Save model to file as pretrain."
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
			self.saver.save(self.sess, self.save_file)

	def eva_termination(self, valid):
		if len(valid) > 5:
			if valid[-1] > valid[-2] and valid[-2] > valid[-3] and valid[-3] > valid[-4] and valid[-4] > valid[-5]:
				return True
		return False

<<<<<<< HEAD
	def evaluate(self, data, epoch=None, data_type='train'):  # evaluate the results for an input set
=======
	def evaluate(self, data):  # evaluate the results for an input set
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
		num_example = len(data['Y'])
		# fetch the first batch
		batch_index = 0
		batch_xs = self.get_ordered_block_from_data(data, self.batch_size, batch_index)
		# batch_xs = data
		y_pred = None
<<<<<<< HEAD

=======
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
		# if len(batch_xs['X']) > 0:
		while len(batch_xs['X']) > 0:
			num_batch = len(batch_xs['Y'])
			feed_dict = {self.train_features: batch_xs['X'], self.train_labels: [[y] for y in batch_xs['Y']], self.dropout_keep: list(1.0 for i in range(len(self.keep))), self.train_phase: False}
			a_exp, a_sum, a_out, batch_out = self.sess.run((self.attention_exp, self.attention_sum, self.attention_out, self.out), feed_dict=feed_dict)
			
			if batch_index == 0:
				y_pred = np.reshape(batch_out, (num_batch,))
			else:
				y_pred = np.concatenate((y_pred, np.reshape(batch_out, (num_batch,))))
			# fetch the next batch
			batch_index += 1
			batch_xs = self.get_ordered_block_from_data(data, self.batch_size, batch_index)

		y_true = np.reshape(data['Y'], (num_example,))

<<<<<<< HEAD

		# Datatype
		if data_type == 'train':
			summary_type = self.summary_train
		elif data_type == 'valid':
			summary_type = self.summary_valid
		elif data_type == 'test':
			summary_type = self.summary_test

		# Update the events file.
		summary_str = self.sess.run(summary_type, feed_dict=feed_dict)
		self.summary_writer.add_summary(summary_str, epoch)
		self.summary_writer.flush()

=======
>>>>>>> 1ecd770dcfcc25c9907d36068910d9af197d9282
		predictions_bounded = np.maximum(y_pred, np.ones(num_example) * min(y_true))  # bound the lower values
		predictions_bounded = np.minimum(predictions_bounded, np.ones(num_example) * max(y_true))  # bound the higher values
		RMSE = math.sqrt(mean_squared_error(y_true, predictions_bounded))
		return RMSE

if __name__ == '__main__':
	pass