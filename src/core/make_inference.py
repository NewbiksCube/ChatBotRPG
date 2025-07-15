import random
import requests
import json
from config import get_api_key_for_service, get_base_url_for_service, get_current_service, get_default_utility_model

try:
    from google import genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

def _convert_model_name_for_google(model_name):
    if model_name.startswith("google/"):
        return model_name[7:]
    return model_name

def _internal_summarize_chunk(text_chunk, instruction, original_user_message_for_context):
    summary_prompt_for_llm = f"{instruction}\n\nTEXT TO SUMMARIZE:\n{text_chunk}"
    max_summary_tokens = 1536
    summary = make_inference(
        context=[{"role": "user", "content": summary_prompt_for_llm}],
        user_message=original_user_message_for_context,
        character_name=None,
        url_type=get_default_utility_model(),
        max_tokens=max_summary_tokens,
        temperature=0.3,
        is_utility_call=True,
        allow_summarization_retry=False
    )
    if summary and "Sorry, API error" in summary:
        return f"[Error during summarization: {summary[:100]}]"
    elif not summary:
        return "[Summarization failed to produce content]"
    return summary

def _make_google_genai_request(context, model_name, max_tokens, temperature, api_key):
    if not GOOGLE_GENAI_AVAILABLE:
        return "Sorry, API error: google-genai package not installed. Please install it with 'pip install google-genai'"
    
    try:
        client = genai.Client(api_key=api_key)
        
        formatted_messages = []
        for msg in context:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                formatted_messages.append(genai.types.Content(role='user', parts=[genai.types.Part(text=f"[SYSTEM] {content}")]))
            elif role == 'user':
                formatted_messages.append(genai.types.Content(role='user', parts=[genai.types.Part(text=content)]))
            elif role == 'assistant':
                formatted_messages.append(genai.types.Content(role='model', parts=[genai.types.Part(text=content)]))
        
        converted_model_name = _convert_model_name_for_google(model_name)
        
        config = genai.types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95
        )
        
        response = client.models.generate_content(
            model=converted_model_name,
            contents=formatted_messages,
            config=config
        )
        
        if response and response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text
        
        return ""
    
    except Exception as e:
        return f"Sorry, API error: Google GenAI request failed - {str(e)}"

