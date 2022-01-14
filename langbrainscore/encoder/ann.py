from enum import unique
import typing
import IPython
import numpy as np
from langbrainscore.interface.encoder import _ANNEncoder
from collections import defaultdict
import string
import torch
import xarray as xr


## Functions (probably to migrate later on)

def flatten_activations(activations):
	"""
	Convert activations into dataframe format
	Input: dict, key = layer, item = 2D array of stimuli x units
	Output: pd dataframe, stimulus ID x MultiIndex (layer, unit)
	"""
	labels = []
	arr_flat = []
	for layer, arr in activations.items():
		arr = np.array(arr)  # for each layer
		arr_flat.append(arr)
		for i in range(arr.shape[1]):  # across units
			labels.append((layer, i))
	arr_flat = np.concatenate(arr_flat, axis=1)  # concatenated activations across layers
	df = pd.DataFrame(arr_flat)
	df.columns = pd.MultiIndex.from_tuples(labels)  # rows: stimuli, columns: units
	return df


def get_activations(model, tokenizer, stimuli, emb_method='last-tok',
					case='lower', punc='strip-all', punc_exceptions=[],
					norm=None, outlier_removal=None,
					verbose=True):
	"""
	Obtain activations from (HF) models.

	:param model: model object, HF
	:paral tokenizer: tokenizer object, HF
	:param stimuli: list/array, [to do, edit] containing strings
	:param emb_method: str, denoting how to obtain sentence embedding
	:param case: str, denoting which casing to use
	:param punc: str, denoting which operations to perform regarding punctuation
	:param punc_exceptions: list, denoting which punctuation to NOT strip if punc == 'strip-all'
	:param norm: str, denoting how to normalize the embeddings
	:param outlier_removel: str, denoting whether to remove 'outliers' from the embedding

	Returns dict with key = layer, item = 2D array of stimuli x units
	"""
	
	return states_sentences


def aggregate_layers(hidden_states, aggregation_args):
	"""[summary]

	Args:
		hidden_states (torch.Tensor): pytorch tensor of shape (batch_size, n_items, dims)
		aggregation_args (ANNEmbeddingConfig): an object specifying the method to use for aggregating
												representations across items within a layer

	Raises:
		NotImplementedError

	Returns:
		np.ndarray: the aggregated array
	"""
	method = aggregation_args.aggregation
	states_layers = defaultdict(list)
	for i in range(n_layer + 1):  # for each layer
		if method == 'last':
			state = hidden_states[i].squeeze()[-1, :]  # get last token
		elif method == 'mean':
			state = torch.mean(hidden_states[i].squeeze(), dim=0)  # mean over tokens
		elif method == 'median':
			state = torch.median(hidden_states[i].squeeze(), dim=0)  # median over tokens
		elif method == 'sum':
			state = torch.sum(hidden_states[i].squeeze(), dim=0)  # sum over tokens
		elif method == 'all' or method == None:
			state = hidden_states
		else:
			raise NotImplementedError('Sentence embedding method not implemented')
		
		states_layers[i].append(state.detach().numpy())
		
		return states_layers


class ANNEmbeddingConfig:
	def __init__(self, aggregation: typing.Union[str, None, typing.Callable] = 'last',
				 norm=None, outlier_removal=None) -> None:
		if type(aggregation) in (str, type(None)) and aggregation not in {'first', 'last', 'mean', 'median', 'all',
																		  None}:
			raise ValueError(f'aggregation type {aggregation} not supported')
		# else: it could be a Callable (user implementing their own aggregation method); we won't sanity-check that here
		self.aggregation = aggregation
		self.norm = norm
		self.outlier_removal = outlier_removal


