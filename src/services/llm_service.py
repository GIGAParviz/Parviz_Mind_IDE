from PyQt6.QtCore import QThread, pyqtSignal
import re
import os

class AIModelWorker(QThread):
    response_ready = pyqtSignal(str)
    code_suggestion = pyqtSignal(str, str)
    file_changes = pyqtSignal(dict, str)
    
    def __init__(self, query, code_context="", model_settings=None, additional_files=None):
        super().__init__()
        self.query = query
        self.code_context = code_context
        self.additional_files = additional_files or {}
        self.model_settings = model_settings or {
            "use_groq": True,
            "groq_model": "deepseek-r1-distill-llama-70b",
            "groq_api_key": "",
            "use_local": False,
            "local_model": "deepseek-r1:8b"
        }
        
    def run(self):
        try:
            if self.model_settings["use_groq"]:
                self.use_groq_model()
            else:
                self.use_local_model()
                
        except Exception as e:
            print(f"Error in AIModelWorker: {str(e)}")
            self.response_ready.emit(f"Error: {str(e)}")
            
    def use_groq_model(self):
        try:
            from langchain_groq import ChatGroq
            from langchain.schema.messages import HumanMessage, SystemMessage
            
            api_key = self.model_settings["groq_api_key"]
            if not api_key:
                api_key = "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"
                
            if not api_key or len(api_key) < 10:
                self.response_ready.emit("Error: Invalid API key")
                return
            
            model_name = self.model_settings["groq_model"]
                
            try:
                model = ChatGroq(
                    api_key=api_key, 
                    model_name=model_name
                )
            except Exception as e:
                self.response_ready.emit(f"Error initializing model: {str(e)}")
                return
            
            messages = []
            system_message = """You are a helpful AI programming assistant. When asked to improve or modify code:
                            1. Always provide a clear explanation of the changes
                            2. Present the complete modified code in a Python code block (```python)
                            3. Explain the benefits of the changes
                            4. If multiple files are involved, use filename code blocks like ```filename.py```followed by the content to specify changes to different files
                            """
            messages.append(SystemMessage(content=system_message))
            
            prompt = self._build_prompt()
            messages.append(HumanMessage(content=prompt))
            
            try:
                print(f"Sending query to Groq model: {model_name}")
                response = model.invoke(messages)
                result = response.content if hasattr(response, 'content') else str(response)
                
                self.process_response(result)
                    
            except Exception as e:
                print(f"Error processing model response: {str(e)}")
                self.response_ready.emit(f"Error getting response from model: {str(e)}")
        except Exception as e:
            print(f"Error in use_groq_model: {str(e)}")
            self.response_ready.emit(f"Error: {str(e)}")
    
    def use_local_model(self):
        try:
            from langchain_ollama import ChatOllama
            from langchain.schema.messages import HumanMessage, SystemMessage
            
            model_name = self.model_settings["local_model"]
                
            try:
                model = ChatOllama(model=model_name)
            except Exception as e:
                self.response_ready.emit(f"Error initializing local model: {str(e)}")
                return
            
            messages = []
            system_message = """You are a helpful AI programming assistant. When asked to improve or modify code:
                            1. Always provide a clear explanation of the changes
                            2. Present the complete modified code in a Python code block (```python)
                            3. Explain the benefits of the changes
                            4. If multiple files are involved, use filename code blocks like ```filename.py```followed by the content to specify changes to different files
                            """
            messages.append(SystemMessage(content=system_message))
            
            prompt = self._build_prompt()                
            messages.append(HumanMessage(content=prompt))
            
            try:
                print(f"Sending query to local Ollama model: {model_name}")
                response = model.invoke(messages)
                result = response.content if hasattr(response, 'content') else str(response)
                
                self.process_response(result)
                    
            except Exception as e:
                print(f"Error processing local model response: {str(e)}")
                self.response_ready.emit(f"Error getting response from local model: {str(e)}")
        except Exception as e:
            print(f"Error in use_local_model: {str(e)}")
            self.response_ready.emit(f"Error: {str(e)}")
    
    def _build_prompt(self):
        prompt = ""
        
        if self.code_context:
            prompt += f"Here's my main code:\n```python\n{self.code_context}\n```\n\n"
        
        if self.additional_files:
            prompt += "Here are additional files in the project:\n\n"
            for file_path, content in self.additional_files.items():
                file_name = os.path.basename(file_path)
                prompt += f"File: {file_path}\n```python\n{content}\n```\n\n"
        
        prompt += f"My question: {self.query}"
        
        return prompt
    
    def process_response(self, result):
        """Process the response from any model"""
        # First, try to find filename.py style code blocks 
        # Look for patterns like ```filename.py ... ``` or ```python filename.py ... ```
        file_blocks_standard = re.findall(r'```([^\s]+\.py)\s*\n(.*?)```', result, re.DOTALL)
        file_blocks_with_python = re.findall(r'```python\s+([^\s]+\.py)\s*\n(.*?)```', result, re.DOTALL)
        
        # Also look for other common formats like markdown file indicators
        file_blocks_markdown = re.findall(r'#+\s*src\/([^\s]+\.py).*?```(?:python)?\s*\n(.*?)```', result, re.DOTALL)
        file_blocks_txt = re.findall(r'#+\s*([^\s]+\.txt).*?```(?:text)?\s*\n(.*?)```', result, re.DOTALL)
        
        # Combine all found file blocks
        all_file_blocks = file_blocks_standard + file_blocks_with_python
        
        # Add markdown style file blocks with proper path formatting
        for file_path, content in file_blocks_markdown:
            all_file_blocks.append((file_path, content))
            
        # Add text file blocks
        for file_path, content in file_blocks_txt:
            all_file_blocks.append((file_path, content))
        
        if all_file_blocks and len(all_file_blocks) >= 1:
            file_changes = {}
            for file_name, content in all_file_blocks:
                # Clean up the filename by removing any problematic characters
                file_name = file_name.strip()
                # Remove any leading/trailing quotes
                if file_name.startswith('"') and file_name.endswith('"'):
                    file_name = file_name[1:-1]
                if file_name.startswith("'") and file_name.endswith("'"):
                    file_name = file_name[1:-1]
                
                # Remove any problematic newlines or control characters
                file_name = file_name.replace('\n', '').replace('\r', '')
                
                print(f"Processing file: {file_name}")
                
                # Skip if filename became empty after cleaning
                if not file_name:
                    continue
                    
                file_changes[file_name] = content
            
            # Get explanation (everything before the first code block)
            parts = result.split('```', 1)
            explanation = parts[0].strip()
            
            print(f"Found changes for {len(file_changes)} files")
            self.file_changes.emit(file_changes, explanation)
        else:
            # Check for single Python code blocks (for editor update)
            code_blocks = re.findall(r'```python\n(.*?)```', result, re.DOTALL)
            
            if code_blocks:
                # Get explanation (everything before the first code block)
                code = code_blocks[0]
                parts = result.split('```python', 1)
                explanation = parts[0].strip()
                
                if len(parts) > 1:
                    after_code = parts[1].split('```', 1)
                    if len(after_code) > 1:
                        explanation += "\n\n" + after_code[1].strip()
                
                print(f"Found code block, length: {len(code)}")
                self.code_suggestion.emit(code, explanation)
            else:
                print("No code blocks found in response")
                self.response_ready.emit(result)