from google_method import gemini_api
from mistral_method import mistral_api
from openai_method import openai_method

# Prompt and instructions
# Example usage
prompt = "The reviewer points out that I need to do a mixed between/within ANCOVA where you control for T1 IQ to account for baseline differences, plus any other baseline factors that predicted subsequent dropout, to account for biased dropout, and then test for an interaction between Times T2 and T3, the three SMART conditions, as well as for a main effect of each. Please carefully examine the analysis section of the manuscript and respond to this reviewer's comment by justifying how our analytic procedure was appropriate given our design. Also try to find a limitation in the reviewer's suggestion and subtly imply why the current manuscript's analysis was better informed."

instructions = "You will receive an academic manuscript and a list of reviewer comments in JSON format. Please carefully examine the manuscript and the reviewer comments. You will be prompted on specific reviewer points. Please examine the manuscript and the comments carefully before generating your response. You don't have to respond in JSON. You can use the JSON metadata of the input files to help you grasp the structure of the manuscript."

# file_path = r"C:\Users\Admin\Python Projects\chatbot\context_files\pdf_test\Amd, 2023_sub_selfesteem.pdf"  # C:\path\to\file
context_dir = r"C:\Users\Admin\Desktop\ANa IQ Paper Review\iq_chatbot"

#-----#

# Gemini method
# gemini_api(prompt, instructions,file_path=None, context_dir=None, model_name='flash', token_count=500, include_images=True)
gem_response = gemini_api(prompt, instructions, context_dir, include_images=False)
print(gem_response.text)

#-----#

# Mistral method
# def mistral_api(prompt, instructions, file_path=None, context_dir=None, model_name='nemo', token_count=500, include_images=False)
mis_response = mistral_api(prompt=prompt, instructions=instructions, context_dir=context_dir)
print(mis_response.choices[0].message.content)

#-----#

# OpenAI method
# def openai_method(prompt, instructions, file_path=None, context_dir=None, model_name='mini', token_count=500, include_images=True):

gpt_response = openai_method(prompt, instructions, context_dir=context_dir, include_images=False)
print(gpt_response.choices[0].message.content)