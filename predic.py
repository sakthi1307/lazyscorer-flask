from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers import SentenceTransformer
import tensorflow as tf
import tensorflow_hub as hub    

def cos_sim(sentence1_emb, sentence2_emb):
    """
    Cosine similarity between two columns of sentence embeddings
    
    Args:
      sentence1_emb: sentence1 embedding column
      sentence2_emb: sentence2 embedding columna
    
    Returns:
      The row-wise cosine similarity between the two columns.
      For instance is sentence1_emb=[a,b,c] and sentence2_emb=[x,y,z]
      Then the result is [cosine_similarity(a,x), cosine_similarity(b,y), cosine_similarity(c,z)]
    """
    cos_sim = cosine_similarity(sentence1_emb, sentence2_emb)
    return np.diag(cos_sim)

def cross_encoder(first,second):
    model = CrossEncoder('cross-encoder/stsb-roberta-base')
    scores = model.predict([first, second])  
    return scores

def univesal_sentence_encoder(first,second):
    # Load the pre-trained model
    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    module_url = 'https://tfhub.dev/google/universal-sentence-encoder/4'
    model = hub.load(module_url)
    
    # Generate Embeddings

    sentence1_emb = model([first]).numpy()
    sentence2_emb = model([second]).numpy()
    # Cosine Similarity
    score = cos_sim(sentence1_emb, sentence2_emb)
    return score[0]
    

def bi_encoder(first,second):
    model = SentenceTransformer('stsb-mpnet-base-v2')
    sentence1_emb = model.encode([first])
    sentence2_emb = model.encode([second])
    return(cos_sim(sentence1_emb, sentence2_emb)[0])
