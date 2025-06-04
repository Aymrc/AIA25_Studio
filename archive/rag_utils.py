import numpy as np
import json
from server.config import *

# This script is only used as a RAG tool for other scripts.

def get_embedding(text, model=embedding_model):
    text = text.replace("\n", " ")
    if mode == "openai":
        response = client.embeddings.create(input = [text], dimensions = 768, model=model)
    else:
        response = client.embeddings.create(input = [text], model=model)
    vector = response.data[0].embedding
    return vector

def similarity(v1, v2):
    return np.dot(v1, v2)

def load_embeddings(embeddings):
    with open(embeddings, 'r', encoding='utf8') as infile:
        return json.load(infile)
    
def get_vectors(question_vector, index_lib, n_results):
    scores = []
    for vector in index_lib:
        score = similarity(question_vector, vector['vector'])
        scores.append({'content': vector['content'], 'score': score})

    scores.sort(key=lambda x: x['score'], reverse=True)
    best_vectors = scores[0:n_results]
    return best_vectors

def rag_answer(question, prompt, model=completion_model):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", 
             "content": prompt
            },
            {"role": "user", 
             "content": question
            }
        ],
        temperature=0.1,
    )
    return completion.choices[0].message.content

def rag_call(question, embeddings, n_results):

    print("Initiating RAG...")
    # Embed our question
    question_vector = get_embedding(question)

    # Load the knowledge embeddings
    index_lib = load_embeddings(embeddings)

    # Retrieve the best vectors
    scored_vectors = get_vectors(question_vector, index_lib, n_results)
    scored_contents = [vector['content'] for vector in scored_vectors]
    rag_result = "\n".join(scored_contents)

    # Get answer from vector informed query
    prompt = f"""Answer the question based on the provided information. 
                You are given the extracted parts of a long document and a question. Provide a direct answer.
                If you don't know the answer, just say "I do not know." Don't make up an answer.
                PROVIDED INFORMATION: """ + rag_result
    
    # prompt = f"""Make a summary of the provided information. 
    #             You are given the extracted parts of a long document. 
    #             PROVIDED INFORMATION:  + {rag_result}
    #             SUMMARY: """

    answer = rag_answer(question, prompt)
    return answer
