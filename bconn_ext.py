# -*- coding: utf-8 -*-
"""bconn_ext.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B88-4BPQ32fj34ZZyg1l7u6wlYOSf9SX
"""

pip install sklearn-crfsuite

import xml.etree.ElementTree as ET

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    sentences = []

    for doc in root.findall('.//document'):
        for sent in doc.findall('.//sentence'):
            sent_text = sent.get('text')
            entities = {entity.get('id'): entity.get('text') for entity in sent.findall('.//entity')}

            # Tokenize the sentence text here as per your requirement
            tokens = sent_text.split()  # This is a simplistic tokenizer

            # Create a list of (word, label) tuples
            labeled_tokens = []
            for token in tokens:
                label = 'O'  # Default label
                for entity_id, entity_text in entities.items():
                    if entity_text in token:
                        label = 'B-Individual_protein'  # Replace with actual entity type
                        break
                labeled_tokens.append((token, label))

            sentences.append(labeled_tokens)

    return sentences

file_path = '/content/WhiteTextNegFixFull.xml'  # Replace with your XML file path
sentences = parse_xml(file_path)

import sklearn_crfsuite
from sklearn_crfsuite import metrics

def word2features(sent, i):
    word = sent[i][0]
    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
    }
    if i > 0:
        word1 = sent[i-1][0]
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
        })
    else:
        features['BOS'] = True

    if i < len(sent)-1:
        word1 = sent[i+1][0]
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
        })
    else:
        features['EOS'] = True

    return features

def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]

def sent2labels(sent):
    return [label for token, label in sent]

# Example: Load your data here

# Split data into training and test sets (customize this according to your data)
train_sents = sentences[:int(len(sentences) * 0.8)]
test_sents = sentences[int(len(sentences) * 0.8):]

X_train = [sent2features(s) for s in train_sents]
y_train = [sent2labels(s) for s in train_sents]

X_test = [sent2features(s) for s in test_sents]
y_test = [sent2labels(s) for s in test_sents]

# Train the CRF model
crf = sklearn_crfsuite.CRF(
    algorithm='lbfgs',
    c1=0.1,
    c2=0.1,
    max_iterations=100,
    all_possible_transitions=True
)
crf.fit(X_train, y_train)

# Make predictions
y_pred = crf.predict(X_test)

# Evaluate the model
print(metrics.flat_accuracy_score(y_test, y_pred))

new_file_path = '/content/WhiteTextUnseenEval.xml'
new_sentences = parse_xml(new_file_path)

X_new = [sent2features(s) for s in new_sentences]

new_predictions = crf.predict(X_new)

# Iterate over all sentences and their predictions
for sentence, predicted_labels in zip(new_sentences, new_predictions):
    for word, prediction in zip(sentence, predicted_labels):
        print(f"{word[0]}: {prediction}")
    print("\n--- End of Sentence ---\n")

with open("predicted_results.txt", "w") as file:
    for sentence, predicted_labels in zip(new_sentences, new_predictions):
        for word, prediction in zip(sentence, predicted_labels):
            file.write(f"{word[0]}: {prediction}\n")
        file.write("\n--- End of Sentence ---\n\n")