class HuggingFaceEncoder(_ANNEncoder):
	_pretrained_model_name_or_path = None
	
	def __init__(self, pretrained_model_name_or_path) -> None:
		# super().__init__(self)
		self._pretrained_model_name_or_path = pretrained_model_name_or_path
		
		from transformers import AutoModel, AutoConfig, AutoTokenizer
		self.config = AutoConfig.from_pretrained(self._pretrained_model_name_or_path)
		self.tokenizer = AutoTokenizer.from_pretrained(self._pretrained_model_name_or_path)
		self.model = AutoModel.from_pretrained(self._pretrained_model_name_or_path, config=self.config)
	
	def encode(self, dataset: 'langbrainscore.dataset.DataSet',
			   word_level_args: ANNEmbeddingConfig = ANNEmbeddingConfig(aggregation='last'),
			   sentence_level_args: ANNEmbeddingConfig = ANNEmbeddingConfig(aggregation='last'),
			   case: str = 'lower', punct: typing.Union[str, None, typing.List[str]] = None,
			   context_dimension: str = None, bidirectional: bool = False):
		"""[summary]

		Args:
			dataset (langbrainscore.dataset.DataSet): [description]
			word_level_args (ANNEmbeddingConfig, optional): [description]. Defaults to ANNEmbeddingConfig(aggregation='last').
			sentence_level_args (ANNEmbeddingConfig, optional): [description]. Defaults to ANNEmbeddingConfig(aggregation='last').
			case (str, optional): [description]. Defaults to 'lower'.
			punct (typing.Union[str, None, typing.List[str]], optional): [description]. Defaults to None.
			context_dimension (str, optional): the name of a dimension in our xarray-like dataset objcet that provides
												groupings of sampleids (stimuli) that should be used
												as context when generating encoder representations. for instance, in a word-by-word
												presentation paradigm we (may) still want the full sentence as context. [default: None].
			bidirectional (bool, optional): if True, allows using "future" context to generate the representation for a current token
											otherwise, only uses what occurs in the "past". some might say, setting this to False
											gives you a more biologically plausibly analysis downstream (: [default: False]

		Raises:
			NotImplementedError: [description]
			ValueError: [description]

		Returns:
			[type]: [description]
		"""
		self.model.eval()
		n_layer = self.model.config.n_layer
		states_sentences = defaultdict(list)
		
		stimuli = dataset.stimuli.values
		if context_dimension is None:
			context_groups = np.arange(0, len(stimuli), 1)
		else:
			context_groups = dataset.stimuli.coords[context_dimension].values
		
		for group in np.unique(context_groups):
			mask_context = context_groups == group
			stimuli_in_context = stimuli[mask_context]  # mask based on the context group
			
			# we want to tokenize all stimuli of this ctxt group individually first in order to keep track of
			# which tokenized subunit belongs to what stimulus
			
			tokenized_lengths = [0]
			word_ids_by_stim = []  # contains a list of token->word_id lists per stimulus
			states_sentences_across_stimuli = []
			for i, stimulus in enumerate(stimuli_in_context):
				print(f'encoding stimulus {i} of {len(stimuli_in_context)}')
				# mask based on the uni/bi-directional nature of models :)
				if not bidirectional:
					stimuli_directional = stimuli_in_context[:i + 1]
				else:
					stimuli_directional = stimuli_in_context
				
				stimuli_directional = ' '.join(stimuli_directional)
				
				if case == 'lower':
					stimuli_directional = stimuli_directional.lower()
				elif case == 'upper':
					stimuli_directional = stimuli_directional.upper()
				else:
					stimuli_directional = stimuli_directional
				
				# tokenize the stimuli
				tokenized_stim = self.tokenizer(stimuli_directional, padding=False, return_tensors='pt')
				tokenized_lengths += [tokenized_stim.input_ids.shape[1]]
				
				# Get the hidden states
				result_model = self.model(tokenized_stim.input_ids, output_hidden_states=True, return_dict=True)
				hidden_states = result_model[
					'hidden_states']  # dict with key=layer, value=3D tensor of dims: [batch, tokens, emb size]
				
				word_ids = tokenized_stim.word_ids()  # make sure this is positional, not based on word identity
				word_ids_by_stim += [
					word_ids]  # contains the ids for each tokenized words in stimulus todo: maybe get rid of this?
				
				# now cut the 'irrelevant' context from the hidden states
				for idx_layer, layer in enumerate(hidden_states):
					states_sentences[idx_layer] = layer[:, tokenized_lengths[-2]: tokenized_lengths[-1],
												  :].squeeze()  # to obtain [tokens;emb dim]
				
				# aggregate within  a stimulus
				states_sentences_agg = aggregate_layers(states_sentences,
														aggregation_args=sentence_level_args)  # fix todo to aggregation args,
				# dict with key=layer, value=array of # size [emb dim]
				
				states_sentences_across_stimuli.append(states_sentences_agg)
			# now we have all the hidden states for the current context group across all stimuli,
			emb_dim = states_sentences_across_stimuli[0][0].shape[-1]
			
			# flatten across layers and package as xarray
			# generate xarray DataSet
			xr_dataset = xr.DataArray(
				recorded_data,
				dims=("sampleid", "neuroid", "timeid"),
				coords={
					"sampleid": dataset.sampleid.values,
					"neuroid": np.arange(np.sum(len(states_sentences_agg[x] for x in states_sentences_agg))),  # check
					"timeid": np.arange(),
					"stimuli": ("sampleid", stimuli),
					"sent_identifier": ("sampleid", [f'mycorpus.{i:0>5}' for i in range(num_stimuli)]),
					"experiment": ("sampleid", experiment),
					"passage": ("sampleid", passage),
					"subject": ("neuroid", recording_metadata["subj_id"]),
					"roi": ("neuroid", recording_metadata["roi"]),
				},
			).to_dataset(name="data")


class PTEncoder(_ANNEncoder):
	def __init__(self, ptid) -> None:
		super().__init__(self)
		self._ptid = ptid
	
	def encode(self, dataset: 'langbrainscore.dataset.DataSet') -> None:
		pass
