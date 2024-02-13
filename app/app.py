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

def unique_list(x):
    return list(set(x))

# modified from get_skill function
def get_entities(resumes):

    ent_types = ['PERSON', 'SKILL', 'PRODUCT', 'ORG']

    output = {
        'FILE': [],
        'PERSON': [],
        'SKILL': [],
        'PRODUCT': [],
        'ORG': []
    }
    
    for filename, resume in resumes:
        doc = nlp(resume)
        
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ in ent_types:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
                else:
                    entities[ent.label_] = [ent.text]

        for ent_type in ent_types:
            try:
                output[ent_type].append(', '.join(unique_list(entities[ent_type])))
            except:
                output[ent_type].append('-')

        output['FILE'].append(filename)

    return output

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        # Get the list of files from webpage 
        files = request.files.getlist("file")
        resumes = []

        for file in files:
            reader = PdfReader(file)
            page = reader.pages[0]
            resume = preprocessing(page.extract_text())
            resumes.append((file.filename, resume))

        print(resumes)
        output = get_entities(resumes)

        return render_template('home.html', output=output)

    else:
        return render_template('home.html', output=None)

if __name__ == '__main__':
    app.run(debug=True)