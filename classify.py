"""
Classification orchestrator with waterfall ML pipeline

This module implements the core classification logic using a three-tier
waterfall approach:
1. Regex: Fast pattern matching for common log types (~1ms)
2. BERT: ML embeddings for complex patterns (~50ms) 
3. LLM: AI-powered classification for edge cases (~300ms)

The waterfall strategy optimizes for both speed and cost by using
cheaper/faster methods first and falling back to expensive methods
only when needed.
"""
from processor_regex import classify_with_regex
from processor_bert import classify_with_bert, get_bert_classifier
from processor_llm import classify_with_llm
from typing import List, Tuple
import time
from logger_config import get_logger
from metrics import get_metrics
from models import ClassificationMethod

logger = get_logger(__name__)
metrics = get_metrics()


def classify(logs: List[Tuple[str, str]]) -> List[dict]:
    """
    Classify multiple logs
    
    Args:
        logs: List of (source, log_message) tuples
        
    Returns:
        List of dicts with keys: category, method, confidence, severity
    """
    results = []
    for source, log_msg in logs:
        try:
            result = classify_log(source, log_msg)
            results.append(result)
        except Exception as e:
            logger.error("Classification failed for log", extra={
                "source": source,
                "error": str(e),
                "message": log_msg[:100]
            })
            results.append({
                "category": "Unclassified",
                "method": "error",
                "confidence": 0.0,
                "severity": "LOW"
            })
    return results


def classify_log(source: str, log_msg: str) -> dict:
    """
    Classify a single log with waterfall strategy
    
    Args:
        source: Log source system
        log_msg: Log message
        
    Returns:
        Dict with keys: category, method, confidence, severity
    """
    from severity_mapper import get_severity
    
    start_time = time.time()
    method = ClassificationMethod.UNCLASSIFIED
    error = False
    confidence = 0.0
    
    try:
        # Strategy: LegacyCRM uses LLM, others use Regex -> BERT fallback
        if source == "LegacyCRM":
            logger.debug("Using LLM for LegacyCRM", extra={"source": source})
            label = classify_with_llm(log_msg)
            method = ClassificationMethod.LLM
            confidence = 0.85  # LLM typically high confidence
        else:
            # Try regex first (fastest)
            label = classify_with_regex(log_msg)
            if label:
                method = ClassificationMethod.REGEX
                confidence = 0.95  # Regex is deterministic
            else:
                # Fallback to BERT
                logger.debug("Regex failed, using BERT", extra={"source": source})
                bert_result = classify_with_bert(log_msg)
                # BERT may return string or tuple (label, confidence)
                if isinstance(bert_result, tuple):
                    label, confidence = bert_result
                else:
                    label = bert_result
                    confidence = 0.80  # Default BERT confidence
                method = ClassificationMethod.BERT
        
        # Get severity
        severity = get_severity(label).value
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        metrics.record_classification(method.value, processing_time_ms, error=False)
        
        logger.info("Classification successful", extra={
            "source": source,
            "method": method.value,
            "label": label,
            "confidence": confidence,
            "severity": severity,
            "processing_time_ms": processing_time_ms
        })
        
        return {
            "category": label,
            "method": method.value,
            "confidence": confidence,
            "severity": severity
        }
        
    except Exception as e:
        error = True
        processing_time_ms = (time.time() - start_time) * 1000
        metrics.record_classification("error", processing_time_ms, error=True)
        
        logger.error("Classification error", extra={
            "source": source,
            "error": str(e),
            "message": log_msg[:100]
        })
        
        return {
            "category": "Unclassified",
            "method": "error",
            "confidence": 0.0,
            "severity": "LOW"
        }


def classify_csv(input_file: str) -> str:
    """
    Classify logs from CSV file
    
    Args:
        input_file: Path to input CSV file
        
    Returns:
        Path to output CSV file
    """
    import pandas as pd
    import os
    
    logger.info("Processing CSV file", extra={"file": input_file})
    
    try:
        df = pd.read_csv(input_file)
        
        # Validate columns
        required_cols = ["source", "log_message"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Perform classification
        results = classify(list(zip(df["source"], df["log_message"])))
        
        # Add classification results to DataFrame
        df["target_label"] = [r["category"] for r in results]
        df["method"] = [r["method"] for r in results]
        df["confidence"] = [r["confidence"] for r in results]
        df["severity"] = [r["severity"] for r in results]
        
        # Save results
        os.makedirs("resources", exist_ok=True)
        output_file = "resources/output.csv"
        df.to_csv(output_file, index=False)
        
        logger.info("CSV processing complete", extra={
            "input": input_file,
            "output": output_file,
            "rows": len(df)
        })
        
        return output_file
        
    except Exception as e:
        logger.error("CSV processing failed", extra={
            "file": input_file,
            "error": str(e)
        })
        raise


