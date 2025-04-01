import os
import openai
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from util.errors import InternalProcessingError, NotFoundError
from api.models import Assignment
import asyncio


DEFAULT_MODEL="gpt-4-turbo"
DEFAULT_FEEDBACK_PROMPT="You are an AI used to provide constructive feedback to students on their coding assignments.\
    Provide feedback on the following assignment regarding correctness, efficiency, code quality, documentation,\
    error handling, style/formatting.\n"
DEFAULT_TEMPERATURE=0.5
RETURN_SPEC="Response should be JSON in the form:\
            { 'insights': <updated insights for this student's coding behavior, focused on areas of improvement. Should be a series of consise bullets>,\
            'annotations': [{'pattern': <> , 'comment': <>}, ...]\
            }"

# Load environment variables
load_dotenv()

# Load encryption key for decrypting API key
SECRET_KEY = os.getenv("API_SECRET_KEY")
cipher = Fernet(SECRET_KEY)

def encrypt_api_key(api_key: str) -> str:
    """Encrypt the OpenAI API key before storing it in the database."""
    return cipher.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt the API key before using it."""
    return cipher.decrypt(encrypted_key.encode()).decode()


# TODO: Finish implementation
# def get_ai_feedback_settings(assignment_id):
#     """Retrieve AI feedback settings for a given assignment.
#     Returns None if assignment id not found"""
#     assignment = Assignment.query.filter_by(id=assignment_id).first()
    
#     if not assignment:
#         return None

#     return {
#         "ai_feedback_enabled": assignment.ai_feedback_enabled, # is feedback enabled?
#         "ai_feedback_prompt": assignment.ai_feedback_prompt or DEFAULT_FEEDBACK_PROMPT,
#         "ai_feedback_model": assignment.ai_feedback_model or DEFAULT_MODEL,
#         "ai_feedback_temperature": assignment.ai_feedback_temperature if assignment.ai_feedback_temperature is not None else DEFAULT_TEMPERATURE
#     }

# def ai_feedback_enabled(assignment_id):
#     """Return True/False based on if AI feedback is enabled for a given assignment.
#     Returns False if assignment not found."""
#     assignment = Assignment.query.filter_by(id=assignment_id).first()

#     if not assignment:
#         return False

#     return assignment.ai_feedback_enabled


# async def generate_feedback(student_code: str, assignment_desc: str, autograder_output: str, encrypted_api_key: str, ai_settings: dict):
#     """Asynchronously generate AI-based feedback for a student's assignment."""

#     if not encrypted_api_key:
#         return
    
#     api_key = decrypt_api_key(encrypted_api_key)
#     openai.api_key = api_key

#     prompt = ai_settings.get("ai_feedback_prompt") + RETURN_SPEC # return spec specifies how the data should be returned
#     if assignment_desc:
#         prompt+=f"Assignment Description:\n{assignment_desc}\n"
    
#     prompt+= "Student's Code:\n{student_code}\n"

#     if autograder_output:
#         prompt+=f"Autograder Output:\n{autograder_output}\n"

    
#     try:
#         response = await asyncio.to_thread(
#             openai.ChatCompletion.create,
#             model=ai_settings.get("ai_feedback_model", "gpt-4-turbo"),
#             messages=[{"role": "system", "content": prompt}],
#             temperature=ai_settings.get("ai_feedback_temperature"),
#             max_tokens=512
#         )
#         return response["choices"][0]["message"]["content"]
#     except openai.error.OpenAIError as e:
#         raise InternalProcessingError(f"OpenAI API error: {str(e)}")