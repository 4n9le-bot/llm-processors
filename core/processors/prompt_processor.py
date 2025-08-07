from typing import Optional, Dict, Any

from jinja2 import Environment, BaseLoader, meta
from jinja2.exceptions import TemplateError

from ..base import Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class PromptProcessor(Processor):
    """
    A processor that sets up prompts for LLM processing with Jinja2 template support.
    
    This processor takes a prompt template (plain text or Jinja2 template) and prepares 
    it for LLM consumption by rendering it with context data.
    """
    
    def __init__(self, 
                 prompt: str, 
                 output_key: str = "prompt", 
                 input_key: Optional[str] = None,
                 template_vars: Optional[Dict[str, Any]] = None,
                 strict_mode: bool = True,
                 name: Optional[str] = None):
        """
        Initialize prompt processor.
        
        Args:
            prompt: The prompt text or Jinja2 template to use
            output_key: The key to store the rendered prompt in context
            input_key: The key to get template variables from context (optional)
            template_vars: Additional static template variables (optional)
            strict_mode: If True, raises error for undefined variables; 
                        if False, undefined variables are replaced with empty string
            name: Optional name for the processor
        """
        super().__init__(name)
        self.prompt = prompt
        self.output_key = output_key
        self.input_key = input_key
        self.template_vars = template_vars or {}
        self.strict_mode = strict_mode
        
        # Initialize Jinja2 environment
        if strict_mode:
            from jinja2 import StrictUndefined
            undefined_class = StrictUndefined
        else:
            from jinja2 import Undefined
            undefined_class = Undefined
            
        self.jinja_env = Environment(
            loader=BaseLoader(),
            undefined=undefined_class
        )
        
        # Check if the prompt contains Jinja2 template syntax
        self.is_template = self._is_jinja_template(prompt)
        
        # Pre-compile template if it's a Jinja2 template
        if self.is_template:
            try:
                self.template = self.jinja_env.from_string(prompt)
                self.template_vars_needed = self._get_template_variables(prompt)
            except TemplateError as e:
                raise ValueError(f"Invalid Jinja2 template: {e}")
        else:
            self.template = None
            self.template_vars_needed = set()
    
    def _is_jinja_template(self, text: str) -> bool:
        """
        Check if the text contains Jinja2 template syntax.
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if text contains Jinja2 syntax
        """
        # Check for common Jinja2 patterns
        jinja_patterns = ['{{', '{%', '{#']
        return any(pattern in text for pattern in jinja_patterns)
    
    def _get_template_variables(self, template_string: str) -> set:
        """
        Extract template variables from a Jinja2 template.
        
        Args:
            template_string: The template string
            
        Returns:
            set: Set of variable names used in the template
        """
        try:
            ast = self.jinja_env.parse(template_string)
            return meta.find_undeclared_variables(ast)
        except Exception:
            return set()
    
    def _prepare_template_context(self, context: Context) -> Dict[str, Any]:
        """
        Prepare the template context by combining context data and template vars.
        
        Args:
            context: Processing context
            
        Returns:
            Dict containing template variables
        """
        template_context = {}
        
        # Add all context data (lowest priority)
        template_context.update(context.get_all())
        
        # Add template variables from context via input_key (medium priority)
        if self.input_key and context.has(self.input_key):
            context_template_vars = context.get(self.input_key)
            if isinstance(context_template_vars, dict):
                template_context.update(context_template_vars)
            else:
                # If the input_key value is not a dict, log a warning but continue
                pass
        
        # Add static template variables (highest priority - these can override everything)
        template_context.update(self.template_vars)
        
        return template_context
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt template and add rendered result to context.
        
        Args:
            context: The processing context
            
        Returns:
            ProcessingResult: Result of the prompt processing
        """
        try:
            if self.is_template and self.template is not None:
                # Render Jinja2 template
                template_context = self._prepare_template_context(context)
                
                # Check for missing required variables in strict mode
                if self.strict_mode:
                    missing_vars = self.template_vars_needed - set(template_context.keys())
                    if missing_vars:
                        raise ValueError(f"Missing required template variables: {missing_vars}")
                
                rendered_prompt = self.template.render(template_context)
            else:
                # Use prompt as-is for non-template strings
                rendered_prompt = self.prompt
            
            # Add the rendered prompt to context using the specified output key
            context.set(self.output_key, rendered_prompt)
            
            metadata = {
                "processor_type": "prompt", 
                "prompt_length": len(rendered_prompt),
                "output_key": self.output_key,
                "is_template": self.is_template,
                "original_prompt_length": len(self.prompt)
            }
            
            if self.is_template:
                metadata.update({
                    "template_vars_needed": list(self.template_vars_needed),
                    "template_vars_provided": list(self.template_vars.keys())
                })
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=rendered_prompt,
                metadata=metadata
            )
            
        except TemplateError as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=ValueError(f"Template rendering error: {e}")
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
    
    def validate_input(self, context: Context) -> bool:
        """
        Validate input for prompt processor.
        
        For template prompts, checks if required variables are available.
        For plain prompts, always returns True.
        """
        if not self.is_template:
            return True
            
        if not self.strict_mode:
            return True
            
        # Get all available variables from different sources
        available_vars = set(context.get_all().keys())
        
        # Add variables from input_key if available
        if self.input_key and context.has(self.input_key):
            input_vars = context.get(self.input_key)
            if isinstance(input_vars, dict):
                available_vars.update(input_vars.keys())
        
        # Add static template variables
        available_vars.update(self.template_vars.keys())
        
        # Check if all required template variables are available
        missing_vars = self.template_vars_needed - available_vars
        return len(missing_vars) == 0
    
    def get_required_variables(self) -> set:
        """
        Get the set of variables required by this template.
        
        Returns:
            set: Set of variable names required for template rendering
        """
        return self.template_vars_needed.copy()
    
    def add_template_var(self, key: str, value: Any) -> None:
        """
        Add or update a template variable.
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.template_vars[key] = value
    
    def remove_template_var(self, key: str) -> Any:
        """
        Remove a template variable.
        
        Args:
            key: Variable name to remove
            
        Returns:
            The removed value or None if key doesn't exist
        """
        return self.template_vars.pop(key, None)
    
    def preview_render(self, context_data: Optional[Dict[str, Any]] = None, 
                      input_key_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Preview how the template would be rendered with given context data.
        
        Args:
            context_data: Optional context data for preview
            input_key_data: Optional data that would be available via input_key
            
        Returns:
            str: Rendered template or original prompt if not a template
            
        Raises:
            ValueError: If template rendering fails
        """
        if not self.is_template or self.template is None:
            return self.prompt
            
        try:
            template_context = {}
            
            # Add context data (lowest priority)
            if context_data:
                template_context.update(context_data)
            
            # Add input_key data (medium priority)
            if input_key_data:
                template_context.update(input_key_data)
            
            # Add static template variables (highest priority)
            template_context.update(self.template_vars)
                
            return self.template.render(template_context)
        except TemplateError as e:
            raise ValueError(f"Template preview error: {e}")
        except Exception as e:
            raise ValueError(f"Preview error: {e}")
    
    def __repr__(self) -> str:
        """String representation of the processor."""
        parts = [f"name='{self.name}'", f"is_template={self.is_template}"]
        
        if self.input_key:
            parts.append(f"input_key='{self.input_key}'")
            
        if self.is_template:
            parts.append(f"template_vars={len(self.template_vars)}")
            
        return f"PromptProcessor({', '.join(parts)})"
