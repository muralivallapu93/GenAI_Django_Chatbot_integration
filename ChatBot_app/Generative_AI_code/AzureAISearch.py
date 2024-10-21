from azure.storage.blob import (
    BlobServiceClient,
    generate_account_sas,
    ResourceTypes,
    AccountSasPermissions
)
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# llama_index packages
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.settings import Settings
from llama_index.core.memory import ChatMemoryBuffer, BaseMemory
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.prompts import BasePromptTemplate

# General packages
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from calereschatbot.settings import *

# Loading Env variables
current_path = os.path.abspath(__file__)
parent_path = os.path.abspath(os.path.join(current_path, '../../../'))
env_path = os.path.join(parent_path, '.env')

load_dotenv(dotenv_path=env_path)


# Fetching environment variables
AZURE_OPENAI_API_KEY1 = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_API_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_MODEL_NAME = os.getenv('AZURE_OPENAI_MODEL_NAME')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
AZURE_EMBEDDING_MODEL_NAME = os.getenv('AZURE_EMBEDDING_MODEL_NAME')
AZURE_EMBEDDING_DEPLOYMENT_NAME = os.getenv('AZURE_EMBEDDING_DEPLOYMENT_NAME')
AZURE_AISEARCH_SERVICE_API_KEY = os.getenv('AZURE_AISEARCH_SERVICE_API_KEY')
AZURE_AISEARCH_SERVICE_ENDPOINT = os.getenv('AZURE_AISEARCH_SERVICE_ENDPOINT')
AZURE_AISEARCH_INDEX_NAME = os.getenv('AZURE_AISEARCH_INDEX_NAME')
AZURE_BLOB_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_BLOB_STORAGE_ACCOUNT_NAME')
AZURE_BLOB_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_BLOB_STORAGE_ACCOUNT_KEY')
CHATNAME_SYSTEM_MESSAGE = os.getenv('CHATNAME_GEN_SYSTEM_MESSAGE')
CHATNAME_USER_MESSAGE = os.getenv('CHATNAME_GEN_USER_MESSAGE')

# llama_index chat initial setup
chat_store = SimpleChatStore()

llm = AzureOpenAI(
    model=AZURE_OPENAI_MODEL_NAME,
    deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_API_KEY1,
    azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
    temperature=0.3
)

embed_model = AzureOpenAIEmbedding(
    model=AZURE_EMBEDDING_MODEL_NAME,
    deployment_name=AZURE_EMBEDDING_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_API_KEY1,
    azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)

Settings.embed_model = embed_model
Settings.llm = llm

index = VectorStoreIndex.from_documents([])

reference_links = []

# Class AzureAI Search
class AzureAIResponse:
    def __init__(self, user_query):
        self.user_query = user_query

    def azure_retriever(self, user_query):
        search_client = SearchClient(
            endpoint=AZURE_AISEARCH_SERVICE_ENDPOINT,
            index_name=AZURE_AISEARCH_INDEX_NAME,
            credential=AzureKeyCredential(AZURE_AISEARCH_SERVICE_API_KEY)
        )
        chunks = search_client.search(search_text=self.user_query, query_type="semantic")

        sas_token = generate_account_sas(
            account_name=AZURE_BLOB_STORAGE_ACCOUNT_NAME,
            account_key=AZURE_BLOB_STORAGE_ACCOUNT_KEY,
            resource_types=ResourceTypes(object=True),
            permission=AccountSasPermissions(read=True),
            expiry=datetime.now(tz=timezone.utc) + timedelta(hours=1)
        )

        data = []
        global reference_links
        reference_links = []

        for chunk in chunks:
            score = chunk['@search.score']
            if score > 4:
                reference_links.append(chunk['metadata_storage_path'] + "?" + sas_token)
                data.append(chunk['chunk_content'])
        
        context_str = "\n\n".join(data)
        reference_links = list(set(reference_links))
        return context_str, chunks

    def llamachat_engine(self, chat_history):
        if len(chat_history) > 0:
            self.user_query = CondensePlusContextChatEngine.condense_question(chat_history, self.user_query)
        
        condense_engine = CondensePlusContextChatEngine(llm=llm, retriever=self.azure_retriever)
        memory = ChatMemoryBuffer.from_defaults(chat_history=chat_history, max_token_limit=3500)

        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            memory=memory,
            context_prompt=BasePromptTemplate.from_defaults(
                template="You are a chatbot who will assist the user in answering their queries based on the context provided to you. Always respond in a readable and beautiful format by always using HTML tags. Here is the relevant information for the context:\n\n{context_str}\n\nInstruction: Use only the previous chat history or the context above to interact and help."
            ),
            verbose=False,
            skip_condense=True
        )

        response = chat_engine.chat(self.user_query)
        responses = response.response
        return responses, reference_links
    # Function for Conversation name generation
    def chatNameGenerator(self, messages_list):
        messages_list.insert(0, {"role": "system", "content": CHATNAME_SYSTEM_MESSAGE})
        messages_list.append({"role": "user", "content": CHATNAME_USER_MESSAGE})

        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY1,
            azure_endpoint=AZURE_OPENAI_API_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME
        )

        response = client.chat.completions.create(
            model=AZURE_OPENAI_MODEL_NAME,
            messages=messages_list
        )

        conversationName = response.choices[0].message['content']

        # Removing double quotes from title
        if '"' in conversationName:
            conversationName = conversationName.replace('"', '')

        return conversationName
