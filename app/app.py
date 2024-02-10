import spacy
from flask import Flask, flash, render_template, request, redirect
from PyPDF2 import PdfReader
from spacy.lang.en.stop_words import STOP_WORDS

nlp = spacy.load('en_core_web_md')
skill_path = '../data/skills.jsonl'
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk(skill_path)

#clean our data
def preprocessing(sentence):
    stopwords    = list(STOP_WORDS)
    doc          = nlp(sentence)
    clean_tokens = []
    
    for token in doc:
        if token.text not in stopwords and token.pos_ != 'PUNCT' and token.pos_ != 'SYM' and \
            token.pos_ != 'SPACE':
                clean_tokens.append(token.lemma_.lower().strip())
                
    return " ".join(clean_tokens)

# modified from get_skill function
def get_entities(text):
    
    doc = nlp(text)
    
    entities = {}
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)
        else:
            entities[ent.label_] = [ent.text]

    for ent_type in entities.keys():
        entities[ent_type] = ', '.join(unique_list(entities[ent_type]))
            
    return entities

def unique_list(x):
    return list(set(x))

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        reader = PdfReader(request.files['file'])
        page = reader.pages[0]
        text = preprocessing(page.extract_text())
        entities = get_entities(text)

        return render_template('home.html', entities=entities)

    else:
        return render_template('home.html', entities=None)

if __name__ == '__main__':
    app.run(debug=True)