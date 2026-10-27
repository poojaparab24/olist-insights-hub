import os
import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
import time

st.set_page_config(page_title='Olist Insights Hub', page_icon='🛒', layout='wide')
st.title('🛒 E-Commerce Insights Hub')
st.caption('Ask questions in English about orders, customers, delivery and review sentiment.')

SPACE_ID = os.environ['GENIE_SPACE_ID']
w = WorkspaceClient()

SUGGESTED = [
    'What are the top 10 product categories by revenue?',
    'Show average sentiment stars by month',
    'Compare average order value by customer tier',
    'Which categories have the most negative reviews?',
    'Do late deliveries get lower review scores? Show by state',
]

if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.conversation_id = None

def wait_for_message(conv_id, msg_id, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        m = w.genie.get_message(SPACE_ID, conv_id, msg_id)
        status = str(m.status)
        if 'COMPLETED' in status:
            return m
        if 'FAILED' in status or 'CANCELLED' in status:
            raise RuntimeError(f'Genie {status}. Details: {m.error}')
        time.sleep(2)
    raise TimeoutError('Genie took too long to answer')

def fetch_result(conv_id, msg_id, attachment_id):
    g = w.genie
    for name in ('get_message_attachment_query_result',
                 'get_message_query_result_by_attachment'):
        f = getattr(g, name, None)
        if f:
            return f(SPACE_ID, conv_id, msg_id, attachment_id)
    f = getattr(g, 'get_message_query_result', None)
    if f:
        return f(SPACE_ID, conv_id, msg_id)
    methods = [m for m in dir(g) if not m.startswith('_')]
    raise AttributeError(f'No result method found. Available: {methods}')

def ask_genie(question):
    if st.session_state.conversation_id is None:
        wait = w.genie.start_conversation(SPACE_ID, question)
    else:
        wait = w.genie.create_message(
            SPACE_ID, st.session_state.conversation_id, question)
    r = wait.response
    conv_id = getattr(r, 'conversation_id', None) or st.session_state.conversation_id
    msg_id = r.message_id
    st.session_state.conversation_id = conv_id
    msg = wait_for_message(conv_id, msg_id)

    out = {'text': None, 'sql': None, 'df': None}
    for att in (msg.attachments or []):
        if att.text:
            out['text'] = att.text.content
        if att.query:
            out['sql'] = att.query.query
            out['text'] = out['text'] or att.query.description
            res = fetch_result(conv_id, msg_id, att.attachment_id)
            cols = [c.name for c in res.statement_response.manifest.schema.columns]
            rows = res.statement_response.result.data_array or []
            df = pd.DataFrame(rows, columns=cols)
            for c in df.columns:
                try:
                    df[c] = pd.to_numeric(df[c])
                except (ValueError, TypeError):
                    pass
            out['df'] = df
    return out

with st.sidebar:
    st.subheader('Try asking')
    for q in SUGGESTED:
        if st.button(q):
            st.session_state.pending = q
            st.session_state.conversation_id = None
    if st.button('New conversation'):
        st.session_state.messages = []
        st.session_state.conversation_id = None

for m in st.session_state.messages:
    with st.chat_message(m['role']):
        st.write(m.get('text') or '')
        if m.get('df') is not None:
            st.dataframe(m['df'], use_container_width=True)
        if m.get('sql'):
            with st.expander('View SQL'):
                st.code(m['sql'], language='sql')

prompt = st.chat_input('Ask a question about the data...') or st.session_state.pop('pending', None)
if prompt:
    st.session_state.messages.append({'role': 'user', 'text': prompt})
    with st.spinner('Genie is thinking...'):
        try:
            ans = ask_genie(prompt)
        except Exception as e:
            ans = {'text': f'Something went wrong: {e}', 'sql': None, 'df': None}
    st.session_state.messages.append({'role': 'assistant', **ans})
    st.rerun()