def make_inference(context, user_message, character_name, url_type, max_tokens, temperature, seed=None, is_utility_call=False, allow_summarization_retry=True):
    if seed is not None:
        random.seed(seed); seed = random.randint(-1, 100000)
    current_service = get_current_service()
    api_key = get_api_key_for_service()
    
    if not api_key and current_service != "local":
        service_names = {"openrouter": "OpenRouter", "google": "Google GenAI"}
        service_name = service_names.get(current_service, current_service.title())
        return f"Sorry, API error: {service_name} API key not configured. Please check config.json file."
    
    if current_service == "google":
        return _make_google_genai_request(context, url_type, max_tokens, temperature, api_key)
    
    base_url = get_base_url_for_service()
    if base_url.endswith('/'):
        base_url = base_url.rstrip('/')
    base_url = f"{base_url}/chat/completions"
    
    final_data = { "model": url_type, "temperature": temperature, "max_tokens": max_tokens, "top_p": 0.95, "messages": context }
    headers = { "Content-Type": "application/json" }
    
    if current_service == "openrouter":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = "https://github.com/your-repo/your-project"
        headers["X-Title"] = "ChatBot RPG"
    elif current_service == "local":
        if api_key and api_key != "local":
            headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        final_response = requests.post(base_url, headers=headers, json=final_data, timeout=180)
        final_response.raise_for_status()
        final_response_data = final_response.json()
    except requests.exceptions.Timeout:
        error_msg = "Sorry, the request timed out."
        print(f"\n=== API Error ===\n{error_msg}")
        return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"API Request failed: {e}"
        print(f"\n=== API Error ===\n{error_msg}")
        error_details = "No specific error details available."
        status_code = None
        if e.response is not None:
            try:
                error_data = e.response.json()
                error_details = error_data.get("error", {}).get("message", json.dumps(error_data))
            except: pass
            status_code = e.response.status_code
            if allow_summarization_retry and "maximum context length" in error_details.lower() and not final_data.get("_summarization_attempted", False):
                final_data["_summarization_attempted"] = True
                original_messages = final_data["messages"]
                leading_setup_messages = []
                trailing_system_messages = []
                conversational_history_messages = []
                first_assistant_idx = -1
                last_assistant_idx = -1
                for i, msg in enumerate(original_messages):
                    if msg.get('role') == 'assistant':
                        if first_assistant_idx == -1:
                            first_assistant_idx = i
                        last_assistant_idx = i
                if first_assistant_idx == -1:
                    is_final_system_instruction = False
                    for i, msg in enumerate(original_messages):
                        if msg.get('role') == 'system' and \
                           ("your turn" in msg.get('content','').lower() or \
                            "what does" in msg.get('content','').lower() or \
                            "you are playing as" in msg.get('content','').lower()):
                            is_final_system_instruction = True
                        if is_final_system_instruction:
                            trailing_system_messages.append(msg)
                        else:
                            if msg.get('role') != 'system':
                                conversational_history_messages.append(msg)
                            else:
                                leading_setup_messages.append(msg)
                    if not conversational_history_messages and original_messages and original_messages[-1].get('role') == 'user':
                        if len(original_messages) > 1:
                           leading_setup_messages = [m for m in original_messages[:-1] if m.get('role') == 'system']
                           conversational_history_messages.extend([m for m in original_messages[:-1] if m.get('role') != 'system'])
                        conversational_history_messages.append(original_messages[-1])
                        trailing_system_messages = []
                else:
                    for i, msg in enumerate(original_messages):
                        if i < first_assistant_idx:
                            leading_setup_messages.append(msg)
                        elif i > last_assistant_idx and msg.get('role') == 'system':
                            trailing_system_messages.append(msg)
                        else:
                            conversational_history_messages.append(msg)
                original_conversational_text = ""
                for msg in conversational_history_messages:
                    original_conversational_text += f"{msg.get('role', 'unknown')}: {msg.get('content', '')}\n"
                else:
                    mid_point = len(original_conversational_text) // 2
                    first_half_text = original_conversational_text[:mid_point]
                    second_half_text = original_conversational_text[mid_point:]
                    summary1_instruction = (
                        "You are a highly skilled text summarizer. Your task is to create a concise yet detailed summary "
                        "of the following first part of a conversation. Focus on extracting and preserving all key events, "
                        "character actions, important dialogue, and significant emotional shifts. The summary must be a "
                        "factual representation of the provided text. Do not add new information or continue the conversation. "
                        "Output only the summary."
                    )
                    summary1 = _internal_summarize_chunk(first_half_text, summary1_instruction, user_message)
                    summary2_instruction = (
                        f"You are a highly skilled text summarizer. The first part of the conversation was summarized as: {summary1}\n\n"
                        f"Now, your task is to create a concise yet detailed summary of the following second part of the conversation. "
                        f"Focus on extracting and preserving all key events, character actions, important dialogue, and significant "
                        f"emotional shifts from this second part. The summary must be a factual representation of the provided text. "
                        f"Do not add new information or continue the conversation from the perspective of any character. "
                        f"Output only the summary of the second part."
                    )
                    summary2 = _internal_summarize_chunk(second_half_text, summary2_instruction, user_message)
                    if "[Error during summarization" in summary1 or "[Summarization failed" in summary1 or \
                       "[Error during summarization" in summary2 or "[Summarization failed" in summary2:
                        print("[ERROR] Critical failure during internal summarization process. Aborting retry.")
                        return f"Sorry, API error ({status_code}): {error_details} (Summarization attempt also failed.)"
                    full_conversation_summary = f"{summary1}\n\n{summary2}"
                    new_messages_for_retry = []
                    new_messages_for_retry.extend(leading_setup_messages)
                    new_messages_for_retry.append({"role": "user", "content": (
                        f"The historical user/assistant conversation has been summarized due to length constraints as follows:\n\n"
                        f"{full_conversation_summary}\n\n"
                        f"Please use this summarized history, along with all preceding setup instructions and any "
                        f"following turn-specific instructions, to formulate your response."
                    )})
                    if character_name and character_name != "Narrator":
                        character_prompt = f"(You are playing as: {character_name}. It is now {character_name}'s turn. You must respond in character as {character_name}'s next turn in the chat-based roleplay that was summarized before. Play only as the provided character and only for one turn. We are not continuing the summary, we are continuing the roleplay chat. What does {character_name} do or say next?)"
                        new_messages_for_retry.append({"role": "user", "content": character_prompt})
                    new_messages_for_retry.extend(trailing_system_messages)
                    final_data["messages"] = new_messages_for_retry
                    try:
                        final_response = requests.post(base_url, headers=headers, json=final_data, timeout=180)
                        final_response.raise_for_status()
                        final_response_data = final_response.json()
                        if final_response_data.get("choices") and final_response_data["choices"][0].get("message"):
                            final_message = final_response_data["choices"][0]["message"]["content"]
                            if not is_utility_call: print(f"\n=== Final Message (after retry) ===\nAssistant response: {final_message}")
                            return final_message
                        return "" 
                    except Exception as retry_e:
                        print(f"\n[ERROR] Summarized retry failed: {retry_e}")
            return f"Sorry, API error ({status_code}): {error_details}"
        else:
            return f"Sorry, there was an issue processing your request: {e}"
    except Exception as e:
        error_msg = f"An unexpected error occurred during API call: {e}"
    final_message = ""
    if final_response_data.get("choices") and final_response_data["choices"][0].get("message"):
        final_message = final_response_data["choices"][0]["message"]["content"]
    return final_message
