import spacy
from flask import Flask, flash, render_template, request, redirect
from PyPDF2 import PdfReader
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.matcher import Matcher

nlp = spacy.load('en_core_web_md')
skill_path = '../data/skills.jsonl'
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk(skill_path)

matcher = Matcher(nlp.vocab)
matcher.add("PERSON", [[{"POS": "PROPN", "OP": "{2}", "ENT_TYPE": "PERSON"}]], greedy="LONGEST")
matcher.add("EMAIL", [[{"LIKE_EMAIL": True}]], greedy="LONGEST")
matcher.add("URL", [[{"LIKE_URL": True}]], greedy="LONGEST")
matcher.add("PHONE NUMBER", [
    [{"ORTH": {"in": ["(", "["]}, "is_digit": True}, {"SHAPE": "dddd"}, {"ORTH": {"in": [")", "]"]}}, {"SHAPE": "dddd"}, {"SHAPE": "dddd"}],
    [{"ORTH": {"in": ["(", "["]}, "is_digit": True}, {"SHAPE": "ddd"}, {"ORTH": {"in": [")", "]"]}}, {"SHAPE": "ddd"}, {"SHAPE": "dddd"}],
    [{"SHAPE": "ddd"}, {"ORTH": "-"}, {"SHAPE": "ddd"}, {"ORTH": "-"}, {"SHAPE": "dddd"}],
    [{"SHAPE": "ddd"}, {"SHAPE": "ddd"}, {"SHAPE": "dddd"}],
])

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

    ent_types = ["SKILL", "ORG"]
    pattern_types = ["PERSON", "PHONE NUMBER", "EMAIL", "URL"]

    output = {
        'FILE': [],
        'PERSON': [],
        'PHONE NUMBER': [],
        'EMAIL': [],
        'URL': [],
        'SKILL': [],
        'ORG': []
    }
    
    for filename, resume in resumes:
        doc = nlp(resume)
        
        entities = {}

        # detect and capture patterns using matcher in resume text
        matches = matcher(doc)
        matches.sort(key = lambda x: x[1])

        for match in matches:
            pattern_type = nlp.vocab.strings[match[0]]
            if pattern_type in entities:
                entities[pattern_type].append(str(doc[match[1]:match[2]]))
            else:
                entities[pattern_type] = [str(doc[match[1]:match[2]])]

        # capture entities in resume text
        for ent in doc.ents:
            if ent.label_ in ent_types:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
                else:
                    entities[ent.label_] = [ent.text]

        for field in ent_types+pattern_types:
            try:
                output[field].append(', '.join(unique_list(entities[field])))
            except:
                output[field].append('-')

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