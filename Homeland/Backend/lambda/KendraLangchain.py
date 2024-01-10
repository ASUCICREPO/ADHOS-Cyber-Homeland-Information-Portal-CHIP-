import json 
import os
from langchain.retrievers import AmazonKendraRetriever
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.llms.bedrock import Bedrock
import boto3
from botocore.exceptions import ClientError
from email_handler import send_email

kendra_index = os.environ['AWS_KENDRA']

sender_address = os.environ['SENDER_ADDRESS']

receiver_address = os.environ['RECEIVER_ADDRESS']

access_key_id = os.environ['ACCESS_KEY']

secret_access_key = os.environ['SECRET_ACCESS_KEY']

region = os.environ["AWS_REGION"]

bedrock_runtime = boto3.client(
        service_name = "bedrock-runtime",
        region_name = region,
        aws_access_key_id = access_key_id,
        aws_secret_access_key = secret_access_key
    )

# The function for creating a Retrieval documents chain using the RetrievalQA function from langchain framework
def create_chain(retriever_: AmazonKendraRetriever):

    Claude2 = Bedrock(
        model_id='anthropic.claude-v2',
        client=bedrock_runtime,
        model_kwargs={
        'temperature': 0}
    )

    retriever = retriever_
    
    print("RETREIVER")
    print(retriever)

    prompt_template = """
    The following is a formal conversation between a human and an AI. 
    The AI is provides required details from its context.
    If the AI does not know the answer to a question, it truthfully says it 
    does not know. 
    {context}.
    Instruction: Based on the above documents, provide a detailed answer for, {question} Answer "reach out to the support team" if not present in the document. Solution:
    """
    
    # referencing the prompt tempelate
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    # passing the prompt as a variable in the RetrievalQA function
    chain_type_kwargs = {"prompt": PROMPT}
    
    # returning the RetrievalQA chain with all the parameters
    return RetrievalQA.from_chain_type(
        Claude2, 
        chain_type="stuff", 
        retriever=retriever, 
        chain_type_kwargs=chain_type_kwargs, 
        return_source_documents=True
    )

# function for starting the chain 
def start_chain(chain, prompt: str):
    result = chain(prompt)
    print("RESULT")
    print(result)
    for i in result :
        print(i)
    return {
        "answer": result['result'],
        "source_documents": result['source_documents']
    }


def handler(event, context):
    print(event['path'])

    path =  event['path']
    
    if path == "/sendemail":
        req_body = json.loads(event['body'])
        recepient_email = req_body['email']
        recepient_query = req_body['query']

        resp = send_email(sender_address, receiver_address, region, recepient_email, recepient_query)
        
        print(resp)
        
        return resp
    else:

        print(json.dumps(event))
        
        body_ = json.loads(event['body'])
        
        print(body_)
        
        prompt_ = body_['prompt']
        
        print(prompt_)
        
        prompt_ = prompt_.lower()
        
        #Replace program word in the question to match the program name in the documents
        if "program" in prompt_:
            prompt_ = prompt_.replace("program", "program or State of Arizona FFY2022 State and Local Cyber Grant Program")
            
        print(prompt_)
            
        Aws_Retriever = AmazonKendraRetriever(index_id = kendra_index)
        
        chain = create_chain(Aws_Retriever)
        
        print(chain)
        
        result = start_chain(chain, prompt_)
        
        print(json.dumps(result['answer']))
        
        response = result['answer'].encode('ascii', 'replace').decode('ascii')
        
        print(response)

        #Flag to check whether the LLM answer is don't know or not    
        ans_flag = True
        
        dont_know_possibilities = [" I do not know, I don't know", "don't know", "do not know", "support team", "team"]
        
        # Flag to send email or not
        email_required = False
        
        if any(value in response for value in dont_know_possibilities):
            
            ans_flag = False
            #response = "I don't Know"
            email_required = True
        
        sources_doc_list = []

        if 'source_documents' in result and ans_flag == True:
            print('Sources:')
            for d in result['source_documents']:
                print(d)
                sources_doc_list.append(d.metadata['source'])
                print(d.metadata['source'])

        result = buildResponse(response, list(set(sources_doc_list)), email_required)
        
        print(result)
        
        return result


def buildResponse(resp, doc_list, email_required):
    
    return {
        "statusCode" : 200,
        "headers" : {
            'Access-Control-Allow-Origin' : '*',
            'Content-Type' : 'application/json'
        },
        "body" : json.dumps({
            "answer": resp,
            "sources": doc_list,
            "email_required": email_required
        })
    }
