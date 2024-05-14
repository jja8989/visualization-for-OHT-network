from flask import Blueprint, jsonify, request, g, session
import pandas as pd
import json
from utils import *
import json

bp = Blueprint("func_bp", __name__); 

@bp.route('/docs/<string:col>')
def doc_names(col):

    docs = [doc for doc in g.db[col].find({}, {'_id' : 0, 'name' : 1})]
    return jsonify(docs)

@bp.route('/upload', methods=['POST'])
def upload():    
    if 'json' in request.form:
        name = request.form['json']
        query = {'name' : name}
        data = g.db['json'].find_one(query, {'_id': False})
        session['current_data'] = data

        return jsonify(data)
    

    elif 'json-file' in request.files: 
        file = request.files['json-file']
        name = file.filename
        data = json.load(file.stream) 
        doc = {'name' : name, 'data' : data}
        g.db['json'].update_one({'name': name}, {'$set': doc}, upsert=True) 
        doc.pop('_id', None)
        session['current_data'] = doc
        
        return jsonify(doc)
    
    structure = request.form.get('structure')
    
    data_dict = {
        'node': None,
        'link': None,
        'port': None,
        'flow' : None,
    }

    for d_type in ['node', 'link', 'port', 'flow']:
        if d_type in request.form:
            name = request.form[d_type]
            query = {'name' : name}
            result = g.db[d_type].find_one(query, {'_id': False})
            data_dict[d_type] = pd.read_json(result['data'], orient='records')
        
        elif f'{d_type}-file' in request.files:
            file = request.files[f'{d_type}-file']
            name = file.filename
            df = pd.read_csv(file) if d_type != 'flow' else pd.read_csv(file, names=['loading', 'destination'])
            data = df.to_json(orient='records')
            doc = {'name' : name, 'data' : data}
            g.db[d_type].update_one({'name': name}, {'$set': doc}, upsert=True)
            data_dict[d_type] = df
    
    node = data_dict['node']
    link = data_dict['link']
    port = data_dict['port']
    flow = data_dict['flow']
    save_name = request.form.get('save_name')
            
    if structure == 'flow':
        data = cal_flow(node, link, flow)
        doc = {'name' : save_name, 'data' : data, 'type' : 'flow'}
        g.db['json'].update_one({'name': save_name}, {'$set': doc}, upsert=True)
        doc.pop('_id', None)
        return jsonify(doc)

    if 'centrality' in request.form:
        centrality = request.form.get('centrality')
    else:
        centrality = 'layout'
    

    data = cal(node, link, port, centrality)
    
    doc = {'name' : save_name, 'data' : data, 'type' : centrality}
    g.db['json'].update_one({'name': save_name}, {'$set': doc}, upsert=True)
    doc.pop('_id', None)
    
    return jsonify(doc)