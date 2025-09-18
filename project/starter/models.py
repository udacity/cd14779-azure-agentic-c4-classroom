
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict,List

class FraudResult(BaseModel):
    """
    Model to represent the result of a fraud detection analysis.
    
    """
    pass

class SupportResult(BaseModel):
    """
    Model to represent the result of a customer support interaction.
    
    """
    pass

class LoanResult(BaseModel):
    """
    Model to represent the result of a loan processing operation.
    
    """
    pass

class SynthReport(BaseModel):
    """
    Model to represent the result of a synthetic data generation task.
    
    """
    pass