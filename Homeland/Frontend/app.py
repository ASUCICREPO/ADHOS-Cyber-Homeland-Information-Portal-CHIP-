import streamlit as st
import requests as request
import json
from PIL import Image

# Add your own API Endpoints 
api_endpoint  = ""

api_email_send_endpoint = "" 

st.title('Cyber Homeland Information Portal (CHIP)')
prompt = st.text_input("")

if prompt:
    request_ = request.post( api_endpoint, json= {
        "prompt": prompt
    } )
    
    # formatting the response form api
    formatted_response = json.loads(request_.text)

    email_required = True

    # extracting answer from the api response 
    if formatted_response and 'answer' in formatted_response:
        answer = formatted_response['answer']
    else:
        answer =  "I dont Know"

    email_required = formatted_response['email_required']

    # displaying the answer produced
    st.write(answer)

    #if re.sub('\W+','', answer) != "Idontknow":
    if not email_required:

        st.write("Sources")

        # using streamlit expander to display source link and the aws kendra excerpt
        # extracting source link and the excerpt from aws Kendra
        if 'sources'  in formatted_response and len(formatted_response['sources']) > 0:
            for src in formatted_response['sources']:
                st.write("Source Link: " + src)

    else:
        st.write("**A member from the AZ DOHS Team will contact you regarding your question. Please provide your contact details below**")
        with st.form("details"):
            email = st.text_input("*Enter your Email", key ="email")
            submitted = st.form_submit_button("Submit")

            if submitted:
                resp = request.post( api_email_send_endpoint, json= {
                        "email": email,
                        "query": prompt
                        } )
                    
                data = json.loads(resp.text)

                if data['email_sent']:
                    st.write("Request sent Successfully")
                else:
                    st.write("Request sent failed. Please fill the required fields correctly")